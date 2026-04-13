export function ProgressCard({ title, value, description }: { title: string; value: string | number; description: string }) {
  return (
    <div className="rounded-2xl border p-4">
      <div className="text-sm text-gray-500">{title}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
      <div className="mt-1 text-sm text-gray-600">{description}</div>
    </div>
  );
}
