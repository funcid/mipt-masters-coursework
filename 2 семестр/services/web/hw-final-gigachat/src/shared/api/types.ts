export type Role = 'system' | 'user' | 'assistant';

export interface ChatAttachment {
  /** Тип содержимого: для multimodal GigaChat передаётся как отдельное поле attachments */
  kind: 'image';
  /** Имя файла — для отображения в UI */
  name: string;
  /** data: URL для предпросмотра */
  dataUrl: string;
  /** MIME-тип, например image/png */
  mimeType: string;
  /** ID файла, выданный GigaChat после загрузки */
  fileId?: string;
}

export interface ChatCompletionMessage {
  role: Role;
  content: string;
  /** ID прикреплённых файлов (изображений), возвращаемые GigaChat /files */
  attachments?: string[];
}

export interface CompletionParams {
  temperature: number;
  top_p: number;
  max_tokens: number;
  repetition_penalty: number;
}

export interface ChatCompletionRequest extends CompletionParams {
  model: string;
  messages: ChatCompletionMessage[];
  stream?: boolean;
}

export interface ChatCompletionChoice {
  message?: { role: Role; content: string };
  delta?: { role?: Role; content?: string };
  finish_reason?: string;
}

export interface ChatCompletionResponse {
  choices: ChatCompletionChoice[];
  created?: number;
  model?: string;
  object?: string;
}

export interface ModelInfo {
  id: string;
  object: string;
  owned_by?: string;
}

export interface ModelsResponse {
  data: ModelInfo[];
  object: string;
}
