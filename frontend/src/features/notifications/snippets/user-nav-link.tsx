import Link from 'next/link';

export function UserNotificationsNavLink() {
  return (
    <Link href="/notifications" className="rounded-xl border border-zinc-800 px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-900">
      Notifications
    </Link>
  );
}
