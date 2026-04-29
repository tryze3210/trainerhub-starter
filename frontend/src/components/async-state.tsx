export function LoadingCard({ text = 'Загрузка…' }: { text?: string }) {
  return <div className="card"><p className="muted">{text}</p></div>;
}

export function ErrorCard({ text }: { text: string }) {
  return <div className="card error">{text}</div>;
}

export function EmptyCard({ text }: { text: string }) {
  return <div className="card"><p className="muted">{text}</p></div>;
}
