import Link from 'next/link';
import { TrainerCabinetNav } from './trainer-cabinet-nav';
import { ProfileWorkbench, ProfileWorkbenchHero } from '@/design-system/profile-workbench';

export function TrainerCabinetShell({
  title,
  description,
  children,
  actions,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
}) {
  const heroActions = [
    actions,
    <Link href="/catalog" className="premium-secondary-button" key="catalog">Открыть каталог</Link>,
  ].filter(Boolean);

  return (
    <ProfileWorkbench tone="trainer">
      <ProfileWorkbenchHero
        eyebrow="Кабинет тренера"
        title={title}
        description={description}
        actions={heroActions}
      />
      <TrainerCabinetNav variant="horizontal" />
      <div className="profile-workbench-content trainer-cabinet-content">{children}</div>
    </ProfileWorkbench>
  );
}
