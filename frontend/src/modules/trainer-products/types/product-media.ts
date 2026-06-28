export type TrainerProductMediaVideo = {
  id: string;
  title: string;
  status?: string | null;
  price?: number | string | null;
  price_amount?: number | string | null;
  currency?: string | null;
  slug?: string | null;
  video_asset_id?: string | number | null;
  videoAssetId?: string | number | null;
  media_asset_id?: string | number | null;
  media_asset?: unknown;
};

export function getMediaVideoTitle(video: TrainerProductMediaVideo): string {
  return video.title?.trim() || 'Видеоурок';
}

export function hasMediaVideoFile(video: TrainerProductMediaVideo): boolean {
  return Boolean(video.video_asset_id || video.videoAssetId || video.media_asset_id || video.media_asset);
}

export function getMediaVideoPublicAddressState(video: TrainerProductMediaVideo): string {
  return video.slug ? 'Адрес настроен' : 'Адрес не указан';
}

export function getMediaVideoPrice(video: TrainerProductMediaVideo): number | string | null | undefined {
  return video.price ?? video.price_amount;
}
