import { useEffect, useLayoutEffect, useRef } from 'react';
import { useChatsStore, selectActiveChat } from '@/entities/chat/model/store';
import { Message } from '@/entities/message/ui/Message';
import { InputField } from '@/features/chat-send/ui/InputField';
import { useChatSend } from '@/features/chat-send/model/useChatSend';
import { ErrorBoundary } from '@/app/providers/ErrorBoundary';
import { IconBot } from '@/shared/ui/Icon';

/**
 * Главное окно с сообщениями + поле ввода.
 * Отвечает за автоскролл к последнему сообщению.
 */
export function ChatWindow() {
  const chat = useChatsStore(selectActiveChat);
  const createChat = useChatsStore((s) => s.createChat);
  const { send, stop, isSending } = useChatSend();

  const scrollerRef = useRef<HTMLDivElement>(null);
  const lastLengthRef = useRef(0);
  const isUserPinnedRef = useRef(true);

  useEffect(() => {
    lastLengthRef.current = 0;
    isUserPinnedRef.current = true;
  }, [chat?.id]);

  useLayoutEffect(() => {
    const node = scrollerRef.current;
    if (!node) return;
    if (!chat) return;
    const last = chat.messages[chat.messages.length - 1];
    const currentLen = (last?.content.length ?? 0) + chat.messages.length * 1000;
    if (currentLen === lastLengthRef.current) return;
    lastLengthRef.current = currentLen;
    if (isUserPinnedRef.current) {
      node.scrollTo({ top: node.scrollHeight, behavior: 'smooth' });
    }
  });

  const handleScroll = () => {
    const node = scrollerRef.current;
    if (!node) return;
    const delta = node.scrollHeight - node.scrollTop - node.clientHeight;
    isUserPinnedRef.current = delta < 80;
  };

  if (!chat) {
    return <EmptyState onStart={() => createChat()} />;
  }

  const lastMessage = chat.messages[chat.messages.length - 1];
  const isStreamingLast = isSending && lastMessage?.role === 'assistant';

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div
        ref={scrollerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto"
      >
        {chat.messages.length === 0 ? (
          <WelcomeHint />
        ) : (
          <ErrorBoundary>
            {chat.messages.map((m) => (
              <Message
                key={m.id}
                message={m}
                streaming={isStreamingLast && m.id === lastMessage?.id}
              />
            ))}
          </ErrorBoundary>
        )}
        <div className="h-4" />
      </div>
      <div className="border-t border-border-subtle bg-bg-primary">
        <InputField onSend={send} onStop={stop} isSending={isSending} />
      </div>
    </div>
  );
}

function EmptyState({ onStart }: { onStart: () => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center p-6 text-center">
      <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/20 text-accent">
        <IconBot width={28} height={28} />
      </div>
      <h1 className="text-2xl font-semibold">GigaChat Studio</h1>
      <p className="mt-2 max-w-md text-sm text-text-secondary">
        Чат на базе публичного API GigaChat. Начните новый диалог, чтобы отправить первый запрос.
      </p>
      <button
        type="button"
        onClick={onStart}
        className="mt-6 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-hover"
      >
        Начать новый чат
      </button>
    </div>
  );
}

function WelcomeHint() {
  return (
    <div className="mx-auto flex h-full max-w-2xl flex-col items-center justify-center px-6 py-20 text-center">
      <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/20 text-accent">
        <IconBot width={28} height={28} />
      </div>
      <h2 className="text-xl font-semibold">Чем я могу помочь?</h2>
      <p className="mt-2 max-w-md text-sm text-text-secondary">
        Спросите GigaChat о чём угодно: от объяснения концепций до генерации кода и анализа изображений.
      </p>
      <div className="mt-8 grid w-full grid-cols-1 gap-2 sm:grid-cols-2">
        {suggestions.map((s) => (
          <div
            key={s.title}
            className="rounded-lg border border-border-subtle bg-bg-elevated/60 p-3 text-left"
          >
            <p className="text-sm font-medium">{s.title}</p>
            <p className="mt-1 text-xs text-text-muted">{s.hint}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

const suggestions = [
  {
    title: 'Объясни React Hooks',
    hint: 'Краткий гайд по useState, useEffect, useMemo и правилам хуков',
  },
  {
    title: 'Напиши unit-тесты',
    hint: 'Подготовь тесты на Jest для функции форматирования даты',
  },
  {
    title: 'Проанализируй изображение',
    hint: 'Прикрепи картинку — спроси, что на ней изображено',
  },
  {
    title: 'Объясни сложную статью',
    hint: 'Вставь фрагмент — получи краткое изложение и TL;DR',
  },
];
