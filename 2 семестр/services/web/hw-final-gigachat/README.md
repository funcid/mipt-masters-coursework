# GigaChat Studio

Итоговая работа по дисциплине **«Основы frontend-разработки»** (2 семестр).

Клон интерфейса ChatGPT на **React 18 + TypeScript** с интеграцией публичного **GigaChat API**. Поддерживает стриминг токенов через **Server-Sent Events**, markdown-рендеринг с подсветкой кода, историю чатов в `localStorage`, управление настройками модели и работу с изображениями (multimodal).

**Автор:** Царюк Артём Владимирович, МФТИ, магистратура  
**Преподаватель:** Марк Садыков

---

## Содержание

- [Возможности](#возможности)
- [Стек технологий](#стек-технологий)
- [Архитектура](#архитектура)
- [Быстрый старт](#быстрый-старт)
- [Примеры запросов](#примеры-запросов)
- [Скрипты](#скрипты)
- [Соответствие критериям оценки](#соответствие-критериям-оценки)
- [Как это работает внутри](#как-это-работает-внутри)
- [Известные ограничения](#известные-ограничения)

---

## Возможности

### Интерфейс чата

- Главный экран с областью сообщений и полем ввода, классический трёхколоночный макет.
- Визуально разные бабблы для **user** и **assistant** (цветные аватары, иконки, отдельная разметка).
- Полноценный **Markdown** в ответах GigaChat: заголовки, списки, таблицы, ссылки, блочный и инлайновый код, `---`, `> цитаты`, GFM-чекбоксы.
- **Подсветка синтаксиса** в блоках кода (`highlight.js`, тема GitHub Dark) + кнопка «Копировать» на каждом блоке.
- **Индикация загрузки** двух видов:
  - «typing dots» до прихода первого токена,
  - мигающий курсор `▍` у последнего assistant-сообщения, пока идёт стриминг.
- **Автоскролл** к последнему сообщению, который **уважает ручной скролл вверх** (если пользователь поднялся посмотреть историю — автоскролл не дёргает).
- **Копирование ответа** ассистента в буфер обмена (появляется на hover).
- **Остановить генерацию**: кнопка заменяет «отправить» на время генерации, под капотом `AbortController` рвёт SSE-поток.

### Управление чатами

- **Sidebar** слева со списком всех чатов пользователя.
- Создание нового чата + **автоматическая генерация названия** на основе первого пользовательского сообщения (`autoTitle`).
- Переключение между чатами — каждый хранит свой контекст.
- **Редактирование названия** по клику на иконку карандаша, **удаление** с подтверждением (`confirm()`).
- **Поиск** по названию и содержимому сообщений с подсветкой сниппета (matchType: `title` | `content`).
- История сохраняется в **localStorage** через `zustand/persist` (ключ: `gigachat-studio/v1`).

### Работа с GigaChat API

- Отправка запросов на `POST /api/v1/chat/completions` через BFF-прокси.
- Передача полного контекста диалога (`system`/`user`/`assistant`).
- **Streaming-режим** (`stream: true`) + корректный парсинг **SSE** (`text/event-stream`, `\n\n` разделитель, обработка `[DONE]`).
- **Fallback на REST**: если стриминг упал (не-2xx, разрыв), автоматически делается нестриминговый запрос.
- Настраиваемые параметры запроса: `temperature`, `top_p`, `max_tokens`, `repetition_penalty`, `systemPrompt`, выбор модели.
- `GET /api/v1/models` — выпадающий список моделей в настройках.
- **Multimodal**: прикреплённые изображения загружаются в `POST /files`, полученный `id` уходит в `attachments` сообщения.
- **OAuth**: прокси-сервер получает access-token у `ngw.devices.sberbank.ru:9443/api/v2/oauth`, кеширует с учётом `expires_at`.

### Дополнительно

- **Error Boundaries** на корне приложения и вокруг markdown-рендера.
- Адаптивная тёмная тема в стиле ChatGPT, мобильный drawer-sidebar.
- Кастомные хуки (`useChatSend`, `useCopyToClipboard`) и компоненты (`Markdown`, `CodeBlock`, `IconButton`) в духе «паттерна компоновщик».
- Предзаготовленный `.env.example` и dev-скрипт `concurrently`, запускающий фронт и BFF одной командой.

---

## Стек технологий

| Слой | Выбор |
|---|---|
| UI | React 18.3 + TypeScript 5.6 |
| Сборка | Vite 5 |
| State | Zustand 4 + `persist` в `localStorage` |
| Стили | Tailwind CSS 3 (кастомная палитра, анимации) |
| HTTP | Fetch API |
| Markdown | `react-markdown` + `remark-gfm` + `rehype-highlight` |
| Подсветка | `highlight.js` (github-dark theme) |
| BFF | Node.js 20+ / Express 4 (только `/api/gigachat/*` прокси + OAuth) |
| Утилиты | `uuid`, `dotenv`, `cors`, `concurrently` |

---

## Архитектура

Структура исходников построена по **Feature-Sliced Design**:

```
src/
├── app/            # провайдеры и глобальные стили (ErrorBoundary, global.css)
├── entities/       # бизнес-сущности
│   ├── chat/       #   - chats store (zustand + persist), типы Chat/Message
│   └── message/    #   - Message UI, разный рендер для user/assistant
├── features/       # пользовательские фичи
│   ├── chat-send/  #   - хук useChatSend + InputField (SSE, abort, attachments)
│   ├── chat-search/#   - поиск по истории (searchChats)
│   └── settings/   #   - панель параметров модели
├── widgets/        # композиция из features + entities
│   ├── Sidebar/    #   - список чатов, поиск, CRUD, settings button
│   └── ChatWindow/ #   - лента сообщений + поле ввода + автоскролл
├── shared/         # переиспользуемый слой
│   ├── api/        #   - адаптер GigaChat (gigachat.ts), SSE парсер (sse.ts)
│   ├── hooks/      #   - useCopyToClipboard
│   └── ui/         #   - Markdown, CodeBlock, IconButton, набор иконок
└── App.tsx
```

API-слой вынесен в `shared/api` и реализует **паттерн «Адаптер»**: фронт ничего не знает о формате upstream, работает с типизированными функциями `sendMessage`, `streamMessage`, `streamOrFallback`, `fetchModels`, `uploadFile`.

BFF-прокси `server/index.js` решает сразу три проблемы:

1. **OAuth**: держит `GIGACHAT_AUTH_KEY` на сервере и прозрачно меняет access-токен.
2. **CORS**: в браузере сам API GigaChat недоступен напрямую.
3. **TLS**: у Sber используется собственный CA; в dev-окружении `NODE_TLS_REJECT_UNAUTHORIZED=0` снимает проблему с цепочкой сертификатов.

Поток данных одного ответа ассистента:

```
[InputField] ──► useChatSend ──► gigachat.streamMessage
                                   │
                                   ├─► POST /api/gigachat/chat/completions  (BFF)
                                   │     └─► Bearer <cached token>
                                   │           └─► https://gigachat.devices.sberbank.ru/...
                                   │
                                   └─► parseSse(ReadableStream)
                                         └─► onDelta(chunk) → buffer
                                               └─► requestAnimationFrame flush
                                                     └─► store.updateMessage(...)
                                                           └─► <Markdown/> rerender
```

---

## Быстрый старт

### Требования

- Node.js ≥ 20
- npm ≥ 10
- Авторизационные данные GigaChat (Client ID + Client Secret → base64 строка) из личного кабинета Sber Studio: <https://developers.sber.ru/studio>

### 1. Установка зависимостей

```bash
cd "2 семестр/services/web/hw-final-gigachat"
npm install
```

### 2. Конфигурация

Скопируйте шаблон и впишите свой ключ:

```bash
cp .env.example .env
```

`.env`:

```dotenv
GIGACHAT_AUTH_KEY=<base64(ClientID:ClientSecret) из Sber Studio>
GIGACHAT_SCOPE=GIGACHAT_API_PERS       # физ.лица; или GIGACHAT_API_CORP
GIGACHAT_MODEL=GigaChat                # модель по умолчанию
PORT=8787
NODE_TLS_REJECT_UNAUTHORIZED=0         # обходит самоподписанный CA Sber в dev
```

### 3. Запуск в dev-режиме

```bash
npm run dev
```

Команда поднимает **одновременно**:
- Vite dev-server на <http://localhost:5173>
- BFF-прокси на <http://localhost:8787>

Открыть: <http://localhost:5173>.

Health-check BFF: <http://localhost:8787/api/gigachat/health> — должен вернуть `{"ok":true,"scope":"GIGACHAT_API_PERS","defaultModel":"GigaChat"}` при корректном ключе.

### 4. Production-сборка

```bash
npm run build
npm run preview    # локальный предпросмотр dist/
```

---

## Примеры запросов

### Нестриминговый запрос (из фронта → BFF → GigaChat)

```http
POST /api/gigachat/chat/completions
Content-Type: application/json

{
  "model": "GigaChat",
  "messages": [
    {"role": "system", "content": "Ты полезный ассистент"},
    {"role": "user",   "content": "Привет!"}
  ],
  "temperature": 0.7,
  "top_p": 0.9,
  "max_tokens": 2048,
  "repetition_penalty": 1.0,
  "stream": false
}
```

Ответ (`200 OK`):

```json
{
  "choices": [{
    "message": { "role": "assistant", "content": "Привет! Чем могу помочь?" },
    "finish_reason": "stop"
  }],
  "model": "GigaChat"
}
```

### Streaming (SSE)

Тот же эндпоинт с `"stream": true`. Заголовок ответа `Content-Type: text/event-stream`, куски:

```
data: {"choices":[{"delta":{"role":"assistant","content":"При"}}]}

data: {"choices":[{"delta":{"content":"вет"}}]}

data: {"choices":[{"delta":{"content":"! Чем могу помочь?"}}, "finish_reason": "stop"}]}

data: [DONE]
```

Парсится в `src/shared/api/sse.ts` и потоково дописывается в текущее `assistant`-сообщение.

### Multimodal (изображение + вопрос)

1. Пользователь нажимает «скрепку» в `InputField`, выбирает PNG/JPEG (< 8 МБ).
2. Перед отправкой `useChatSend` вызывает `POST /api/gigachat/files` (multipart/form-data).
3. GigaChat возвращает `{ id: "<uuid>" }`, id сохраняется в `ChatAttachment.fileId`.
4. В теле `/chat/completions` сообщение принимает вид:

```json
{
  "role": "user",
  "content": "Что на картинке?",
  "attachments": ["<uuid-from-/files>"]
}
```

---

## Скрипты

| Команда | Что делает |
|---|---|
| `npm run dev` | Запускает фронт и BFF параллельно (для локальной разработки). |
| `npm run dev:web` | Только Vite dev-server. |
| `npm run dev:api` | Только BFF-прокси. |
| `npm run build` | `tsc` + `vite build` → `dist/`. |
| `npm run preview` | Локальный предпросмотр production-сборки. |

---

## Соответствие критериям оценки

### Обязательные (с `*`)

| Критерий | Где реализовано |
|---|---|
| * Главный экран с messages + полем ввода | `widgets/ChatWindow/ChatWindow.tsx` + `features/chat-send/ui/InputField.tsx` |
| * Хронология + визуальное разделение user/assistant | `entities/message/ui/Message.tsx` |
| * Индикация загрузки | `TypingDots` в `Message.tsx` + `caret` в `Markdown.tsx` |
| * Автоскролл к последнему сообщению | `useLayoutEffect` в `ChatWindow.tsx` (уважает ручной скролл) |
| * Запросы к `POST /api/v1/chat/completions` | `shared/api/gigachat.ts`, прокси `server/index.js` |
| * SSE при streaming | `shared/api/sse.ts` + `streamMessage` в `gigachat.ts` |

### Интерфейс чата (ещё баллы)

| Критерий | Где |
|---|---|
| Markdown-форматирование (2 балла) | `shared/ui/Markdown.tsx`, `remark-gfm`, `rehype-highlight` |
| Копирование ответа (0.5) | `entities/message/ui/Message.tsx` + `useCopyToClipboard` |
| Остановить генерацию (0.5) | `useChatSend.stop()` + `AbortController` |

### Управление чатами (4 балла)

| Критерий | Где |
|---|---|
| Sidebar со списком чатов (0.5) | `widgets/Sidebar/Sidebar.tsx` |
| Авто-название чата из первого сообщения (0.5) | `chatsStore.autoTitle` |
| Переключение без потери данных (1) | zustand-стор держит все чаты + `activeChatId` |
| Редактирование/удаление с подтверждением (0.5) | inline-input + `window.confirm` в `Sidebar.tsx` |
| Поиск по названию и содержимому (0.5) | `features/chat-search/lib/search.ts` |
| Персистентность (1) | `zustand/persist` → localStorage |

### GigaChat API (сквозные, обязательны для 5+)

- Корректные заголовки `Authorization`, `Content-Type`, `Accept`, `RqUID` — BFF `server/index.js`.
- Контекст `messages` собирается из истории в `useChatSend.ts`.
- `stream: true` + SSE — см. выше.
- Параметры `temperature`, `top_p`, `max_tokens`, `repetition_penalty` редактируемы через настройки.

### Дополнительные баллы

- Multimodal (2 балла): `POST /files` через BFF + `attachments` в `messages`.

---

## Как это работает внутри

### Кеширование OAuth-токена

```js
let tokenCache = { token: '', expiresAt: 0 };

async function fetchAccessToken() {
  const now = Date.now();
  if (tokenCache.token && tokenCache.expiresAt - 60_000 > now) return tokenCache.token;
  // ... POST на /api/v2/oauth с Basic <GIGACHAT_AUTH_KEY>
}
```

Обновление — за 60 секунд до истечения. RqUID генерируем через `crypto.randomUUID()` — требование Sber.

### Парсинг SSE

Собственный `parseSse(stream)` разбирает поток по `\n\n` / `\r\n\r\n`, склеивает многострочные `data:`, завершает итерацию на `[DONE]` и пробрасывает `AbortSignal` вглубь `reader.cancel()`.

### Защита от «подвисших стримов»

`streamOrFallback` ловит любую ошибку стриминга (включая разрывы TLS) и делает обычный REST-запрос — требование ТЗ «Если не получается SSE, то обычный REST».

### Ленивый рендер markdown

Инкремент `delta` складывается в буфер и применяется к состоянию одним `requestAnimationFrame`. Так мы не переподписываем `<Markdown/>` на каждый токен и не теряем фреймы на длинных ответах.

---

## Известные ограничения

- В Windows из-за Node 22 рекомендуется держать `NODE_TLS_REJECT_UNAUTHORIZED=0` в dev. В production следует установить корневой сертификат Sber (`russian_trusted_root_ca.cer`) и убрать этот флаг.
- Файлы > 8 МБ отсекаются на фронте, чтобы не упираться в лимит раздела `/files`.
- localStorage на некоторых браузерах ограничен ~5 МБ; при большом количестве длинных чатов можно упереться. Миграция на IndexedDB (`idb-keyval`) — очевидное развитие.
- Голосовой ввод / TTS в этой итерации намеренно не реализованы: держим scope в границах обязательных критериев + multimodal.
