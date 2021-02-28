import boto3
import json
import logging
import os

import psycopg2

def lambda_handler(event, context):
    print("I've been installed!")
