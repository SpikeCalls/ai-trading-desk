# Security

## What this repo will never ask for

- Private keys or seed phrases
- Wallet signing permissions
- Exchange API keys with withdrawal rights

If anything claiming to be this project asks for one, it's a scam.

## Keys it does use

- `ANTHROPIC_API_KEY` for the analyst seat
- Optional: `TELEGRAM_BOT_TOKEN`, `SOLANA_RPC_URL`, Alpaca **paper** keys

Keep them in `.env` (already in `.gitignore`). Never commit them, never paste them in issues.

## Prompt injection

Token names, descriptions, links and headlines are written by strangers. The analyst receives them wrapped as untrusted data, and the architecture makes sure a fooled analyst still cannot size or place a trade.

## Reporting

Found a vulnerability? Don't open a public issue. Message the maintainers on [Telegram](https://t.me/+Ykc8YKaJR6Q3NDNk) first.
