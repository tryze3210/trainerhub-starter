import type { ChangeEvent, DragEvent, FormEvent, ReactNode } from 'react';
import { trainerContentFileSize } from './trainer-upload-format';

type TrainerVideoUploadCardProps = {
  title: string;
  slug: string;
  description: string;
  priceAmount: string;
  currency: string;
  file: File | null;
  saving: boolean;
  uploadStep: string;
  highlighted?: boolean;
  actions?: ReactNode;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onTitleChange: (value: string) => void;
  onSlugChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onPriceChange: (value: string) => void;
  onCurrencyChange: (value: string) => void;
  onFileChange: (file: File | null) => void;
};

export function TrainerVideoUploadCard({
  title,
  slug,
  description,
  priceAmount,
  currency,
  file,
  saving,
  uploadStep,
  highlighted,
  actions,
  onSubmit,
  onTitleChange,
  onSlugChange,
  onDescriptionChange,
  onPriceChange,
  onCurrencyChange,
  onFileChange,
}: TrainerVideoUploadCardProps) {
  function pickFile(event: ChangeEvent<HTMLInputElement>) {
    onFileChange(event.target.files?.[0] || null);
  }

  function prevent(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
  }

  function dropFile(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    onFileChange(event.dataTransfer.files?.[0] || null);
  }

  return (
    <form className={highlighted ? 'trainer-content-form trainer-video-upload-card trainer-video-upload-card-highlight' : 'trainer-content-form trainer-video-upload-card'} onSubmit={onSubmit}>
      <div className="trainer-content-editor-header">
        <div>
          <h2>Загрузить видеоурок</h2>
          <p>Добавьте файл, название, описание и цену. Видео сохранится как черновик, а после проверки его можно опубликовать или использовать в программе.</p>
        </div>
        {actions}
      </div>

      <label className={file ? 'trainer-upload-dropzone trainer-upload-dropzone-active' : 'trainer-upload-dropzone'} onDragOver={prevent} onDrop={dropFile}>
        <input type="file" accept="video/mp4,video/quicktime" onChange={pickFile} />
        <strong>Перетащите видео сюда или выберите файл</strong>
        <span>MP4 или MOV</span>
        {file ? (
          <span>Файл выбран: {file.name}. Размер: {trainerContentFileSize(file.size)}</span>
        ) : (
          <span>Файл можно добавить сейчас или позже.</span>
        )}
      </label>

      <label className="trainer-content-field">
        <span>Название видео</span>
        <input className="trainer-content-input" value={title} onChange={(event) => onTitleChange(event.target.value)} required />
      </label>
      <label className="trainer-content-field">
        <span>Публичный адрес</span>
        <input className="trainer-content-input" value={slug} onChange={(event) => onSlugChange(event.target.value)} required />
      </label>
      <label className="trainer-content-field">
        <span>Описание</span>
        <textarea className="trainer-content-textarea" rows={4} value={description} onChange={(event) => onDescriptionChange(event.target.value)} />
      </label>
      <div className="trainer-content-form-grid">
        <label className="trainer-content-field">
          <span>Цена</span>
          <input className="trainer-content-input" type="number" min="0" step="0.01" value={priceAmount} onChange={(event) => onPriceChange(event.target.value)} />
        </label>
        <label className="trainer-content-field">
          <span>Валюта</span>
          <input className="trainer-content-input" value={currency} onChange={(event) => onCurrencyChange(event.target.value.toUpperCase())} />
        </label>
      </div>
      {uploadStep ? <div className="trainer-content-upload-step">{uploadStep}</div> : null}
      <div className="trainer-content-actions">
        <button className="trainer-content-button" type="submit" disabled={saving}>Сохранить видеоурок</button>
      </div>
    </form>
  );
}
