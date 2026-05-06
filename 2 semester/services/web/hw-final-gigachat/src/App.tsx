import { useEffect, useState } from 'react';
import { Sidebar } from './widgets/Sidebar/Sidebar';
import { ChatWindow } from './widgets/ChatWindow/ChatWindow';
import { SettingsPanel } from './features/settings/ui/SettingsPanel';
import { IconButton } from './shared/ui/IconButton';
import { IconMenu, IconPlus } from './shared/ui/Icon';
import { useChatsStore, selectActiveChat } from './entities/chat/model/store';

function App() {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const createChat = useChatsStore((s) => s.createChat);
  const activeChat = useChatsStore(selectActiveChat);

  // При первом запуске — создадим пустой чат, если ни одного ещё нет.
  useEffect(() => {
    const state = useChatsStore.getState();
    if (state.chats.length === 0) {
      state.createChat();
    } else if (!state.activeChatId) {
      state.setActiveChat(state.chats[0].id);
    }
  }, []);

  return (
    <div className="flex h-full w-full overflow-hidden bg-bg-primary">
      {/* Desktop Sidebar */}
      <div className="hidden w-72 shrink-0 border-r border-border-subtle md:block">
        <Sidebar onOpenSettings={() => setSettingsOpen(true)} />
      </div>

      {/* Mobile Sidebar */}
      {mobileSidebarOpen && (
        <div className="fixed inset-0 z-30 md:hidden">
          <div
            className="absolute inset-0 bg-black/60"
            onClick={() => setMobileSidebarOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 w-72 max-w-[80vw] border-r border-border-subtle">
            <Sidebar
              mobile
              onOpenSettings={() => {
                setSettingsOpen(true);
                setMobileSidebarOpen(false);
              }}
              onClose={() => setMobileSidebarOpen(false)}
            />
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border-subtle px-3 py-2 md:hidden">
          <IconButton label="Открыть панель" onClick={() => setMobileSidebarOpen(true)}>
            <IconMenu />
          </IconButton>
          <span className="truncate px-2 text-sm font-medium">
            {activeChat?.title ?? 'GigaChat Studio'}
          </span>
          <IconButton label="Новый чат" onClick={() => createChat()}>
            <IconPlus />
          </IconButton>
        </header>

        <main className="flex min-h-0 flex-1">
          <div className="flex min-h-0 flex-1 flex-col">
            <ChatWindow />
          </div>
        </main>
      </div>

      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}

export default App;
