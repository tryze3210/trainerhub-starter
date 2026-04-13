import { NotificationCenter } from '@/features/notifications/components/NotificationCenter';

export default function NotificationsPage() {
  return (
    <main className="min-h-screen bg-black px-6 py-10">
      <div className="mx-auto max-w-7xl">
        <NotificationCenter />
      </div>
    </main>
  );
}
