from dataclasses import dataclass

@dataclass
class UploadPayload:
    upload_url: str
    storage_key: str
    expires_in: int

class MessageMediaPipeline:
    def initiate_upload(self, *, conversation_id, actor_id, kind, filename, content_type, file_size):
        return UploadPayload(
            upload_url="https://storage.example.local/presigned-upload",
            storage_key=f"messaging/{conversation_id}/{filename}",
            expires_in=900,
        )

    def finalize_upload(self, *, upload_session_id, checksum: str | None = None):
        return {"status": "uploaded", "checksum": checksum}
