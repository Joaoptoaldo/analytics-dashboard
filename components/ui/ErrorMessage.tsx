import { Button } from './button';

interface ErrorMessageProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorMessage({ message = 'Ocorreu um erro inesperado.', onRetry }: ErrorMessageProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 p-4 text-destructive">
      <span>{message}</span>
      {onRetry && (
        <Button variant="outline" onClick={onRetry}>
          Tentar novamente
        </Button>
      )}
    </div>
  );
}
