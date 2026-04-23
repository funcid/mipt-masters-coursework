import { useCallback, useRef, useState } from 'react';
import { useChatsStore } from '@/entities/chat/model/store';
import type { ChatAttachment, ChatCompletionMessage } from '@/shared/api/types';
import { streamOrFallback, sendMessage, uploadFile } from '@/shared/api/gigachat';

/** data:URL → File, чтобы загрузить в GigaChat /files как multipart */
function dataUrlToFile(dataUrl: string, name: string, mimeType: string): File {
  const [, base64] = dataUrl.split(',');
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return new File([bytes], name, { type: mimeType });
}

interface SendPayload {
  text: string;
  attachments?: ChatAttachment[];
}

/**
 * Хук-оркестратор отправки сообщения пользователя в активный чат.
 * Реализует:
 *  - добавление user + assistant(stub) сообщений;
 *  - построение messages-контекста (system + история);
 *  - streaming с обновлением content по мере прихода токенов;
 *  - возможность остановить генерацию (AbortController);
 *  - автогенерацию названия чата из первого сообщения.
 */
export function useChatSend() {
  const [isSending, setIsSending] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const send = useCallback(async ({ text, attachments }: SendPayload) => {
    const trimmed = text.trim();
    if (!trimmed && !(attachments && attachments.length)) return;
    if (isSending) return;

    const store = useChatsStore.getState();
    let chatId = store.activeChatId;
    if (!chatId) chatId = store.createChat();

    // 0. Грузим вложения в GigaChat /files, чтобы получить fileId (multimodal).
    //    Если загрузка упадёт — продолжим без конкретного вложения, UI не ломаем.
    const uploaded: ChatAttachment[] = [];
    if (attachments?.length) {
      for (const a of attachments) {
        try {
          const file = dataUrlToFile(a.dataUrl, a.name, a.mimeType);
          const id = await uploadFile(file);
          uploaded.push({ ...a, fileId: id });
        } catch (error) {
          console.warn('[useChatSend] uploadFile failed:', error);
          uploaded.push(a);
        }
      }
    }

    // 1. Добавляем user
    store.appendMessage(chatId, {
      role: 'user',
      content: trimmed,
      attachments: uploaded.length ? uploaded : undefined,
    });
    store.autoTitle(chatId);

    // 2. Сразу создаём пустое assistant-сообщение, которое будем дописывать стримом
    const assistantMsg = store.appendMessage(chatId, {
      role: 'assistant',
      content: '',
    });

    // 3. Собираем контекст (после append обновлённое состояние берём заново)
    const fresh = useChatsStore.getState().chats.find((c) => c.id === chatId);
    if (!fresh) return;

    const { settings } = useChatsStore.getState();
    const messages: ChatCompletionMessage[] = [];
    const sysPrompt = fresh.systemPrompt ?? settings.systemPrompt;
    if (sysPrompt.trim()) {
      messages.push({ role: 'system', content: sysPrompt });
    }
    for (const m of fresh.messages) {
      if (m.id === assistantMsg.id) continue;
      if (!m.content && !(m.attachments && m.attachments.length)) continue;
      const payload: ChatCompletionMessage = { role: m.role, content: m.content };
      const fileIds = (m.attachments ?? []).map((a) => a.fileId).filter(Boolean) as string[];
      if (fileIds.length) payload.attachments = fileIds;
      messages.push(payload);
    }

    const controller = new AbortController();
    abortRef.current = controller;
    setIsSending(true);

    let buffer = '';
    let rafScheduled = false;
    const flush = () => {
      rafScheduled = false;
      useChatsStore.getState().updateMessage(chatId!, assistantMsg.id, { content: buffer });
    };
    const scheduleFlush = () => {
      if (rafScheduled) return;
      rafScheduled = true;
      window.requestAnimationFrame(flush);
    };

    try {
      if (settings.streaming) {
        await streamOrFallback({
          model: settings.model,
          messages,
          params: {
            temperature: settings.temperature,
            top_p: settings.top_p,
            max_tokens: settings.max_tokens,
            repetition_penalty: settings.repetition_penalty,
          },
          signal: controller.signal,
          onDelta: (chunk) => {
            buffer += chunk;
            scheduleFlush();
          },
          onDone: () => flush(),
        });
      } else {
        const full = await sendMessage({
          model: settings.model,
          messages,
          params: {
            temperature: settings.temperature,
            top_p: settings.top_p,
            max_tokens: settings.max_tokens,
            repetition_penalty: settings.repetition_penalty,
          },
          signal: controller.signal,
        });
        buffer = full;
        flush();
      }
    } catch (error) {
      const aborted = controller.signal.aborted || (error as Error).name === 'AbortError';
      if (aborted) {
        useChatsStore.getState().updateMessage(chatId!, assistantMsg.id, {
          content: buffer || '*(генерация остановлена)*',
          interrupted: true,
        });
      } else {
        console.error('[useChatSend]', error);
        useChatsStore.getState().updateMessage(chatId!, assistantMsg.id, {
          content: `> Ошибка: ${(error as Error).message}`,
          errored: true,
        });
      }
    } finally {
      abortRef.current = null;
      setIsSending(false);
    }
  }, [isSending]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { send, stop, isSending };
}
