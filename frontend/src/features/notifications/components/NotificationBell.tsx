"use client";

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { fetchUnreadCount } from '../api';

export function NotificationBell() {
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    let active = true;
    fetchUnreadCount()
      .then((data) => {
        if (active) setUnread(data.unread_count);
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, []);

  return (
    <Link href="/notifications" className="relative inline-flex items-center rounded-xl border border-zinc-800 px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-900">
      Notifications
      {unread > 0 ? (
        <span className="ml-2 inline-flex min-w-6 items-center justify-center rounded-full bg-emerald-500 px-2 py-0.5 text-xs font-semibold text-black">
          {unread}
        </span>
      ) : null}
    </Link>
  );
}
