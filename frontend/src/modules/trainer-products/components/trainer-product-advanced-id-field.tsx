'use client';

import { useState } from 'react';

type TrainerProductAdvancedIdFieldProps = {
  value: string;
  onChange: (value: string) => void;
};

export function TrainerProductAdvancedIdField({ value, onChange }: TrainerProductAdvancedIdFieldProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <section className="trainer-product-advanced-field">
      <header className="profile-workbench-section-header">
        <div>
          <h3>Расширенная настройка</h3>
          <p>Используйте это поле, только если нужно вручную связать уже загруженные видео по ID.</p>
        </div>
        <button className="trainer-product-advanced-field-toggle premium-secondary-button" type="button" onClick={() => setIsOpen((current) => !current)}>
          {isOpen ? 'Скрыть поле ID' : 'Показать поле ID'}
        </button>
      </header>

      {isOpen ? (
        <label className="trainer-editor-field">
          <span>ID видео</span>
          <textarea className="trainer-content-textarea" value={value} onChange={(event) => onChange(event.target.value)} rows={5} />
          <small>Один ID на строку.</small>
        </label>
      ) : null}
    </section>
  );
}
