'use client';

import { markAllNotificationsRead, markNotificationRead } from '@/lib/api';
import { useRouter } from 'next/navigation';

export function NotificationActions({ notificationId, markAll = false }: { notificationId?: number; markAll?: boolean }) {
  const router = useRouter();

  async function handleClick() {
    if (markAll) {
      await markAllNotificationsRead();
    } else if (notificationId) {
      await markNotificationRead(notificationId);
    }
    router.refresh();
  }

  return (
    <button className="rounded-lg border px-3 py-2 text-sm" onClick={handleClick}>
      {markAll ? 'Mark all read' : 'Mark read'}
    </button>
  );
}
