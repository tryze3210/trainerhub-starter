'use client';

import { useEffect, useMemo, useState } from 'react';

import { uploadApi } from '@/modules/upload/api';
import { trainerContentStatusLabel } from '@/modules/upload/components/trainer-upload-format';
import type { VideoDraft } from '@/types/api';

type TrainerSelectedMediaListProps = {
  selectedVideoIds: string[];
  onRemove: (videoId: string) => void;
};

export function TrainerSelectedMediaList({ selectedVideoIds, onRemove }: TrainerSelectedMediaListProps) {
  const [videos, setVideos] = useState<VideoDraft[]>([]);

  useEffect(() => {
    let mounted = true;
    uploadApi.listMyVideos()
      .then((items) => {
        if (mounted) setVideos(items);
      })
      .catch(() => {
        if (mounted) setVideos([]);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const selectedVideos = useMemo(
    () => selectedVideoIds.map((id) => videos.find((video) => video.id === id)).filter(Boolean) as VideoDraft[],
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

      {selectedVideoIds.map((videoId, index) => {
        const video = selectedVideos.find((item) => item.id === videoId);
        return (
          <div className="trainer-selected-media-row" key={videoId}>
            <div>
              <strong>{video?.title || `Видео из библиотеки ${index + 1}`}</strong>
              <span>{video ? trainerContentStatusLabel(video.status) : 'Видео выбрано'}</span>
            </div>
            <button className="premium-secondary-button" type="button" onClick={() => onRemove(videoId)}>Убрать</button>
          </div>
        );
      })}
    </section>
  );
}
