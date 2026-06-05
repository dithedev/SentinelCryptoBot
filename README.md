<p align="center">
  <img src="" alt="Sentinel Crypto Bot and Mini App banner" width="100%">
</p>


# Sentinel Crypto Bot and Mini App

Sentinel Crypto is a Telegram crypto assistant with a companion Telegram Mini
App. It lets users check supported market prices, create price alerts, run token
risk checks, and manage whale alert settings from one bot-backed interface.

Sentinel Crypto uses a production-oriented layered architecture with database
migrations, asynchronous background workers, typed API contracts, unit and
integration tests, CI checks, and a lightweight Telegram Mini App served by
FastAPI.

## ✨ Highlights

- **Telegram bot** built with `aiogram` 3
- **Telegram Mini App** with modular vanilla JavaScript, HTML, and CSS
- **FastAPI API** for Mini App endpoints and public price routes
- **PostgreSQL persistence** with SQLAlchemy 2 and Alembic migrations
- **Background workers** for price alert checks and whale notifications
- **Token risk checks** via a GoPlus-compatible security provider client
- **Whale Alerts Core** driven by an asynchronous worker and a provider-based
  integration layer. The project ships with a simulated provider so the full
  storage, deduplication, and notification pipeline works locally without
  external infrastructure.
- **Security-first architecture** with Telegram WebApp signed authentication,
  user-scoped data access, input validation, and in-memory rate limiting.
- **Quality gates** with Ruff, mypy strict mode, pytest, and GitHub Actions

## 🧭 Feature Overview

### 🤖 Telegram Bot

- Main navigation menu with prices, alerts, whales and risk checks
- Price alert creation flow with FSM state handling
- Active alert list and alert history
- Token risk check flow with chain selection and contract input
- Whale alert settings and latest whale event pages

### 📱 Mini App

- Market price cards for supported coins
- Unified Alerts screen: create an alert and manage active/history alerts
- Risk Check screen with readable signal labels and risk-level styling
- Whales screen with settings, tracked assets, event types, and a note when the
  simulated provider is active
- Telegram WebApp `initData` authentication for protected actions

### ⚙️ Workers

- Price worker checks active alerts and marks triggered alerts
- Whale worker polls the configured whale provider and sends notifications
- Telegram delivery handling disables notifications for blocked users
- Shared Telegram send throttling reduces burst delivery to the Bot API

## 🎬 Feature Demos

<details>
<summary><strong>📊 Market Prices</strong></summary>

Current USD prices for supported coins, available from both the Telegram bot and the Mini App.

<table>
  <thead>
    <tr>
      <th width="50%">Telegram Bot</th>
      <th width="50%">Mini App</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center">
        <img src="" width="260" alt="Market Prices Bot Demo">
      </td>
      <td>
        <img src="" width="260" alt="Market Prices Mini App Demo">
      </td>
    </tr>
  </tbody>
</table>

</details>

<details>
<summary><strong>🔔 Price Alerts</strong></summary>

Create above/below price alerts, review active alerts, and keep triggered or
disabled alerts in history.

<table>
  <thead>
    <tr>
      <th width="50%">Telegram Bot</th>
      <th width="50%">Mini App</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center">
        <img src="" width="260" alt="Market Prices Bot Demo">
      </td>
      <td>
        <img src="" width="260" alt="Market Prices Mini App Demo">
      </td>
    </tr>
  </tbody>
</table>

</details>

<details>
<summary><strong>🐋 Whale Alerts</strong></summary>

Configure whale notifications, update the minimum USD threshold, and browse
latest locally generated whale events.

<table>
  <thead>
    <tr>
      <th width="50%">Telegram Bot</th>
      <th width="50%">Mini App</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center">
        <img src="" width="260" alt="Market Prices Bot Demo">
      </td>
      <td>
        <img src="" width="260" alt="Market Prices Mini App Demo">
      </td>
    </tr>
  </tbody>
</table>

</details>

<details>
<summary><strong>🛡️ Token Risk Check</strong></summary>

Run token contract checks by selecting a blockchain and submitting an EVM
contract address. Results are formatted for both chat and Mini App views.

<table>
  <thead>
    <tr>
      <th width="50%">Telegram Bot</th>
      <th width="50%">Mini App</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center">
        <img src="" width="260" alt="Market Prices Bot Demo">
      </td>
      <td>
        <img src="" width="260" alt="Market Prices Mini App Demo">
      </td>
    </tr>
  </tbody>
</table>

</details>

## 🧰 Tech Stack

| Area | Tools |
|------|-------|
| Bot | aiogram 3, Telegram Bot API |
| API | FastAPI, Pydantic |
| Database | PostgreSQL, SQLAlchemy 2, Alembic |
| Workers | asyncio services, provider-based integrations |
| Mini App | HTML, CSS, ES modules |
| Testing | pytest, pytest-asyncio, httpx |
| Quality | Ruff, mypy strict mode, GitHub Actions |

## 🗂️ Project Layout

```text
app/
  api/              FastAPI app, routes, schemas, presenters
  bot/              Telegram bot routers, services, keyboards, texts
  core/             shared config, constants, errors, logging
  database/         SQLAlchemy models, session, health checks
  integrations/     external provider clients and provider abstractions
  miniapp/          static Telegram Mini App frontend, ES modules, CSS modules
  repositories/     database access layer
  risk/             risk scoring configuration and loader
  services/         domain use cases shared by API, bot, and workers
  utils/            validation, money, coin helpers
  worker/           background worker entrypoints and cycles
alembic/            database migrations
tests/              unit and integration tests
```

## ✅ Requirements

