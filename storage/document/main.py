import boto3
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def fetch_objects():
    print(os.getenv("LOCALSTACK_ENDPOINT"))
    s3 = boto3.client("s3", endpoint_url=os.getenv("LOCALSTACK_ENDPOINT"))
    response = s3.list_buckets()

    # Output the bucket names
    print('Existing buckets:')
    for bucket in response['Buckets']:
        print(f'  {bucket["Name"]}')

fetch_objects()