#!/usr/bin/env python3
""" Event Generator

    This program creates a set of imaginary users, and walks them through interactions with
    an imaginary eCommerce site, writing their actions to a Kinesis stream.

    Invocation:

        clickstream_generator.py NUM_EVENTS NUM_USERS NUM_PRODUCTS KINESIS_STREAM

    Where:

        NUM_EVENTS       - the total number of events to write
        NUM_USERS        - number of users (1000 is a good value)
        NUM_PRODUCTS     - number of products (100 is a good value)
        KINESIS_STREAM   - name of the stream where events get written.
    """

import boto3
import json
import random
import sys
import uuid

from datetime import datetime, timedelta
from pprint import pprint


class Counters:
    """ A utility class for tracking metrics.
        """

    def __init__(self):
        self.counts = {}

    def increment(self, name):
        if name:
            value = self.counts.get(name, 0)
            self.counts[name] = value + 1


class KinesisWriter:
    """ Writes events to Kinesis, batching them to improve throughput.

        To use, call send() with each event. After sending all events,
        call flush() to ensure that they're all written to Kinesis.
        """

    def __init__(self, kinesis_client, stream_name):
        self._client = kinesis_client
        self._stream_name = stream_name
        self._events = []
        self.counters = Counters()
        self.total_event_count = 0

    def send(self, rec):
        self.total_event_count += 1
        self.counters.increment(rec.get('eventType'))
        self._events.append(rec)
        if len(self._events) > 499:
            self.flush()

    def flush(self):
        while len(self._events) > 0:
            events = self._events[:500]
            self._events = self._events[500:]
            print(f"sending {len(events)} events")
            recs = [{'PartitionKey': event['userId'], 'Data': bytes(json.dumps(event), 'utf-8')} for event in events]
            response = self._client.put_records(StreamName=self._stream_name, Records=recs)
            results = response['Records']
            requeued = []
            for ii in range(len(results)):
                if results[ii].get('ErrorCode'):
                    requeued.append(events[ii])
            if len(requeued) > 0:
                print(f"{len(requeued)} events requeued")
                self._events = requeued + self._events


class Product:
    """ Holder for a product, which is just a numeric ID and a random price.
        The class also maintains a lookup table from ID to instance.
        """

    lookup = {}

    def __init__(self, id):
        self.id = str(id + 1000)
        self.price = (random.randrange(40) + 1) / 4
        Product.lookup[self.id] = self


class User:
    """ A state machine that controls a single user's actions.

        Construct with a KinesisWriter (or anything else that behaves the
        same way) and a list of products, then repeatedly call act().
        """

    def __init__(self, event_writer, product_list):
        self.id = str(uuid.uuid4())
        self.state = "DEFAULT"
        self.writer = event_writer
        self.product_list = product_list
        self.cur_product = None
        self.cart = {}

    def _cart_summary(self):
        items = 0
        total_value = 0.0
        for product_id, quantity in self.cart.items():
            items += quantity
            total_value += Product.lookup[product_id].price * quantity
        return (items, total_value)

    def act(self, timestamp):
        # print(f"{timestamp.isoformat(timespec='seconds')} {self.id}: {self.state}")
        if self.state == "DEFAULT":
            if random.randrange(1000) < 1:
                self.state = "ENGAGED"
        elif self.state == "ENGAGED":
            if random.randrange(100) < 5:
                self.state = "DEFAULT"
            elif self.cart and random.randrange(100) < 10:
                self.state = "BEGIN_CHECKOUT"
            elif random.randrange(100) < 25:
                self.state = "LOOK_AT_PRODUCT"
        elif self.state == "LOOK_AT_PRODUCT":
            if not self.cur_product:
                self.cur_product = self.product_list[random.randrange(len(self.product_list))]
                self._emit_event(timestamp, "productPage", product_id=self.cur_product.id)
            elif random.randrange(100) < 10:
                self.cur_product = None
                self.state = "ENGAGED"
            elif random.randrange(100) < 5:
                self._update_cart(timestamp, self.cur_product, random.randrange(10) + 1)
                self.cur_product = None
                self.state = "ENGAGED"
        elif self.state == "BEGIN_CHECKOUT":
            self._checkout_action(timestamp, False)
            self.state = "IN_CART"
        elif self.state == "IN_CART":
            if random.randrange(100) < 5:
                self.state = "DEFAULT"
            elif random.randrange(100) < 25:
                self._checkout_action(timestamp, True)

    def _update_cart(self, timestamp, product, quantity):
        eventType = "updateItemQuantity" if product.id in self.cart else "addToCart"
        self.cart[product.id] = quantity
        self._emit_event(timestamp, eventType, product_id=product.id, quantity=quantity)

    def _checkout_action(self, timestamp, finish_checkout):
        (items_in_cart, total_value) = self._cart_summary()
        if finish_checkout:
            self._emit_event(timestamp, "checkoutComplete", items_in_cart=items_in_cart, total_value=total_value)
            self.cart = {}
            self.state = "DEFAULT"
        else:
            self._emit_event(timestamp, "checkoutStarted", items_in_cart=items_in_cart, total_value=total_value)

    def _emit_event(self, timestamp, eventType, product_id=None, quantity=None, items_in_cart=None, total_value=None):
        event = {}
        event['eventType'] = eventType
        event['eventId'] = str(uuid.uuid4())
        event['timestamp'] = timestamp.isoformat(sep=' ', timespec='milliseconds')
        event['userId'] = self.id
        if product_id:
            event['productId'] = product_id
        if quantity:
            event['quantity'] = quantity
        if items_in_cart:
            event['itemsInCart'] = items_in_cart
        if total_value:
            event['totalValue'] = total_value
        self.writer.send(event)
        
        
def main(num_events, num_users, num_products, stream_name):
    writer = KinesisWriter(boto3.client('kinesis'), stream_name)
    products = [Product(ii) for ii in range(num_products)]
    users = [User(writer, products) for ii in range(num_users)]
    timestamp = datetime.now() - timedelta(seconds=(10 * num_events))
    while writer.total_event_count < num_events:
        for user in users:
            if writer.total_event_count < num_events:
                user.act(timestamp)
        timestamp += timedelta(seconds=random.randrange(5) + 2)
    writer.flush()
    print("events by type:")
    for k,v in writer.counters.counts.items():
        print(f"   {k} = {v}")

        
if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)
    main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
