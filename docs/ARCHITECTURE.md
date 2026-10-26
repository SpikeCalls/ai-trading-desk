# Architecture

![Five seats, one job each](../assets/five-seats.png)

## One cycle (every 60 seconds)

```mermaid
sequenceDiagram
    autonumber
    participant L as run_crypto.py
    participant S as Scanner
    participant C as Chain (RPC)
    participant A as Analyst (Claude)
    participant R as Risk engine
    participant B as Paper broker
    participant J as Journal
    L->>B: manage open positions (exits by rule)
    L->>S: new_tokens()
    S-->>L: fresh pools, ranked by turnover
    loop each token, until budget runs out
        L->>S: free_kill(token)
        alt killed
            L->>J: reject + reason, bench
        else survives
            L->>C: facts(mint)
            alt mint / freeze / concentration
                L->>J: reject + reason, bench
            else facts pass
                L->>A: analyze_token(token, facts, links)
                A-->>L: TokenThesis
                L->>R: check_token_trade(thesis, account, liquidity)
                R-->>L: approved?, ticket, reason
                L->>J: decision
                opt approved
                    L->>B: buy (paper) + Telegram alert
                end
            end
        end
    end
    L->>J: cycle stats
```

## Budgets

| Resource | Per cycle | Why |
| --- | --- | --- |
| GeckoTerminal | `SCAN.pages` calls | free tier is about 10 calls a minute |
| Solana RPC | 8 tokens × 4 calls | public RPC rate-limits fast |
| Claude | 3 calls | caps the bill no matter what the market does |

## Real-wallet concentration

1. `getAccountInfo(mint)` → mint authority, freeze authority, supply, decimals
2. `getTokenLargestAccounts(mint)` → top token accounts
3. `getMultipleAccounts(token accounts)` → the owner of each
4. `getMultipleAccounts(owners)` → which program owns each owner

Owners held by the System Program are wallets. Anything else (bonding curve, pool, vault) is excluded from concentration and reported as `program_held_pct`.

## The bench

A rejected token sits out for a time set by **why** it failed: 10 minutes for "too young", 4 hours for "no sells", forever for an open mint authority, 6 hours after any exit. See `BENCH_MINUTES` in `config.py`.
