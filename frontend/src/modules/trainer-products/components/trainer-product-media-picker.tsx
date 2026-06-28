'use client';

import Link from 'next/link';

import { trainerContentPrice, trainerContentStatusLabel } from '@/modules/upload/components/trainer-upload-format';
import {
  getMediaVideoPrice,
  getMediaVideoPublicAddressState,
  getMediaVideoTitle,
  hasMediaVideoFile,
  type TrainerProductMediaVideo,
} from '@/modules/trainer-products/types/product-media';

type TrainerProductMediaPickerProps = {
  videos: TrainerProductMediaVideo[];
  selectedVideoIds: string[];
  loading?: boolean;
  error?: string | null;
  highlighted?: boolean;
  onChange: (videoIds: string[]) => void;
  onRetry?: () => void;
};

export function TrainerProductMediaPicker({ videos, selectedVideoIds, loading, error, highlighted, onChange, onRetry }: TrainerProductMediaPickerProps) {
  function toggleVideo(videoId: string) {
    if (selectedVideoIds.includes(videoId)) {
      onChange(selectedVideoIds.filter((id) => id !== videoId));
      return;
    }
    onChange([...selectedVideoIds, videoId]);
  }

  return (
    <section className={['trainer-product-media-picker', highlighted ? 'trainer-product-media-picker-highlighted' : ''].filter(Boolean).join(' ')}>
      <header className="profile-workbench-section-header">
        <div>
          <h3>Библиотека видео</h3>
          <p>Выберите видео, которые войдут в продукт. Если видео ещё нет, загрузите его в разделе “Видео и материалы”.</p>
        </div>
        <Link className="premium-secondary-button" href="/trainer/videos?tab=videos&intent=upload">Загрузить видео</Link>
      </header>

      {loading ? <div className="trainer-product-media-picker-state"><strong>Загружаем библиотеку видео</strong></div> : null}
      {error ? (
        <div className="trainer-product-media-picker-state">
          <strong>Не удалось загрузить видео</strong>
          <p>Попробуйте обновить библиотеку или перейти в раздел “Видео и материалы”.</p>
          {onRetry ? <button className="premium-secondary-button" type="button" onClick={onRetry}>Повторить</button> : null}
        </div>
      ) : null}

      {!loading && !error && videos.length === 0 ? (
        <div className="trainer-product-media-picker-state">
          <strong>Видео пока нет</strong>
          <p>Загрузите первый видеоурок, чтобы добавить его в продукт.</p>
          <Link className="premium-secondary-button" href="/trainer/videos?tab=videos&intent=upload">Загрузить видео</Link>
        </div>
      ) : null}

      {!loading && !error && videos.length > 0 ? (
        <div className="trainer-media-picker-rail" aria-label="Библиотека видео для продукта">
          {videos.map((video) => {
            const active = selectedVideoIds.includes(video.id);
            const title = getMediaVideoTitle(video);
            const fileState = hasMediaVideoFile(video) ? 'Файл добавлен' : 'Файл не добавлен';
            const addressState = getMediaVideoPublicAddressState(video);
            const price = trainerContentPrice(String(getMediaVideoPrice(video) ?? '0'), video.currency || 'RUB');
            return (
              <button
                className={['trainer-media-picker-card', active ? 'trainer-media-picker-card-active' : ''].filter(Boolean).join(' ')}
                key={video.id}
                type="button"
                onClick={() => toggleVideo(video.id)}
              >
                <span className="trainer-media-picker-card-status">
                  <span>{trainerContentStatusLabel(video.status ?? undefined)}</span>
                  <span>{price}</span>
                </span>
                <strong>{title}</strong>
                <span>{fileState}</span>
                <small>{addressState}</small>
                <span>{active ? 'Выбрано' : 'Выбрать'}</span>
              </button>
            );
          })}
        </div>
      ) : null}
    </section>
  );
}
