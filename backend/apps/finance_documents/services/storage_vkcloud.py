from __future__ import annotations

from datetime import timedelta
from botocore.client import Config
import boto3

from .storage import StoredArtifact


class VKCloudS3ArtifactStorage:
    def __init__(self, *, bucket: str, endpoint_url: str, region_name: str, access_key: str, secret_key: str):
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region_name,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
        )

    def put_bytes(self, *, storage_key: str, content: bytes, content_type: str) -> StoredArtifact:
        response = self.client.put_object(
            Bucket=self.bucket,
            Key=storage_key,
            Body=content,
            ContentType=content_type,
        )
        return StoredArtifact(
            storage_key=storage_key,
            url=f"s3://{self.bucket}/{storage_key}",
            size_bytes=len(content),
            etag=(response.get("ETag") or "").strip('"'),
            content_type=content_type,
        )

    def build_signed_download_url(self, *, storage_key: str, expires_in: timedelta) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": storage_key},
            ExpiresIn=int(expires_in.total_seconds()),
        )
