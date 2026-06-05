# Security

## Reporting

If you find a security issue, please open a private report or contact the maintainer directly instead of filing a public issue with exploit details.

## Secrets

- Do not commit `.env` or real `BOT_TOKEN` values
- Rotate Telegram bot tokens and database credentials if they were ever exposed in git history
- Use hosting provider secret stores for production (Render, Fly.io, etc.)

## Mini App authentication

Authenticated Mini App routes rely on signed Telegram WebApp `initData`. The backend does not trust client-provided `telegram_id` fields.

## Data & Implementation Notes

- **Whale Alerts:** Uses a simulated data provider by default (`WHALE_PROVIDER=simulated`). Live whale sources can be added by implementing the existing provider protocol.
- **Risk Checks:** Token analysis relies on third-party API data from GoPlus and should be treated as informational only, not financial advice.
