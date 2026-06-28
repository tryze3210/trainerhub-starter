'use client';

import { useMemo } from 'react';

import { trainerContentStatusLabel } from '@/modules/upload/components/trainer-upload-format';
import {
  getMediaVideoPublicAddressState,
  getMediaVideoTitle,
  hasMediaVideoFile,
  type TrainerProductMediaVideo,
} from '@/modules/trainer-products/types/product-media';

type TrainerSelectedMediaListProps = {
  videos: TrainerProductMediaVideo[];
  selectedVideoIds: string[];
  loading?: boolean;
  onRemove: (videoId: string) => void;
};

export function TrainerSelectedMediaList({ videos, selectedVideoIds, loading, onRemove }: TrainerSelectedMediaListProps) {
  const selectedVideos = useMemo(
    () => selectedVideoIds.map((id) => videos.find((video) => video.id === id)).filter(Boolean) as TrainerProductMediaVideo[],
    [selectedVideoIds, videos]
  );

  return (
    <section className="trainer-selected-media-list">
      <header className="profile-workbench-section-header">
        <div>
          <h3>Выбранные материалы</h3>
          <p>{selectedVideoIds.length ? `${selectedVideoIds.length} видео выбрано` : 'Материалы ещё не выбраны'}</p>
        </div>
      </header>

      {selectedVideoIds.length === 0 ? (
        <div className="trainer-product-material-empty">
          <strong>Материалы ещё не выбраны</strong>
          <p>Выберите видео из библиотеки или загрузите новый видеоурок.</p>
        </div>
      ) : null}

      {selectedVideoIds.length > 0 && loading ? (
        <div className="trainer-selected-media-row">
          <div>
            <strong>Обновляем выбранные материалы</strong>
            <span>Материалы уже добавлены в продукт.</span>
          </div>
        </div>
      ) : null}

      {!loading && selectedVideoIds.map((videoId) => {
        const video = selectedVideos.find((item) => item.id === videoId);
        return (
          <div className="trainer-selected-media-row" key={videoId}>
            <div>
              <strong>{video ? getMediaVideoTitle(video) : 'Выбранное видео'}</strong>
              <span>{video ? trainerContentStatusLabel(video.status ?? undefined) : 'Видео уже добавлено в продукт. Данные обновятся после перезагрузки библиотеки.'}</span>
              {video ? <span>{hasMediaVideoFile(video) ? 'Файл добавлен' : 'Файл не добавлен'} · {getMediaVideoPublicAddressState(video)}</span> : null}
            </div>
            <button className="premium-secondary-button" type="button" onClick={() => onRemove(videoId)}>Убрать</button>
          </div>
        );
      })}
    </section>
  );
}
