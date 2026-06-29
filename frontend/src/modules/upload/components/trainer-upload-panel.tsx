'use client';

import { TrainerContentStudio } from './trainer-content-studio';

type TrainerUploadPanelProps = {
  compactHero?: boolean;
};

export function TrainerUploadPanel({ compactHero = false }: TrainerUploadPanelProps) {
  return <TrainerContentStudio compactHero={compactHero} />;
}
