import type { Chat } from '@/entities/chat/model/types';

export interface ChatSearchHit {
  chat: Chat;
  snippet?: string;
  matchType: 'title' | 'content';
}

/**
 * Поиск по истории чатов.
 * Ищет подстроку (case-insensitive) сначала в названиях, затем в содержимом сообщений.
 * Возвращает уникальные чаты, для найденных по содержимому добавляет сниппет.
 */
export function searchChats(chats: Chat[], rawQuery: string): ChatSearchHit[] {
  const query = rawQuery.trim().toLowerCase();
  if (!query) return chats.map((c) => ({ chat: c, matchType: 'title' as const }));

  const hits: ChatSearchHit[] = [];
  const seen = new Set<string>();

  for (const chat of chats) {
    if (chat.title.toLowerCase().includes(query)) {
      hits.push({ chat, matchType: 'title' });
      seen.add(chat.id);
      continue;
    }
    const hitMsg = chat.messages.find((m) => m.content.toLowerCase().includes(query));
    if (hitMsg && !seen.has(chat.id)) {
      hits.push({ chat, matchType: 'content', snippet: makeSnippet(hitMsg.content, query) });
      seen.add(chat.id);
    }
  }
  return hits;
}

function makeSnippet(source: string, query: string, radius = 40): string {
  const idx = source.toLowerCase().indexOf(query);
  if (idx === -1) return source.slice(0, radius * 2);
  const from = Math.max(0, idx - radius);
  const to = Math.min(source.length, idx + query.length + radius);
  const prefix = from > 0 ? '…' : '';
  const suffix = to < source.length ? '…' : '';
  return `${prefix}${source.slice(from, to).replace(/\s+/g, ' ')}${suffix}`;
}
