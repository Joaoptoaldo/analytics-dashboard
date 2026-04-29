import { render, screen } from '@testing-library/react';
import { ErrorMessage } from './ErrorMessage';

describe('ErrorMessage', () => {
  it('exibe mensagem padrão', () => {
    render(<ErrorMessage />);
    expect(screen.getByText('Ocorreu um erro inesperado.')).toBeInTheDocument();
  });

  it('exibe mensagem customizada', () => {
    render(<ErrorMessage message="Erro customizado" />);
    expect(screen.getByText('Erro customizado')).toBeInTheDocument();
  });

  it('chama onRetry ao clicar no botão', () => {
    const onRetry = jest.fn();
    render(<ErrorMessage message="Erro" onRetry={onRetry} />);
    screen.getByRole('button', { name: /tentar novamente/i }).click();
    expect(onRetry).toHaveBeenCalled();
  });
});
