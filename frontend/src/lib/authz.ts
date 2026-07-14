import type { AuthUser } from '@/types/api';

export function isAdminUser(user: AuthUser | null | undefined): boolean {
  return Boolean(
    user &&
      (user.active_role === 'admin' ||
        user.is_staff ||
        user.is_superuser ||
        user.available_roles?.includes('admin'))
  );
}
