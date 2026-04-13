class VKCloudMessageMediaStorage:
    def build_presigned_put(self, *, storage_key: str, content_type: str, expires_in: int = 900):
        raise NotImplementedError

    def build_signed_get(self, *, storage_key: str, expires_in: int = 900):
        raise NotImplementedError
