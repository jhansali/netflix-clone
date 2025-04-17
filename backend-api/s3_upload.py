import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    region_name=os.getenv("AWS_REGION"),
    endpoint_url=f"https://s3.{os.getenv('AWS_REGION')}.amazonaws.com",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)


BUCKET = os.getenv("S3_BUCKET_NAME")

def create_multipart_upload(filename):
    response = s3.create_multipart_upload(Bucket=BUCKET, Key=filename)
    return response["UploadId"]

def generate_presigned_urls(filename, upload_id, total_parts):
    urls = []
    for part_number in range(1, total_parts + 1):
        url = s3.generate_presigned_url(
            ClientMethod="upload_part",
            Params={
                "Bucket": BUCKET,
                "Key": filename,
                "UploadId": upload_id,
                "PartNumber": part_number
            },
            ExpiresIn=3600
        )
        urls.append({"partNumber": part_number, "url": url})
    return urls

def complete_upload(filename, upload_id, parts):
    response = s3.complete_multipart_upload(
        Bucket=BUCKET,
        Key=filename,
        UploadId=upload_id,
        MultipartUpload={"Parts": parts}
    )
    return response