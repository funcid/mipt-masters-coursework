import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { IconSend, IconStop } from '@/shared/ui/Icon';
import { IconButton } from '@/shared/ui/IconButton';

interface InputFieldProps {
  onSend: (payload: { text: string }) => void;
  onStop: () => void;
  isSending: boolean;
  /** Текст плейсхолдера */
  placeholder?: string;
}

/**
 * Поле ввода с поддержкой:
 *  - автоматическое растягивание textarea по высоте;
 *  - Enter → отправка, Shift+Enter → перенос;
 *  - переключение кнопки «отправить» ↔ «остановить» во время генерации.
 */
export function InputField({ onSend, onStop, isSending, placeholder }: InputFieldProps) {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 220)}px`;
  }, [text]);

  const submit = useCallback(() => {
    if (isSending) return;
    const trimmed = text.trim();
    if (!trimmed) return;
    onSend({ text: trimmed });
    setText('');
  }, [text, isSending, onSend]);

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit();
    }
  };

  const canSend = text.trim().length > 0 && !isSending;

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-6 pt-2 sm:px-6">
      <div className="flex items-end gap-2 rounded-2xl border border-border-subtle bg-bg-elevated p-2 shadow-sm focus-within:border-border-strong">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder ?? 'Спросите что-нибудь у GigaChat...'}
          rows={1}
          className="flex-1 resize-none bg-transparent px-2 py-1.5 leading-6 text-text-primary placeholder:text-text-muted focus:outline-none"
        />
        {isSending ? (
          <IconButton label="Остановить генерацию" tone="accent" onClick={onStop}>
            <IconStop />
          </IconButton>
        ) : (
          <IconButton
            label="Отправить"
            tone="accent"
            onClick={submit}
            disabled={!canSend}
          >
            <IconSend />
          </IconButton>
        )}
      </div>
      <p className="mt-2 text-center text-xs text-text-muted">
        Enter — отправить · Shift+Enter — перенос строки · GigaChat может ошибаться
      </p>
    </div>
  );
}
