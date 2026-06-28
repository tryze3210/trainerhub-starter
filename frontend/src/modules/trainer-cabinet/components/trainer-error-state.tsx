export function TrainerErrorState({ message = 'Не удалось загрузить данные', onRetry }: { message?: string; onRetry?: () => void }) {
  return (
    <div className="trainer-error-state">
      <strong>Не удалось загрузить данные</strong>
      <p>{message}</p>
      {onRetry ? <button type="button" className="premium-secondary-button" onClick={onRetry}>Попробовать снова</button> : null}
    </div>
  );
}
