export function CustomerLoadingState({ title = 'Загружаем данные' }: { title?: string }) {
  return (
    <div className="customer-loading-state" aria-live="polite">
      <span />
      <strong>{title}</strong>
    </div>
  );
}
