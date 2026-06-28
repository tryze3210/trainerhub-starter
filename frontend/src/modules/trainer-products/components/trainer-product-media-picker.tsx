'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { uploadApi } from '@/modules/upload/api';
import { trainerContentPrice, trainerContentStatusLabel } from '@/modules/upload/components/trainer-upload-format';
import type { VideoDraft } from '@/types/api';

type TrainerProductMediaPickerProps = {
  selectedVideoIds: string[];
  onChange: (videoIds: string[]) => void;
  highlighted?: boolean;
};

function fileLabel(video: VideoDraft): string {
  return video.video_asset_id || video.media_asset_id || video.media_asset ? 'Файл добавлен' : 'Файл не добавлен';
}

function addressLabel(video: VideoDraft): string {
  return video.slug ? 'Адрес настроен' : 'Адрес не указан';
}

export function TrainerProductMediaPicker({ selectedVideoIds, onChange, highlighted }: TrainerProductMediaPickerProps) {
  const [videos, setVideos] = useState<VideoDraft[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadVideos() {
    setIsLoading(true);
    setError(null);
    try {
      setVideos(await uploadApi.listMyVideos());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить видео');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadVideos();
  }, []);

  function toggleVideo(videoId: string) {
    if (selectedVideoIds.includes(videoId)) {
      onChange(selectedVideoIds.filter((id) => id !== videoId));
      return;
    }
    onChange([...selectedVideoIds, videoId]);
  }

  return (
    <section className={highlighted ? 'trainer-product-media-picker trainer-product-media-picker-highlighted' : 'trainer-product-media-picker'}>
      <header className="profile-workbench-section-header">
        <div>
          <h3>Библиотека видео</h3>
          <p>Выберите видео, которые войдут в продукт. Если видео ещё нет, загрузите его в разделе “Видео и материалы”.</p>
        </div>
        <Link className="premium-secondary-button" href="/trainer/videos?tab=videos&intent=upload">Загрузить видео</Link>
      </header>

      {isLoading ? <div className="trainer-workbench-empty-rail-card"><strong>Загружаем библиотеку видео</strong></div> : null}
      {error ? (
        <div className="trainer-workbench-empty-rail-card">
          <strong>Не удалось загрузить видео</strong>
          <p>Попробуйте обновить страницу или перейти в раздел “Видео и материалы”.</p>
          <button className="premium-secondary-button" type="button" onClick={() => void loadVideos()}>Повторить</button>
        </div>
      ) : null}

      {!isLoading && !error && videos.length === 0 ? (
        <div className="trainer-workbench-empty-rail-card">
          <strong>Видео пока нет</strong>
          <p>Загрузите первый видеоурок, чтобы добавить его в продукт.</p>
          <Link className="premium-secondary-button" href="/trainer/videos?tab=videos&intent=upload">Загрузить видео</Link>
        </div>
      ) : null}

      {!isLoading && !error && videos.length > 0 ? (
        <div className="profile-workbench-rail trainer-media-picker-rail" aria-label="Библиотека видео для продукта">
          {videos.map((video) => {
            const active = selectedVideoIds.includes(video.id);
            return (
              <button
                className={active ? 'profile-workbench-rail-card trainer-media-picker-card trainer-media-picker-card-active profile-workbench-rail-card-active' : 'profile-workbench-rail-card trainer-media-picker-card'}
                key={video.id}
                type="button"
                onClick={() => toggleVideo(video.id)}
              >
                <span>{trainerContentStatusLabel(video.status)}</span>
                <strong>{video.title}</strong>
                <span>{fileLabel(video)}</span>
                <span>{trainerContentPrice(video.price_amount, video.currency)}</span>
                <small>{addressLabel(video)}</small>
                <span>{active ? 'Выбрано' : 'Выбрать'}</span>
              </button>
            );
          })}
        </div>
      ) : null}
    </section>
  );
}
