import type { Role } from '@/shared/api/types';

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  createdAt: number;
  /** Признак незавершённого ответа: например, когда пользователь остановил генерацию */
  interrupted?: boolean;
  /** Признак ошибки при генерации */
  errored?: boolean;
}

export interface Chat {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: ChatMessage[];
  /** Системный промпт для этого чата. Если не задан — используется глобальный. */
  systemPrompt?: string;
}

export interface CompletionSettings {
  model: string;
  temperature: number;
  top_p: number;
  max_tokens: number;
  repetition_penalty: number;
  systemPrompt: string;
  streaming: boolean;
}

export const DEFAULT_SETTINGS: CompletionSettings = {
  model: 'GigaChat',
  temperature: 0.7,
  top_p: 0.9,
  max_tokens: 2048,
  repetition_penalty: 1.0,
  systemPrompt:
    'Ты — полезный, дружелюбный ассистент. Отвечай подробно и структурированно. ' +
    'Используй Markdown, если это улучшает читаемость (списки, подзаголовки, блоки кода).',
  streaming: true,
};
