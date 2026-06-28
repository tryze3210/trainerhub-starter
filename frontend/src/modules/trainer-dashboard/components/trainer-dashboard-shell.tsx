'use client';

import type { ReactNode } from 'react';
import { TrainerCabinetShell } from '@/modules/trainer-cabinet/components/trainer-cabinet-shell';

export function TrainerDashboardShell({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <TrainerCabinetShell title={title} description={description}>
      {children}
    </TrainerCabinetShell>
  );
}
