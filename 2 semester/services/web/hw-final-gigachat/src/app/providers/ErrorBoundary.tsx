import { Component, type ReactNode } from 'react';

type Props = { children: ReactNode; fallback?: ReactNode };
type State = { error: Error | null };

/**
 * Error Boundary: ловит ошибки в дочернем дереве и показывает fallback.
 * Используем на корневом уровне, а также оборачиваем «рисковые» виджеты
 * (например, markdown-рендер с подсветкой кода).
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: unknown) {
    console.error('[ErrorBoundary]', error, info);
  }

  handleReset = () => this.setState({ error: null });

  render() {
    if (!this.state.error) return this.props.children;
    if (this.props.fallback) return this.props.fallback;

    return (
      <div className="flex h-full w-full items-center justify-center p-6">
        <div className="max-w-md rounded-lg border border-border-subtle bg-bg-elevated p-6 text-center shadow-lg">
          <h2 className="mb-2 text-lg font-semibold">Что-то пошло не так</h2>
          <p className="mb-4 text-sm text-text-secondary">
            {this.state.error.message || 'Неизвестная ошибка рендеринга'}
          </p>
          <button
            type="button"
            className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-white hover:bg-accent-hover"
            onClick={this.handleReset}
          >
            Повторить
          </button>
        </div>
      </div>
    );
  }
}
