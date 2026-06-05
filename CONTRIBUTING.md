# Contributing

Thanks for checking out Sentinel Crypto. The project follows a modular structure
with a Telegram bot, FastAPI backend, background workers, a static Mini App,
domain services, repositories, and focused tests.

## Secrets and generated files

- Never commit `.env`, tokens, or database passwords
- Do not add `__pycache__/`, `*.pyc`, or `.pytest_cache/` to git
- Keep placeholders only in `.env.example`

Before pushing, you can verify:

```bash
git ls-files .env
git ls-files | findstr pycache
```

Both commands should print nothing.

## Local setup

1. Install dependencies: `pip install -r requirements-dev.txt`
2. Copy `.env.example` to `.env`
3. Fill `BOT_TOKEN` and `DATABASE_URL`
4. Run `alembic upgrade head`
5. Start API, bot, and worker (see [README.md](README.md))

Optional: `pre-commit install` if you use git hooks locally.

## Before opening a PR

```bash
ruff check app tests
ruff format app tests
mypy app
pytest -q
```

For real PostgreSQL integration tests, set `DATABASE_URL_TEST`, run migrations,
then:

```bash
alembic upgrade head
pytest -m db -q
```

## Code conventions

- Keep Telegram-specific logic in `app/bot`
- Keep business rules in `app/services`
- Keep SQL access in `app/repositories`
- Keep Mini App UI logic in `app/miniapp/js/features`
- Add tests when changing worker reliability or API contracts

## Questions or security reports

See [SECURITY.md](SECURITY.md) for security expectations.
