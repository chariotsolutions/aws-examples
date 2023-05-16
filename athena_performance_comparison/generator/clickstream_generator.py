#!/usr/bin/env python3
""" Event Generator

    This program creates a set of imaginary users, and walks them through interactions with
    an imaginary eCommerce site, writing their actions to objects in S3.

    Invocation:

        ./clickstream_generator.py NUM_EVENTS NUM_USERS NUM_PRODUCTS BUCKET PREFIX FILE_SIZE

    Where:

        NUM_EVENTS   - the total number of events to write
        NUM_USERS    - number of users (1000 is a good value)
        NUM_PRODUCTS - number of products (100 is a good value)
        BUCKET       - S3 bucket to hold files
        PREFIX       - prefix within that bucket where files will be written
        FILE_SIZE    - number of records to store in each file
    """

import boto3
import io
import json
import os
import random
import sys
import time
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


class Writer:
    """ Writes events to files, batching them to improve throughput.
        """

    def __init__(self, bucket, prefix, file_size=500):
        self._s3_bucket = boto3.resource('s3').Bucket(bucket)
        self._s3_prefix = prefix
        self._file_size = file_size
        self._events = {}
        self.counters = Counters()
        self.total_event_count = 0

    def send(self, rec):
        event_type = rec.get('eventType')
        if not event_type:
            return
        self.total_event_count += 1
        self.counters.increment(event_type)
        events = self._events.get(event_type)
        if not events:
            events = []
            self._events[event_type] = events
        events.append(rec)
        if len(events) >= self._file_size:
            self.flush(event_type)

    def flush(self, event_type=None):
        if event_type:
            events = self._events.get(event_type)
            self.write_to_s3(event_type, events)
            self._events[event_type] = []
        else:
            for event_type in self._events.keys():
                self.flush(event_type)

    def write_to_s3(self, event_type, events):
        if not events:
            return
        s3_key = f"{self._s3_prefix}/{event_type}/{event_type}-{int(time.time() * 1000)}.json"
        print(f"writing {len(events)} events to s3://{self._s3_bucket.name}/{s3_key}")
        f = io.StringIO()
        for event in events:
            json.dump(event, f)
            f.write("\n")
        self._s3_bucket.put_object(Key=s3_key, Body=bytes(f.getvalue(), 'utf-8'))


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
        
        
def main(num_events, num_users, num_products, bucket, prefix, file_size):
    writer = Writer(bucket=bucket, prefix=prefix, file_size=file_size)
    products = [Product(ii) for ii in range(num_products)]
    users = [User(writer, products) for ii in range(num_users)]
    timestamp = datetime.now()
    while writer.total_event_count < num_events:
        for user in users:
            if writer.total_event_count < num_events:
                user.act(timestamp)
        timestamp += timedelta(seconds=random.randrange(8) + 2)
    writer.flush()
    print("events by type:")
    for k,v in writer.counters.counts.items():
        print(f"   {k} = {v}")

        
if __name__ == "__main__":
    if len(sys.argv) != 7:
        print(__doc__)
        sys.exit(1)
    main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5], int(sys.argv[6]))

