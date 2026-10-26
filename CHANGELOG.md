# Changelog

## v1.0.0 · 2026-10-26

- Five seats: scanner, chain check, Claude analyst, risk engine, paper execution
- Real-wallet concentration: bonding curve and pool accounts excluded by owner program
- Typed `TokenThesis` and `StockThesis` via structured outputs, untrusted-input wrapping
- Rule-based exits: -35% stop, half at 2x, volume decay, 24h time out, 6h no-revenge bench
- Stocks mode on Alpaca paper with OTO stop orders
- Journal, Telegram alerts, kill switch, weekly review
- 17 offline tests, CI on Python 3.10 to 3.13
