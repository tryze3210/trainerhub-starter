import { completeUploadIntent, createUploadIntent } from "./api";

export async function uploadFileDirect(file: File, accessToken: string) {
  const intent = await createUploadIntent({
    filename: file.name,
    content_type: file.type,
    file_size_bytes: file.size,
    visibility: "private",
  }, accessToken);

  await fetch(intent.upload_url, {
    method: intent.upload_method,
    headers: intent.required_headers,
    body: file,
  });

  await completeUploadIntent(intent.media_asset_id, accessToken);
  return intent.media_asset_id;
}
