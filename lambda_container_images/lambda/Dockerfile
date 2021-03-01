FROM amazon/aws-lambda-python:3.8

COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

COPY src/ /var/task

CMD [ "handler.lambda_handler" ]
