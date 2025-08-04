import boto3
import os
from dotenv import load_dotenv
from functools import lru_cache
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

@lru_cache(maxsize=1)
def get_s3_client():
    return boto3.client("s3", endpoint_url=os.getenv("LOCALSTACK_ENDPOINT"))

def fetch_objects():
    s3 = get_s3_client()
    response = s3.list_buckets()

    # Output the bucket names
    print('Existing buckets:')
    for bucket in response['Buckets']:
        print(f'  {bucket["Name"]}')

def pretty_list_files(bucket: str = os.getenv("S3_BUCKET")):
    s3 = get_s3_client()
    response = s3.list_objects_v2(Bucket=bucket)
    if 'Contents' in response:
        for obj in response['Contents']:
            print(f'  {obj["Key"]}')
    else:
        print("  No files in bucket")

def store_file(file_path: str, bucket: str = os.getenv("S3_BUCKET")):
    s3 = get_s3_client()
    try:
        # Use the file name as the S3 key
        file_name = Path(file_path).name
        s3.upload_file(file_path, bucket, file_name)
        print(f"Successfully uploaded {file_name} to {bucket}")
        return True
    except Exception as e:
        print(f"Error uploading file: {e}")
        return False

def delete_file(file_path: str, bucket: str = os.getenv("S3_BUCKET")):
    s3 = get_s3_client()
    try:
        s3.delete_object(Bucket=bucket, Key=file_path)
        print(f"Successfully deleted {file_path} from {bucket}")
        return True
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False