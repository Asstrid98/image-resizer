import boto3
import os
from botocore.exceptions import ClientError

# --- Eliminados RESULTS_DIR, glob y os.makedirs ya que no se usan con S3 ---

def get_storage_client():
    return boto3.client(
        's3',
        endpoint_url=os.getenv('STORAGE_ENDPOINT', 'http://localhost:9000'),
        aws_access_key_id=os.getenv('STORAGE_ACCESS_KEY', 'minioadmin'),
        aws_secret_access_key=os.getenv('STORAGE_SECRET_KEY', 'minioadmin'),
        region_name='us-east-1'
    )

def ensure_bucket_exists(bucket_name=None):
    if bucket_name is None:
        bucket_name = os.getenv('STORAGE_BUCKET', 'image-resizer')
    client = get_storage_client()
    try:
        client.head_bucket(Bucket=bucket_name)
    except ClientError:
        client.create_bucket(Bucket=bucket_name)
    return bucket_name

def upload_image(key, image_data, bucket_name=None):
    if bucket_name is None:
        bucket_name = os.getenv('STORAGE_BUCKET', 'image-resizer')
    client = get_storage_client()
    # Enviamos los datos directamente al "bucket", sin pasar por carpetas locales
    client.put_object(Bucket=bucket_name, Key=key, Body=image_data)

def download_image(key, bucket_name=None):
    if bucket_name is None:
        bucket_name = os.getenv('STORAGE_BUCKET', 'image-resizer')
    client = get_storage_client()
    response = client.get_object(Bucket=bucket_name, Key=key)
    return response['Body'].read()

def get_download_url(key, bucket_name=None, expires_in=3600):
    if bucket_name is None:
        bucket_name = os.getenv('STORAGE_BUCKET', 'image-resizer')
    client = get_storage_client()
    return client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': key},
        ExpiresIn=expires_in
    )