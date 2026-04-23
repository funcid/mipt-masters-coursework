import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  children: ReactNode;
  tone?: 'ghost' | 'accent' | 'danger';
}

/**
 * Компактная круглая кнопка с иконкой.
 * Используем паттерн compound-friendly: рендерим только children,
 * наружу отдаём aria-label + подсказку title.
 */
export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(function IconButton(
  { label, children, tone = 'ghost', className = '', ...rest },
  ref,
) {
  const toneClass =
    tone === 'accent'
      ? 'bg-accent text-white hover:bg-accent-hover'
      : tone === 'danger'
        ? 'text-red-400 hover:bg-red-500/10'
        : 'text-text-secondary hover:bg-white/[0.06] hover:text-text-primary';

  return (
    <button
      ref={ref}
      type="button"
      aria-label={label}
      title={label}
      className={`inline-flex h-8 w-8 items-center justify-center rounded-md transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${toneClass} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
});
