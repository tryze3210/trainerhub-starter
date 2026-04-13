import { apiFetch } from "@/lib/api/client";

export type UploadIntentResponse = {
  media_asset_id: string;
  object_key: string;
  upload_url: string;
  upload_method: "PUT";
  required_headers: Record<string, string>;
  expires_in: number;
};

export async function createUploadIntent(input: {
  filename: string;
  content_type: string;
  file_size_bytes: number;
  visibility: "private" | "public";
}, accessToken: string) {
  return apiFetch<UploadIntentResponse>("/videos/upload-intents/", {
    method: "POST",
    body: JSON.stringify(input),
  }, accessToken);
}

export async function completeUploadIntent(mediaAssetId: string, accessToken: string) {
  return apiFetch(`/videos/upload-intents/${mediaAssetId}/complete/`, {
    method: "POST",
    body: JSON.stringify({}),
  }, accessToken);
}
