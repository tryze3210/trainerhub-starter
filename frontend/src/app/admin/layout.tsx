import type { ReactNode } from 'react';
import { AdminShell } from '@/modules/admin-shell/admin-shell';
import './admin-route.css';

export default function AdminLayout({ children }: { children: ReactNode }) {
  return <AdminShell>{children}</AdminShell>;
}
