import Link from 'next/link';
import { CustomerCabinetNav } from '@/modules/customer-cabinet/components/customer-cabinet-nav';
import { ProfileWorkbench, ProfileWorkbenchHero } from '@/design-system/profile-workbench';

type CustomerCabinetShellProps = {
  title: string;
  description: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
};

export function CustomerCabinetShell({ title, description, children, actions }: CustomerCabinetShellProps) {
  return (
    <ProfileWorkbench tone="customer">
      <ProfileWorkbenchHero
        eyebrow="Личный кабинет"
        title={title}
        description={description}
        actions={
          <>
          {actions}
          <Link href="/catalog" className="premium-secondary-button">Каталог</Link>
          </>
        }
      />
      <CustomerCabinetNav variant="horizontal" />
      <div className="profile-workbench-content customer-cabinet-content">{children}</div>
    </ProfileWorkbench>
  );
}
