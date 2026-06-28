export function TrainerLoadingState({ title = 'Загружаем данные' }: { title?: string }) {
  return (
    <div className="trainer-loading-state" aria-live="polite">
      <span />
      <strong>{title}</strong>
    </div>
  );
}
