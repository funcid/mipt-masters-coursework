import { useCallback, useEffect, useRef, useState, type ChangeEvent, type KeyboardEvent } from 'react';
import type { ChatAttachment } from '@/shared/api/types';
import { IconClose, IconImage, IconSend, IconStop } from '@/shared/ui/Icon';
import { IconButton } from '@/shared/ui/IconButton';

interface InputFieldProps {
  onSend: (payload: { text: string; attachments?: ChatAttachment[] }) => void;
  onStop: () => void;
  isSending: boolean;
  /** Текст плейсхолдера */
  placeholder?: string;
}

const MAX_IMAGE_MB = 8;

/**
 * Поле ввода с поддержкой:
 *  - автоматическое растягивание textarea по высоте;
 *  - Enter → отправка, Shift+Enter → перенос;
 *  - прикрепление изображений (multimodal: будут загружены в GigaChat /files);
 *  - переключение кнопки «отправить» ↔ «остановить» во время генерации.
 */
export function InputField({ onSend, onStop, isSending, placeholder }: InputFieldProps) {
  const [text, setText] = useState('');
  const [attachments, setAttachments] = useState<ChatAttachment[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 220)}px`;
  }, [text]);

  const submit = useCallback(() => {
    if (isSending) return;
    const trimmed = text.trim();
    if (!trimmed && attachments.length === 0) return;
    onSend({ text: trimmed, attachments: attachments.length ? attachments : undefined });
    setText('');
    setAttachments([]);
  }, [text, attachments, isSending, onSend]);

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit();
    }
  };

  const handleFiles = async (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;
    const incoming: ChatAttachment[] = [];
    for (const file of Array.from(files)) {
      if (!file.type.startsWith('image/')) continue;
      if (file.size > MAX_IMAGE_MB * 1024 * 1024) {
        alert(`${file.name}: превышен лимит ${MAX_IMAGE_MB} МБ`);
        continue;
      }
      const dataUrl = await readAsDataUrl(file);
      incoming.push({
        kind: 'image',
        name: file.name,
        mimeType: file.type,
        dataUrl,
      });
    }
    setAttachments((prev) => [...prev, ...incoming]);
    event.target.value = '';
  };

  const removeAttachment = (idx: number) =>
    setAttachments((prev) => prev.filter((_, i) => i !== idx));

  const canSend = (text.trim().length > 0 || attachments.length > 0) && !isSending;

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-6 pt-2 sm:px-6">
      {attachments.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-2">
          {attachments.map((a, idx) => (
            <div
              key={`${a.name}-${idx}`}
              className="relative h-16 w-16 overflow-hidden rounded-md ring-1 ring-border-subtle"
            >
              <img src={a.dataUrl} alt={a.name} className="h-full w-full object-cover" />
              <button
                type="button"
                className="absolute right-0.5 top-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-black/60 text-white hover:bg-black/80"
                onClick={() => removeAttachment(idx)}
                aria-label={`Удалить ${a.name}`}
              >
                <IconClose width={12} height={12} />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-end gap-2 rounded-2xl border border-border-subtle bg-bg-elevated p-2 shadow-sm focus-within:border-border-strong">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          hidden
          onChange={handleFiles}
        />
        <IconButton
          label="Прикрепить изображение"
          onClick={() => fileInputRef.current?.click()}
          disabled={isSending}
        >
          <IconImage />
        </IconButton>
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

function readAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(reader.error ?? new Error('FileReader error'));
    reader.onload = () => resolve(String(reader.result));
    reader.readAsDataURL(file);
  });
}
