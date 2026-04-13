import { PageHeader } from '@/components/page-header';
import { getFavorites } from '@/lib/api';
import { FavoriteActions } from './favorite-actions';

export default async function FavoritesPage() {
  const favorites = await getFavorites();

  return (
    <div className="p-6">
      <PageHeader title="Favorites" description="Saved trainers, videos, and programs." />
      <div className="space-y-3">
        {favorites.map((item) => (
          <div key={item.id} className="flex items-center justify-between rounded-xl border p-4">
            <div>
              <div className="font-medium">{item.target_type}</div>
              <div className="text-sm text-slate-600">Target ID: {item.target_id}</div>
            </div>
            <FavoriteActions favoriteId={item.id} />
          </div>
        ))}
      </div>
    </div>
  );
}
