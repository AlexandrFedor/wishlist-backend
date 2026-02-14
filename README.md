# Wishlist Backend

API для социального вишлиста — FastAPI + PostgreSQL + Socket.IO.

## Стек

- **FastAPI** — async REST API
- **SQLAlchemy 2.0** — async ORM
- **PostgreSQL** — база данных
- **Alembic** — миграции
- **Socket.IO** — real-time обновления
- **JWT** — аутентификация (access + refresh токены)

## Быстрый старт

### 1. Клонировать и создать окружение

```bash
git clone https://github.com/AlexandrFedor/wishlist-backend.git
cd wishlist-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Запустить PostgreSQL

```bash
docker run -d --name wishlist-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=wishlist \
  -p 5432:5432 \
  postgres:15-alpine
```

### 3. Настроить переменные окружения

```bash
cp .env.example .env
```

Содержимое `.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/wishlist
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=http://localhost:3000
```

### 4. Применить миграции

```bash
alembic upgrade head
```

### 5. Запустить сервер

```bash
uvicorn app.main:app --reload
```

Сервер запустится на `http://localhost:8000`.

## API документация

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Эндпоинты

### Auth
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/auth/register` | Регистрация |
| POST | `/api/auth/login` | Вход |
| POST | `/api/auth/refresh` | Обновление токена |
| POST | `/api/auth/logout` | Выход |
| GET | `/api/auth/me` | Текущий пользователь |

### Wishlists
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/wishlists` | Мои вишлисты |
| POST | `/api/wishlists` | Создать вишлист |
| GET | `/api/wishlists/{id}` | Получить вишлист (владелец) |
| PUT | `/api/wishlists/{id}` | Обновить |
| DELETE | `/api/wishlists/{id}` | Удалить |
| GET | `/api/w/{slug}` | Публичный вишлист (без авторизации) |

### Items
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/wishlists/{id}/items` | Добавить товар |
| PUT | `/api/items/{id}` | Обновить товар |
| DELETE | `/api/items/{id}` | Удалить товар |
| POST | `/api/items/autofill` | Автозаполнение по URL |

### Reservations
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/items/{id}/reserve` | Зарезервировать |
| PUT | `/api/reservations/{id}` | Обновить резервацию |
| DELETE | `/api/reservations/{id}` | Отменить |
| GET | `/api/items/{id}/reservations` | Список резерваций |

### Utility
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/health` | Health check |

## WebSocket

Подключение через Socket.IO на `http://localhost:8000`.

```js
// Подписаться на обновления вишлиста
socket.emit("join:wishlist", { slug: "my-wishlist-abc123" });

// Слушать события
socket.on("item:reserved", (data) => { ... });
socket.on("item:unreserved", (data) => { ... });
```

## Структура проекта

```
app/
├── main.py              # Точка входа
├── core/
│   ├── config.py        # Настройки (.env)
│   ├── security.py      # JWT, bcrypt
│   └── websocket.py     # Socket.IO
├── db/
│   ├── database.py      # SQLAlchemy engine
│   └── session.py       # get_db dependency
├── models/              # SQLAlchemy модели
├── schemas/             # Pydantic схемы
├── services/            # Бизнес-логика
├── api/
│   ├── dependencies.py  # Auth dependencies
│   └── endpoints/       # Роутеры
alembic/                 # Миграции
```

## Деплой (Railway)

1. Создайте проект на [railway.app](https://railway.app)
2. Подключите GitHub-репозиторий
3. Добавьте PostgreSQL сервис
4. Установите переменные:
   - `DATABASE_URL` — из PostgreSQL сервиса
   - `SECRET_KEY` — случайная строка
   - `ALLOWED_ORIGINS` — URL фронтенда

Деплой автоматический через `Procfile` при каждом `git push`.
