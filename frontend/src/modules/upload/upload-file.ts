import { uploadApi } from './api';

export async function uploadFileDirect(file: File): Promise<string> {
  const intent = await uploadApi.createUploadIntent({
    filename: file.name,
    content_type: file.type || 'video/mp4',
    file_size_bytes: file.size,
    visibility: 'private',
  });

  const uploadResponse = await fetch(intent.upload_url, {
    method: intent.upload_method,
    headers: intent.required_headers,
    body: file,
  });

  if (!uploadResponse.ok) {
    throw new Error('Не удалось загрузить файл в object storage');
  }

  await uploadApi.completeUploadIntent(intent.media_asset_id);
  return intent.media_asset_id;
}
