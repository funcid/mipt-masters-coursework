import { parseSse } from './sse';
import type {
  ChatCompletionMessage,
  ChatCompletionResponse,
  CompletionParams,
  ModelsResponse,
} from './types';

/**
 * API-адаптер GigaChat.
 *
 * Все запросы идут через локальный BFF (`/api/gigachat/...`),
 * который отвечает за OAuth. Подробнее см. `server/index.js`.
 */

const BASE = '/api/gigachat';

/**
 * Загружает изображение в GigaChat и возвращает его `id`.
 * Этот id затем используется в поле `attachments` сообщения
 * (multimodal-режим: модель «видит» картинку).
 */
export async function uploadFile(file: File, signal?: AbortSignal): Promise<string> {
  const form = new FormData();
  form.append('file', file, file.name);
  form.append('purpose', 'general');
  const response = await fetch(`${BASE}/files`, {
    method: 'POST',
    body: form,
    signal,
  });
  if (!response.ok) {
    throw new Error(await formatError(response, 'files'));
  }
  const data = (await response.json()) as { id: string };
  if (!data.id) throw new Error('GigaChat /files: ответ без поля id');
  return data.id;
}

export async function fetchModels(signal?: AbortSignal): Promise<ModelsResponse> {
  const response = await fetch(`${BASE}/models`, {
    headers: { Accept: 'application/json' },
    signal,
  });
  if (!response.ok) {
    throw new Error(`GigaChat models failed: ${response.status}`);
  }
  return response.json();
}

export interface SendMessageOptions {
  model: string;
  messages: ChatCompletionMessage[];
  params: CompletionParams;
  signal?: AbortSignal;
}

export interface StreamMessageOptions extends SendMessageOptions {
  onDelta: (chunk: string) => void;
  onDone?: (fullText: string) => void;
}

/** Нестриминговый режим: один JSON-ответ с полным сообщением. */
export async function sendMessage(opts: SendMessageOptions): Promise<string> {
  const response = await fetch(`${BASE}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({
      model: opts.model,
      messages: opts.messages,
      stream: false,
      ...opts.params,
    }),
    signal: opts.signal,
  });

  if (!response.ok) {
    throw new Error(await formatError(response, 'chat/completions'));
  }
  const data = (await response.json()) as ChatCompletionResponse;
  return data.choices?.[0]?.message?.content ?? '';
}

/** Streaming-режим: токены приходят через SSE, склеиваются и отдаются по колбэкам. */
export async function streamMessage(opts: StreamMessageOptions): Promise<string> {
  const response = await fetch(`${BASE}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({
      model: opts.model,
      messages: opts.messages,
      stream: true,
      ...opts.params,
    }),
    signal: opts.signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(await formatError(response, 'chat/completions (stream)'));
  }

  let full = '';
  for await (const payload of parseSse(response.body, opts.signal)) {
    let json: ChatCompletionResponse;
    try {
      json = JSON.parse(payload) as ChatCompletionResponse;
    } catch {
      continue;
    }
    const delta = json.choices?.[0]?.delta?.content;
    if (delta) {
      full += delta;
      opts.onDelta(delta);
    }
    const finalContent = json.choices?.[0]?.message?.content;
    if (finalContent && !delta) {
      const tail = finalContent.startsWith(full) ? finalContent.slice(full.length) : finalContent;
      if (tail) {
        full += tail;
        opts.onDelta(tail);
      }
    }
  }

  opts.onDone?.(full);
  return full;
}

/**
 * Универсальная обёртка: пробуем стриминг, при провале — откатываемся на REST.
 * Так мы покрываем требование ТЗ: «Если не получается SSE, то обычный REST».
 */
export async function streamOrFallback(opts: StreamMessageOptions): Promise<string> {
  try {
    return await streamMessage(opts);
  } catch (error) {
    if (opts.signal?.aborted) throw error;
    console.warn('[GigaChat] streaming failed, falling back to REST:', error);
    const text = await sendMessage(opts);
    if (text) opts.onDelta(text);
    opts.onDone?.(text);
    return text;
  }
}

async function formatError(response: Response, label: string): Promise<string> {
  let details = '';
  try {
    details = await response.text();
  } catch {
    /* ignore */
  }
  return `GigaChat ${label} ${response.status}: ${details || response.statusText}`;
}
