# AI Trading Desk

A five-seat trading desk for pump.fun launches, any Solana token, and US stocks.
**The AI reads. The code decides. You sign.**

```
 SCANNER        CHAIN CHECK       ANALYST            RISK ENGINE        EXECUTION
 GeckoTerminal  Solana RPC        Claude Opus 5.5    plain Python       paper broker
 every launch   mint / freeze     typed thesis       size, limits,      + alert to you
 free cuts      real-wallet top10 score 0-10         daily stop         + journal
    hundreds  ->     tens      ->    a handful    ->   one or none   ->   kill switch
```

Each pass costs more than the one before it, so each one kills harder.
Facts kill before judgements: an open mint authority never reaches the model.

> Not financial advice. Most memecoins go to zero and most strategies lose money,
> automated ones included. This repo trades **paper only**. It holds no private key,
> signs nothing, and cannot move your funds. When it finds a setup it alerts you,
> and you decide in your own terminal.

## Quick start

```bash
git clone <your-fork-url> ai-trading-desk && cd ai-trading-desk
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add ANTHROPIC_API_KEY, optional Telegram + RPC
python -m unittest discover -s tests -v
python run_crypto.py --shadow --once     # one cycle, journal + alerts only
python run_crypto.py                     # paper trading, every 60 s
```

Stocks (Alpaca paper account, free):

```bash
python run_stocks.py --once
```

Stop everything, from anywhere (a synced folder works from your phone):

```bash
touch KILL
```

## The seats

| Seat | File | Job | Model? |
| --- | --- | --- | --- |
| 1 Scanner | `desk/scanner.py` | Fresh pump.fun / PumpSwap pools from GeckoTerminal, free cuts on age, liquidity, volume, mcap, trades, sell ratio | No |
| 2 Chain check | `desk/chain.py` | Mint + freeze authority, top wallet and top 10 share of **real wallets** (curve and pool accounts excluded by owner program) | No |
| 3 Analyst | `desk/analyst.py` | Claude Opus 5.5 fills a typed `TokenThesis`: verdict, score, red flags, shape, invalidation, sources | Yes |
| 4 Risk engine | `desk/risk.py` | Verdict and score gates, quiet hours, daily loss stop, max positions, ticket = min(risk cap, size cap, 2% of pool) | No |
| 5 Execution | `desk/broker.py`, `desk/ops.py` | Paper fills with fees and slippage, rule-based exits, journal, bench, Telegram, kill switch | No |

Every number lives in `config.py`. Retune there and nowhere else.

## Exits (code, not conversation)

- Stop at -35% from entry
- Sell half at 2x, once
- Close when 6-hour volume falls under 20% of the 24-hour pace (after 30 min held)
- Close after 24 hours, or when the price can't be fetched
- A closed token sits out 6 hours: no revenge re-entry

## Cost

The analyst only sees tokens that survived every free check, capped at 3 calls per
cycle. A call is roughly 1,500 input and 600 output tokens (thinking included, it
varies). At Opus 5.5 list prices ($4 / $20 per million) that is about **$0.02 a call**.
A busy day of 300 calls is about $5. Check the Anthropic pricing page for current rates.

## The weekly review

```bash
python review.py            # stats from journal.jsonl
python review.py --claude   # plus a blunt written review from a cheaper model
```

Read the rejections, not just the trades. They tell you whether your filters are
cutting losers or cutting winners.

## Rules this repo will not break

1. No private keys, no signing, no live crypto execution.
2. The model never sizes a position or places an order.
3. Every third-party string (token names, links, headlines) reaches the model wrapped as untrusted text.
4. A missing number is missing, never a pass.
5. Paper first. Weeks, not days. Don't trust a backtest of model judgement: the model may already know how the story ended.

## Files

```
config.py          every threshold
run_crypto.py      the loop: scan -> chain -> analyst -> risk -> paper
run_stocks.py      Alpaca paper, OTO orders with the stop attached
review.py          weekly stats + optional Claude review
desk/              the five seats
prompts/           manual mode: the same desk as a Claude Project + prompt pack
tests/             offline tests, no keys needed
```

License: MIT.
