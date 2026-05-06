/**
 * Парсер Server-Sent Events из ReadableStream<Uint8Array>.
 *
 * Возвращает async-итератор по блокам `data:` (без префикса).
 * Служебные строки (`event:`, `id:`, комментарии `:`) и `[DONE]` фильтруются,
 * на `[DONE]` итератор корректно завершается.
 */
export async function* parseSse(
  stream: ReadableStream<Uint8Array>,
  signal?: AbortSignal,
): AsyncGenerator<string> {
  const reader = stream.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  const onAbort = () => reader.cancel().catch(() => {});
  signal?.addEventListener('abort', onAbort, { once: true });

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // События разделены пустой строкой (\n\n либо \r\n\r\n).
      let boundary: number;
      while ((boundary = findBoundary(buffer)) !== -1) {
        const rawEvent = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary).replace(/^(\r?\n){1,2}/, '');

        const dataLines: string[] = [];
        for (const line of rawEvent.split(/\r?\n/)) {
          if (!line || line.startsWith(':')) continue;
          if (line.startsWith('data:')) {
            dataLines.push(line.slice(5).replace(/^ /, ''));
          }
        }
        if (dataLines.length === 0) continue;
        const payload = dataLines.join('\n');
        if (payload === '[DONE]') return;
        yield payload;
      }
    }

    // Хвост без двойного перевода строки
    const tail = buffer.trim();
    if (tail && tail !== '[DONE]' && tail.startsWith('data:')) {
      const payload = tail.slice(5).trimStart();
      if (payload !== '[DONE]') yield payload;
    }
  } finally {
    signal?.removeEventListener('abort', onAbort);
    try {
      reader.releaseLock();
    } catch {
      /* noop */
    }
  }
}

function findBoundary(buffer: string): number {
  const lf = buffer.indexOf('\n\n');
  const crlf = buffer.indexOf('\r\n\r\n');
  if (lf === -1) return crlf === -1 ? -1 : crlf + 4;
  if (crlf === -1) return lf + 2;
  return lf + 2 < crlf + 4 ? lf + 2 : crlf + 4;
}
