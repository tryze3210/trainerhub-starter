export function AppShell({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <main className="container">
      <h1>{title}</h1>
      {children}
    </main>
  );
}
