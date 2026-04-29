from __future__ import annotations

import boto3
from django.conf import settings


class ObjectStorageService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            endpoint_url = getattr(settings, 'VK_S3_ENDPOINT_URL', '') or None
            self._client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=getattr(settings, 'VK_S3_ACCESS_KEY_ID', '') or None,
                aws_secret_access_key=getattr(settings, 'VK_S3_SECRET_ACCESS_KEY', '') or None,
                region_name='ru-msk',
            )
        return self._client

    def create_presigned_upload(self, bucket: str, key: str, content_type: str, expires_in: int = 900) -> dict:
        if not getattr(settings, 'VK_S3_ENDPOINT_URL', ''):
            return {
                'url': f'https://mock-storage.local/{bucket}/{key}',
                'method': 'PUT',
                'headers': {'Content-Type': content_type},
                'expires_in': expires_in,
            }
        url = self.client.generate_presigned_url(
            ClientMethod='put_object',
            Params={'Bucket': bucket, 'Key': key, 'ContentType': content_type},
            ExpiresIn=expires_in,
        )
        return {'url': url, 'method': 'PUT', 'headers': {'Content-Type': content_type}, 'expires_in': expires_in}

    def create_presigned_read(self, bucket: str, key: str, expires_in: int = 300) -> str:
        if not getattr(settings, 'VK_S3_ENDPOINT_URL', ''):
            return f'https://mock-storage.local/{bucket}/{key}?expires_in={expires_in}'
        return self.client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expires_in,
        )

    def head_object(self, bucket: str, key: str) -> dict:
        if not getattr(settings, 'VK_S3_ENDPOINT_URL', ''):
            return {'ContentLength': 0, 'ContentType': 'application/octet-stream'}
        return self.client.head_object(Bucket=bucket, Key=key)


storage_service = ObjectStorageService()
