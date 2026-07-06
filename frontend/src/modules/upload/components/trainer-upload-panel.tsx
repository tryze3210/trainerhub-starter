'use client';

import { Suspense } from 'react';
import { TrainerContentStudio } from './trainer-content-studio';

type TrainerUploadPanelProps = {
  compactHero?: boolean;
};

export function TrainerUploadPanel({ compactHero = false }: TrainerUploadPanelProps) {
  return (
    <Suspense fallback={<div className="trainer-content-loading">Загрузка студии материалов...</div>}>
      <TrainerContentStudio compactHero={compactHero} />
    </Suspense>
  );
}
