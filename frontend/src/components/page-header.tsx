export function PageHeader({ title, description }: { title: string; description?: string }) {
  return (
    <div className="mb-6 border-b pb-4">
      <h1 className="text-2xl font-semibold">{title}</h1>
      {description ? <p className="mt-1 text-sm text-slate-600">{description}</p> : null}
    </div>
  );
}