- Python 3.13
- PostgreSQL 16+
- Telegram bot token from [@BotFather](https://t.me/BotFather)

## 🚀 Quick Start

### 1. Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

For Linux/macOS:

```bash
source .venv/bin/activate
```

### 2. Install dependencies

For local development:

```bash
pip install -r requirements-dev.txt
```

For production/runtime only:

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
copy .env.example .env
```

For Linux/macOS:

```bash
cp .env.example .env
```

Fill at least:

- `BOT_TOKEN`
- `DATABASE_URL`
- `DATABASE_URL_TEST` if you run DB integration tests
- `MINIAPP_URL` if you want the bot to show the Mini App button

### 4. Prepare the database

Start PostgreSQL, then run migrations:

```bash
alembic upgrade head
```

### 5. Run the services

Open separate terminals:

```bash
uvicorn app.api.main:app --reload
```

```bash
python -m app.bot.main
```

```bash
python -m app.worker.main
```

The local API and Mini App are available at:

- API: `http://localhost:8000`
- Mini App: `http://localhost:8000/miniapp`

## 📱 Mini App Setup

Telegram requires Mini Apps to be available over HTTPS. For local testing, use a
tunnel:

```bash
ngrok http 8000
```

Then set:

```env
MINIAPP_URL=https://<your-ngrok-host>/miniapp
```

Restart the bot after changing `MINIAPP_URL`.

Ngrok can show a browser warning page before the Mini App loads. Telegram's
WebView cannot add the `ngrok-skip-browser-warning` request header for the
initial HTML request, so Cloudflare Tunnel or a real HTTPS deployment is a
better option for stable Mini App testing.

For deployment, use your production host, for example:

```env
MINIAPP_URL=https://<your-render-service>.onrender.com/miniapp
```

## 🐳 Docker Compose

Run API, bot, worker, and PostgreSQL for local development:

```bash
docker compose up --build
```

Compose also runs `alembic upgrade head` once through the `migrate` service
before starting the API, bot, and worker.

Services:

- API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

Inside Compose, `DATABASE_URL` is overridden to use the Docker service host
`postgres`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/sentinel_crypto
```

Your local `.env` can still use `localhost` for running services outside
Docker.

This compose file is intentionally development-oriented: it uses a local
PostgreSQL password, bind mounts the source tree, exposes the database port, and
runs the API with reload enabled. For production, use managed secrets, strong
database credentials, no bind mounts, no public database port, and a non-reload
API command.

## 🧪 Quality Checks

```bash
ruff check app tests
ruff format --check app tests
mypy app
pytest -q
```

Optional real PostgreSQL integration tests:

```bash
alembic upgrade head
pytest -m db -q
```

The repository also includes a GitHub Actions workflow that runs migrations,
Ruff, mypy, and pytest on pushes and pull requests.

## 🔐 Environment Variables

See [`.env.example`](.env.example) for the full list.

Important values:

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | Telegram bot token from BotFather |
| `DATABASE_URL` | SQLAlchemy async PostgreSQL URL |
| `DATABASE_URL_TEST` | Test database URL for integration tests |
| `MINIAPP_URL` | Public HTTPS Mini App URL used by the bot menu |
| `COINGECKO_BASE_URL` | Market price provider base URL |
| `GOPLUS_BASE_URL` | Token security provider base URL |
| `WHALE_PROVIDER` | `simulated` by default. Live whale sources can be added by implementing the existing `WhaleEventProvider` protocol. |
| `WHALE_SIMULATED_EVENTS_PER_CYCLE` | Number of simulated whale events per worker cycle |
| `TELEGRAM_SEND_RATE_PER_SECOND` | Max outgoing Telegram messages per second in workers |
| `BOT_USER_MIN_INTERVAL_SECONDS` | Minimum delay between bot actions from one user |
| `MINIAPP_API_REQUESTS_PER_MINUTE` | Max `/miniapp-api/*` requests per client IP per minute |

## ⏱️ Rate Limiting

- Workers throttle outgoing Telegram notifications via `TELEGRAM_SEND_RATE_PER_SECOND`.
- The bot throttles rapid button presses and messages per Telegram user.
- Mini App API routes under `/miniapp-api/*` return HTTP `429` when a client IP
  exceeds `MINIAPP_API_REQUESTS_PER_MINUTE`.
- Limits are in-memory and apply per running process. Use Redis or a gateway if
  you later scale to multiple API instances.

## 🛡️ Security & Production Notes

- Mini App API routes authenticate users with signed Telegram WebApp
  `initData`.
- The backend derives the user from Telegram-signed data and does not trust
  client-provided `telegram_id` values.
- User-owned resources, such as alerts and whale settings, are scoped by the
  authenticated internal user id.
- Database access uses SQLAlchemy query builders instead of string-built SQL for
  user input.
- Inputs are validated for supported coins, chains, EVM addresses, price ranges,
  whale thresholds, and pagination limits.
- Market prices use the live CoinGecko API. Whale tracking currently uses a
  simulated provider so the background worker, transaction-hash deduplication,
  settings filters, and Telegram delivery pipeline can run locally out of the box.
- For multi-instance production, rate limiting should move to a shared store or
  edge gateway, security headers should be enforced at the edge, and Docker
  configuration should use production secrets and non-development settings.

## ⚙️ Operational & Architecture Notes

- Whale tracking currently uses a simulated polling provider. Integrating a live
  production source requires adding a provider adapter that conforms to the
  existing `WhaleEventProvider` protocol.
- Token risk checks depend on third-party provider data and should be treated as
  informational, not financial advice.
- The Mini App uses browser ES modules directly. No frontend bundler is required
  for this version.

See [`SECURITY.md`](SECURITY.md) for responsible disclosure and credential
handling guidance.

## 📄 License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).
