import boto3
from django.conf import settings

class ObjectStorageService:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.VK_S3_ENDPOINT_URL,
            aws_access_key_id=settings.VK_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.VK_S3_SECRET_ACCESS_KEY,
        )

    def create_presigned_upload(self, bucket: str, key: str, content_type: str, expires_in: int = 900) -> dict:
        url = self.client.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_in,
        )
        return {"url": url, "method": "PUT", "headers": {"Content-Type": content_type}, "expires_in": expires_in}

    def create_presigned_read(self, bucket: str, key: str, expires_in: int = 300) -> str:
        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def head_object(self, bucket: str, key: str) -> dict:
        return self.client.head_object(Bucket=bucket, Key=key)

storage_service = ObjectStorageService()
