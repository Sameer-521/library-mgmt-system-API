# library-api

An async REST API for managing a small library: books and their physical copies, users/staff/admins, loans (checkout and return with late fees), book-copy reservations, and an audit trail of every action.

## Stack

- Python 3.12+, FastAPI, Uvicorn
- SQLAlchemy 2.0 (async) with SQLite (aiosqlite); Postgres via asyncpg also available
- JWT auth (python-jose) with role-based access (user / staff / admin)
- Pydantic + pydantic-settings for validation and configuration
- pytest + pytest-asyncio for tests, ruff for linting

## Project layout

```
app/
  main.py        # FastAPI app, startup table creation, router wiring
  models.py      # SQLAlchemy models and enums
  crud.py        # database queries
  services.py    # business logic
  utils.py       # ID/barcode generators, helpers
  core/          # config, database engine/session, auth, audit middleware
  routers/       # HTTP endpoints: books.py, users.py
  schemas/       # Pydantic request/response models
  tests/         # pytest suite (in-memory SQLite)
start_server.py  # uvicorn runner
```

## Setup

```bash
uv sync                        # install dependencies from uv.lock
cp .env.example .env           # if present; otherwise create .env per Configuration below
uv run python start_server.py  # serve on http://127.0.0.1:8000 with reload
```

Interactive docs are available at `http://127.0.0.1:8000/docs` once running.

## Configuration

Settings are read from `.env` (see `app/core/config.py`). Key variables:

| Variable                                        | Default                                   | Purpose                                           |
| ----------------------------------------------- | ----------------------------------------- | ------------------------------------------------- |
| `DATABASE_URL`                                  | `sqlite+aiosqlite:///./library.db`        | database connection                               |
| `SECRET_KEY`                                    | placeholder                               | JWT signing secret, change before real use        |
| `ACCESS_TOKEN_EXPIRE_MINUTES`                   | 30                                        | token lifetime                                    |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` / `ADMIN_NAME` | admin@library.com / admin123 / Admin User | superuser created on first startup                |
| `HASH_ALGORITHM`                                | `sha256_crypt`                            | passlib password scheme                           |
| `JWT_ALGORITHM`                                 | `HS256`                                   | JWT signing algorithm                             |
| `TEST_MODE`                                     | False                                     | bypasses audit middleware and superuser bootstrap |

## Tests

```bash
uv run pytest
```

Tests run against an in-memory SQLite database; see `app/tests/conftest.py` for fixtures.

## Auth quickstart

1. Sign up a regular user: `POST /users/sign-up` (form-encoded `full_name`, `email`, `password`).
2. Log in: `POST /auth/login` (form-encoded `email`, `password`) to get a bearer token.
3. Send the token as `Authorization: Bearer <token>` on protected endpoints. The token's `role` claim (`user`/`staff`/`admin`) tells the frontend what to show.
4. A superuser (staff + admin) is created automatically from the `ADMIN_*` variables on first startup and logs in through the same `POST /auth/login`.
