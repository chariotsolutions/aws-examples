FROM amazon/aws-lambda-python:3.11

RUN pip install boto3 pyarrow

COPY lambda.py ${LAMBDA_TASK_ROOT}

CMD [ "lambda.lambda_handler" ]
