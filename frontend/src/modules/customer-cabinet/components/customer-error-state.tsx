type CustomerErrorStateProps = {
  message?: string;
  onRetry?: () => void;
};

export function CustomerErrorState({ message = 'Не удалось загрузить данные', onRetry }: CustomerErrorStateProps) {
  return (
    <div className="customer-error-state">
      <strong>Не удалось загрузить данные</strong>
      <p>{message}</p>
      {onRetry ? <button type="button" className="premium-secondary-button" onClick={onRetry}>Попробовать снова</button> : null}
    </div>
  );
}
