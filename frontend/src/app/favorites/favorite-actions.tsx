'use client';

import { deleteFavorite } from '@/lib/api';
import { useRouter } from 'next/navigation';

export function FavoriteActions({ favoriteId }: { favoriteId: number }) {
  const router = useRouter();

  async function handleDelete() {
    await deleteFavorite(favoriteId);
    router.refresh();
  }

  return (
    <button className="rounded-lg border px-3 py-2 text-sm" onClick={handleDelete}>
      Remove
    </button>
  );
}
