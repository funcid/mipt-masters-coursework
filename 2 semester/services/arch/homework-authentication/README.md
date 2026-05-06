# Домашнее задание: Аутентификация

Реализованы 2 микросервиса:

- `auth_service`:
  - `POST /register` — регистрация пользователя (`email`, `password`)
  - `POST /auth` — аутентификация и выдача JWT (`user_id`, `exp`)
- `post_service`:
  - `POST /messages` — сохранение сообщения от имени пользователя по JWT

Используется один контейнер с PostgreSQL и две таблицы:

- `users(id, email, password)`
- `messages(id, user_id, time, message)`

## Запуск

Из папки `homework-authentication`:

```bash
docker compose up --build
```

Сервисы:

- auth: `http://localhost:8101`
- post: `http://localhost:8102`
- db: `localhost:5432`

## Проверка в Postman

Импортируйте `postman_collection.json` и выполните запросы:

1. `Register user`
2. `Authenticate user` (токен сохранится в переменную `jwt_token`)
3. `Create message`

## Ожидаемые коды ответов

### Auth service

- `POST /register`
  - `201` — успешная регистрация
  - `400` — слабый пароль / некорректный email / email уже существует
- `POST /auth`
  - `200` + JSON `{"token": "<jwt>"}` — успех
  - `401` — неверный email или пароль (пустой ответ)

### Post service

- `POST /messages`
  - `201` — сообщение сохранено (пустой ответ)
  - `400` — некорректная подпись токена / поврежденный токен (пустой ответ)
  - `401` — токен отсутствует или срок действия истек (пустой ответ)
