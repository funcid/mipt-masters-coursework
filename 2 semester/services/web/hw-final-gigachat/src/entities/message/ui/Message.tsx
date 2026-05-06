import { memo } from 'react';
import type { ChatMessage } from '@/entities/chat/model/types';
import { Markdown } from '@/shared/ui/Markdown';
import { IconBot, IconCheck, IconCopy, IconUser } from '@/shared/ui/Icon';
import { useCopyToClipboard } from '@/shared/hooks/useCopyToClipboard';

interface MessageProps {
  message: ChatMessage;
  /** Показывать ли каретку стрима — актуально только для последнего пустого/растущего assistant */
  streaming?: boolean;
}

export const Message = memo(function Message({ message, streaming }: MessageProps) {
  const isUser = message.role === 'user';
  const { copied, copy } = useCopyToClipboard();

  return (
    <div className="group w-full animate-fade-in">
      <div className={`mx-auto flex w-full max-w-3xl gap-4 px-4 py-5 sm:px-6 ${isUser ? '' : ''}`}>
        <div
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md ${
            isUser ? 'bg-white/10' : 'bg-accent/20 text-accent'
          }`}
          aria-hidden
        >
          {isUser ? <IconUser /> : <IconBot />}
        </div>
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex items-center justify-between gap-3">
            <span className="text-sm font-semibold">
              {isUser ? 'Вы' : 'GigaChat'}
            </span>
            {!isUser && message.content ? (
              <button
                type="button"
                onClick={() => copy(message.content)}
                className="invisible inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-text-secondary transition-colors hover:bg-white/[0.06] hover:text-text-primary group-hover:visible"
                aria-label="Скопировать ответ"
                title="Скопировать ответ"
              >
                {copied ? <IconCheck width={14} height={14} /> : <IconCopy width={14} height={14} />}
                <span>{copied ? 'Скопировано' : 'Копировать'}</span>
              </button>
            ) : null}
          </div>

          {isUser ? (
            <UserContent message={message} />
          ) : (
            <AssistantContent message={message} streaming={streaming} />
          )}

          {message.interrupted ? (
            <p className="mt-2 text-xs italic text-text-muted">Ответ был остановлен пользователем</p>
          ) : null}
          {message.errored ? (
            <p className="mt-2 text-xs italic text-red-400">Произошла ошибка при генерации</p>
          ) : null}
        </div>
      </div>
    </div>
  );
});

function UserContent({ message }: { message: ChatMessage }) {
  if (!message.content) return null;
  return (
    <p className="whitespace-pre-wrap break-words leading-relaxed">{message.content}</p>
  );
}

function AssistantContent({ message, streaming }: { message: ChatMessage; streaming?: boolean }) {
  if (!message.content && streaming) {
    return <TypingDots />;
  }
  return <Markdown content={message.content} streaming={streaming} />;
}

function TypingDots() {
  return (
    <div className="flex items-center gap-1.5 py-2" aria-label="Ассистент печатает">
      <span className="h-2 w-2 animate-dot-flash rounded-full bg-text-muted [animation-delay:-0.32s]" />
      <span className="h-2 w-2 animate-dot-flash rounded-full bg-text-muted [animation-delay:-0.16s]" />
      <span className="h-2 w-2 animate-dot-flash rounded-full bg-text-muted" />
    </div>
  );
}
