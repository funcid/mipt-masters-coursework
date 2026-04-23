import { useMemo, useState } from 'react';
import { useChatsStore } from '@/entities/chat/model/store';
import { searchChats, type ChatSearchHit } from '@/features/chat-search/lib/search';
import { IconButton } from '@/shared/ui/IconButton';
import {
  IconClose,
  IconEdit,
  IconPlus,
  IconSearch,
  IconSettings,
  IconTrash,
} from '@/shared/ui/Icon';

interface SidebarProps {
  onOpenSettings: () => void;
  onClose?: () => void;
  mobile?: boolean;
}

export function Sidebar({ onOpenSettings, onClose, mobile }: SidebarProps) {
  const chats = useChatsStore((s) => s.chats);
  const activeChatId = useChatsStore((s) => s.activeChatId);
  const setActiveChat = useChatsStore((s) => s.setActiveChat);
  const createChat = useChatsStore((s) => s.createChat);
  const deleteChat = useChatsStore((s) => s.deleteChat);
  const renameChat = useChatsStore((s) => s.renameChat);

  const [query, setQuery] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingValue, setEditingValue] = useState('');

  const hits: ChatSearchHit[] = useMemo(() => searchChats(chats, query), [chats, query]);

  const handleNewChat = () => {
    createChat();
    onClose?.();
  };

  const handleDelete = (id: string, title: string) => {
    const ok = window.confirm(`Удалить чат «${title}»? Это действие нельзя отменить.`);
    if (ok) deleteChat(id);
  };

  const startEdit = (id: string, current: string) => {
    setEditingId(id);
    setEditingValue(current);
  };

  const commitEdit = () => {
    if (editingId) renameChat(editingId, editingValue);
    setEditingId(null);
    setEditingValue('');
  };

  return (
    <aside className="flex h-full w-full flex-col bg-bg-secondary text-text-primary">
      <div className="flex items-center gap-2 px-3 py-3">
        <button
          type="button"
          onClick={handleNewChat}
          className="flex flex-1 items-center gap-2 rounded-md border border-border-subtle bg-bg-elevated px-3 py-2 text-sm font-medium hover:bg-bg-hover"
        >
          <IconPlus width={16} height={16} />
          Новый чат
        </button>
        {mobile && onClose && (
          <IconButton label="Закрыть панель" onClick={onClose}>
            <IconClose />
          </IconButton>
        )}
      </div>

      <div className="px-3 pb-2">
        <label className="relative block">
          <span className="sr-only">Поиск по чатам</span>
          <span className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted">
            <IconSearch width={16} height={16} />
          </span>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Поиск по чатам"
            className="w-full rounded-md border border-border-subtle bg-bg-elevated px-8 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:border-border-strong focus:outline-none"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery('')}
              aria-label="Сбросить поиск"
              className="absolute right-2 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
            >
              <IconClose width={14} height={14} />
            </button>
          )}
        </label>
      </div>

      <nav className="flex-1 overflow-y-auto px-2">
        {hits.length === 0 && (
          <p className="px-3 py-4 text-center text-sm text-text-muted">
            {query ? 'Ничего не найдено' : 'Нет чатов. Начните новый!'}
          </p>
        )}
        <ul className="space-y-0.5">
          {hits.map((hit) => {
            const isActive = hit.chat.id === activeChatId;
            const isEditing = editingId === hit.chat.id;
            return (
              <li key={hit.chat.id}>
                <div
                  className={`group flex items-center gap-1 rounded-md px-2 py-1.5 text-sm transition-colors ${
                    isActive ? 'bg-bg-elevated' : 'hover:bg-bg-hover'
                  }`}
                >
                  {isEditing ? (
                    <input
                      autoFocus
                      value={editingValue}
                      onChange={(e) => setEditingValue(e.target.value)}
                      onBlur={commitEdit}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') commitEdit();
                        if (e.key === 'Escape') setEditingId(null);
                      }}
                      className="flex-1 rounded bg-bg-primary px-1.5 py-0.5 text-sm focus:outline-none"
                    />
                  ) : (
                    <button
                      type="button"
                      onClick={() => {
                        setActiveChat(hit.chat.id);
                        onClose?.();
                      }}
                      className="flex min-w-0 flex-1 flex-col text-left"
                    >
                      <span className="truncate">{hit.chat.title}</span>
                      {hit.matchType === 'content' && hit.snippet && (
                        <span className="truncate text-xs text-text-muted">{hit.snippet}</span>
                      )}
                    </button>
                  )}

                  {!isEditing && (
                    <div className="flex opacity-0 transition-opacity group-hover:opacity-100">
                      <IconButton
                        label="Переименовать"
                        onClick={() => startEdit(hit.chat.id, hit.chat.title)}
                        className="h-7 w-7"
                      >
                        <IconEdit width={14} height={14} />
                      </IconButton>
                      <IconButton
                        label="Удалить"
                        tone="danger"
                        onClick={() => handleDelete(hit.chat.id, hit.chat.title)}
                        className="h-7 w-7"
                      >
                        <IconTrash width={14} height={14} />
                      </IconButton>
                    </div>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="border-t border-border-subtle p-3">
        <button
          type="button"
          onClick={onOpenSettings}
          className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-text-secondary transition-colors hover:bg-bg-hover hover:text-text-primary"
        >
          <IconSettings width={16} height={16} />
          Настройки модели
        </button>
      </div>
    </aside>
  );
}
