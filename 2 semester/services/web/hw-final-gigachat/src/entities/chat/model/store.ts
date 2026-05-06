import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { v4 as uuid } from 'uuid';
import {
  DEFAULT_SETTINGS,
  type Chat,
  type ChatMessage,
  type CompletionSettings,
} from './types';

interface ChatsState {
  chats: Chat[];
  activeChatId: string | null;
  settings: CompletionSettings;

  createChat: () => string;
  deleteChat: (id: string) => void;
  renameChat: (id: string, title: string) => void;
  setActiveChat: (id: string) => void;

  appendMessage: (chatId: string, message: Omit<ChatMessage, 'id' | 'createdAt'>) => ChatMessage;
  updateMessage: (chatId: string, messageId: string, patch: Partial<ChatMessage>) => void;
  removeMessage: (chatId: string, messageId: string) => void;

  updateSettings: (patch: Partial<CompletionSettings>) => void;

  /** Авто-переименование на основе первого пользовательского сообщения */
  autoTitle: (chatId: string) => void;
}

const makeChat = (): Chat => ({
  id: uuid(),
  title: 'Новый чат',
  createdAt: Date.now(),
  updatedAt: Date.now(),
  messages: [],
});

/**
 * Глобальный стор приложения.
 * Хранится в localStorage (key = gigachat-studio/v1).
 */
export const useChatsStore = create<ChatsState>()(
  persist(
    (set, get) => ({
      chats: [],
      activeChatId: null,
      settings: DEFAULT_SETTINGS,

      createChat: () => {
        const chat = makeChat();
        set((state) => ({
          chats: [chat, ...state.chats],
          activeChatId: chat.id,
        }));
        return chat.id;
      },

      deleteChat: (id) =>
        set((state) => {
          const chats = state.chats.filter((c) => c.id !== id);
          const activeChatId =
            state.activeChatId === id ? chats[0]?.id ?? null : state.activeChatId;
          return { chats, activeChatId };
        }),

      renameChat: (id, title) =>
        set((state) => ({
          chats: state.chats.map((c) =>
            c.id === id ? { ...c, title: title.trim() || c.title, updatedAt: Date.now() } : c,
          ),
        })),

      setActiveChat: (id) => set({ activeChatId: id }),

      appendMessage: (chatId, message) => {
        const full: ChatMessage = {
          id: uuid(),
          createdAt: Date.now(),
          ...message,
        };
        set((state) => ({
          chats: state.chats.map((c) =>
            c.id === chatId
              ? { ...c, messages: [...c.messages, full], updatedAt: Date.now() }
              : c,
          ),
        }));
        return full;
      },

      updateMessage: (chatId, messageId, patch) =>
        set((state) => ({
          chats: state.chats.map((c) =>
            c.id === chatId
              ? {
                  ...c,
                  messages: c.messages.map((m) => (m.id === messageId ? { ...m, ...patch } : m)),
                  updatedAt: Date.now(),
                }
              : c,
          ),
        })),

      removeMessage: (chatId, messageId) =>
        set((state) => ({
          chats: state.chats.map((c) =>
            c.id === chatId
              ? { ...c, messages: c.messages.filter((m) => m.id !== messageId) }
              : c,
          ),
        })),

      updateSettings: (patch) =>
        set((state) => ({ settings: { ...state.settings, ...patch } })),

      autoTitle: (chatId) => {
        const chat = get().chats.find((c) => c.id === chatId);
        if (!chat) return;
        if (chat.title !== 'Новый чат') return;
        const firstUser = chat.messages.find((m) => m.role === 'user');
        if (!firstUser) return;
        const source = firstUser.content.trim().replace(/\s+/g, ' ');
        if (!source) return;
        const title = source.length > 48 ? `${source.slice(0, 48)}…` : source;
        set((state) => ({
          chats: state.chats.map((c) =>
            c.id === chatId ? { ...c, title, updatedAt: Date.now() } : c,
          ),
        }));
      },
    }),
    {
      name: 'gigachat-studio/v1',
      storage: createJSONStorage(() => localStorage),
      version: 1,
      partialize: (state) => ({
        chats: state.chats,
        activeChatId: state.activeChatId,
        settings: state.settings,
      }),
    },
  ),
);

/** Селекторы */
export const selectActiveChat = (state: ChatsState): Chat | null => {
  if (!state.activeChatId) return null;
  return state.chats.find((c) => c.id === state.activeChatId) ?? null;
};
