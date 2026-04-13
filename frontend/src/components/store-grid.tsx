import { StoreItem } from '@/lib/api';

export function StoreGrid({ items, actionLabel, renderAction }: { items: StoreItem[]; actionLabel: string; renderAction: (item: StoreItem) => React.ReactNode }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {items.map((item) => (
        <div key={`${item.kind}-${item.id}`} className="rounded-2xl border p-4 shadow-sm">
          <div className="mb-2 text-xs uppercase tracking-wide text-gray-500">{item.kind}</div>
          <h3 className="text-lg font-semibold">{item.title}</h3>
          <p className="mt-2 text-sm text-gray-600">Trainer: {item.trainer_id}</p>
          <p className="mt-2 font-medium">{item.price} {item.currency}</p>
          <div className="mt-4">{renderAction(item)}</div>
        </div>
      ))}
    </div>
  );
}
