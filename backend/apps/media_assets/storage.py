from dataclasses import dataclass
from uuid import uuid4


@dataclass(slots=True)
class PresignedUpload:
    upload_url: str
    storage_key: str
    headers: dict


class VKCloudStorageSigner:
    def build_video_upload(self, trainer_id: str, filename: str, content_type: str) -> PresignedUpload:
        key = f"trainer/{trainer_id}/raw/{uuid4()}-{filename}"
        return PresignedUpload(
            upload_url=f"https://storage.vkcloud.example/upload/{key}",
            storage_key=key,
            headers={"Content-Type": content_type},
        )
