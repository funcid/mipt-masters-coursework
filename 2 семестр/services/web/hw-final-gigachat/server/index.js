/**
 * BFF для GigaChat API.
 *
 * Назначение:
 *  - прячет ClientID/ClientSecret на сервере (в браузер они не попадают);
 *  - самостоятельно получает и кеширует OAuth access_token;
 *  - пробрасывает chat/completions (в т.ч. SSE streaming) на фронт;
 *  - обходит CORS и особенности самоподписанного сертификата Sber на dev-машинах.
 *
 * Эндпоинты, которыми пользуется фронт:
 *   GET  /api/gigachat/models           -> список моделей
 *   POST /api/gigachat/chat/completions -> чат (JSON или SSE text/event-stream)
 *   GET  /api/gigachat/health           -> быстрый self-check
 */

import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import crypto from 'node:crypto';

const PORT = Number(process.env.PORT || 8787);
const AUTH_KEY = process.env.GIGACHAT_AUTH_KEY || '';
const SCOPE = process.env.GIGACHAT_SCOPE || 'GIGACHAT_API_PERS';
const DEFAULT_MODEL = process.env.GIGACHAT_MODEL || 'GigaChat';

const OAUTH_URL = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth';
const API_BASE = 'https://gigachat.devices.sberbank.ru/api/v1';

// Кеш access-токена: обновляем, если до конца жизни осталось <60 секунд.
let tokenCache = { token: '', expiresAt: 0 };

async function fetchAccessToken() {
  if (!AUTH_KEY) {
    throw new Error('GIGACHAT_AUTH_KEY не задан. Заполните .env по образцу .env.example');
  }

  const now = Date.now();
  if (tokenCache.token && tokenCache.expiresAt - 60_000 > now) {
    return tokenCache.token;
  }

  const body = new URLSearchParams({ scope: SCOPE });
  const response = await fetch(OAUTH_URL, {
    method: 'POST',
    headers: {
      Authorization: `Basic ${AUTH_KEY}`,
      'Content-Type': 'application/x-www-form-urlencoded',
      Accept: 'application/json',
      RqUID: crypto.randomUUID(),
    },
    body,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`OAuth failed: ${response.status} ${text}`);
  }

  const data = await response.json();
  tokenCache = {
    token: data.access_token,
    expiresAt: Number(data.expires_at) || now + 25 * 60_000,
  };
  return tokenCache.token;
}

const app = express();
app.use(cors());
app.use(express.json({ limit: '25mb' }));

app.get('/api/gigachat/health', async (_req, res) => {
  try {
    await fetchAccessToken();
    res.json({ ok: true, scope: SCOPE, defaultModel: DEFAULT_MODEL });
  } catch (error) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

app.get('/api/gigachat/models', async (_req, res) => {
  try {
    const token = await fetchAccessToken();
    const upstream = await fetch(`${API_BASE}/models`, {
      headers: { Authorization: `Bearer ${token}`, Accept: 'application/json' },
    });
    const text = await upstream.text();
    res.status(upstream.status).type('application/json').send(text);
  } catch (error) {
    res.status(502).json({ error: { code: 'UPSTREAM', message: error.message } });
  }
});

/**
 * Чат с поддержкой streaming.
 *
 * Если stream=true — прокидываем SSE как text/event-stream,
 * передавая все события как есть (включая финальный "[DONE]").
 * Иначе — обычный JSON-ответ.
 */
app.post('/api/gigachat/chat/completions', async (req, res) => {
  const payload = { model: DEFAULT_MODEL, ...req.body };
  const wantsStream = Boolean(payload.stream);

  let token;
  try {
    token = await fetchAccessToken();
  } catch (error) {
    res.status(500).json({ error: { code: 'AUTH', message: error.message } });
    return;
  }

  const controller = new AbortController();
  req.on('close', () => controller.abort());

  let upstream;
  try {
    upstream = await fetch(`${API_BASE}/chat/completions`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        Accept: wantsStream ? 'text/event-stream' : 'application/json',
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
  } catch (error) {
    if (error.name === 'AbortError') {
      res.end();
      return;
    }
    res.status(502).json({ error: { code: 'UPSTREAM', message: error.message } });
    return;
  }

  if (!upstream.ok) {
    const text = await upstream.text();
    res.status(upstream.status).type(upstream.headers.get('content-type') || 'application/json').send(text);
    return;
  }

  if (!wantsStream) {
    const text = await upstream.text();
    res.status(200).type('application/json').send(text);
    return;
  }

  // SSE: прокачиваем поток байт как есть.
  res.writeHead(200, {
    'Content-Type': 'text/event-stream; charset=utf-8',
    'Cache-Control': 'no-cache, no-transform',
    Connection: 'keep-alive',
    'X-Accel-Buffering': 'no',
  });
  res.flushHeaders?.();

  const reader = upstream.body.getReader();
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      res.write(value);
    }
  } catch (error) {
    if (error.name !== 'AbortError') {
      console.error('SSE relay error:', error);
    }
  } finally {
    res.end();
  }
});

/**
 * Загрузка файла (изображения) в GigaChat. Возвращает JSON с полем `id`,
 * который фронт добавляет в `messages[i].attachments` для multimodal-запроса.
 *
 * На вход принимаем raw-поток (Content-Type: multipart/form-data от браузера),
 * просто прокидываем его в upstream с добавлением Bearer-токена.
 */
app.post('/api/gigachat/files', express.raw({ type: '*/*', limit: '25mb' }), async (req, res) => {
  let token;
  try {
    token = await fetchAccessToken();
  } catch (error) {
    res.status(500).json({ error: { code: 'AUTH', message: error.message } });
    return;
  }

  try {
    const upstream = await fetch(`${API_BASE}/files`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': req.headers['content-type'] || 'multipart/form-data',
        Accept: 'application/json',
      },
      body: req.body,
    });
    const text = await upstream.text();
    res
      .status(upstream.status)
      .type(upstream.headers.get('content-type') || 'application/json')
      .send(text);
  } catch (error) {
    res.status(502).json({ error: { code: 'UPSTREAM', message: error.message } });
  }
});

app.listen(PORT, () => {
  console.log(`[gigachat-bff] listening on http://localhost:${PORT}`);
  if (!AUTH_KEY) {
    console.warn('[gigachat-bff] WARNING: GIGACHAT_AUTH_KEY is empty. See .env.example.');
  }
});
