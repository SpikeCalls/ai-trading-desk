"""Every number the desk uses lives here. Retune the desk by editing this file only.

These are STARTING values, not advice. Run in paper mode, read the journal,
and move a number only when the journal tells you to.
"""

# ---------- Seat 1: scanner (free cuts, data already in the GeckoTerminal batch) ----------
SCAN = {
    "pages": 2,                    # new_pools pages per cycle (1 page = 20 pools)
    "pump_only": True,             # only pump.fun curve + PumpSwap pools
    "pump_dexes": {"pump-fun", "pumpswap"},
    "min_age_minutes": 10,         # younger: the data is noise
    "max_age_hours": 6,            # older with no new move: not a launch any more
    "min_liquidity_usd": 8_000,
    "min_volume_h1_usd": 15_000,
    "min_mcap_usd": 25_000,
    "max_mcap_usd": 5_000_000,
    "min_trades_h1": 120,
    "min_sells_ratio_h1": 0.15,    # sells / buys. Below this nobody can sell = honeypot smell
}

# ---------- Seat 2: chain facts (Solana RPC) ----------
CHAIN = {
    "max_top_wallet": 0.05,        # biggest real wallet, excl. curve / pool / program accounts
    "max_top_10": 0.25,            # top 10 real wallets combined
    "allow_mint_authority": False, # supply can be printed -> hard no
    "allow_freeze_authority": False,
    "largest_accounts_checked": 20,
}

# ---------- Seat 3: analyst ----------
ANALYST_MODEL = "claude-opus-5-5"
REVIEW_MODEL = "claude-sonnet-5-5"   # cheaper model for the weekly review
ANALYST_MAX_TOKENS = 8_000
MIN_SCORE = 7                        # 0-10, the analyst's score must clear this

# ---------- Seat 4: risk engine (pure code) ----------
RISK = {
    "max_risk_per_trade": 0.01,    # lose at most 1% of equity if the stop hits
    "max_position_pct": 0.02,      # no position above 2% of equity (memecoins)
    "max_pool_share": 0.02,        # never be more than 2% of the pool: you'd be the exit
    "max_open_positions": 3,
    "max_daily_loss_pct": 0.03,    # down 3% on the day -> desk stops until tomorrow
    "min_ticket_usd": 10,          # below this, fees eat the edge
    "quiet_hours": (1, 7),         # local hours with no new entries (1 AM to 7 AM)
}

# ---------- Seat 5: exits (paper broker applies these, no model involved) ----------
EXITS = {
    "stop_pct": 0.35,              # -35% from entry -> close all
    "take_half_at": 2.0,           # 2x -> sell half, let the rest ride
    "volume_decay_ratio": 0.20,    # h6 volume / (h24/4) under this -> close
    "volume_decay_min_minutes": 30,
    "max_hold_hours": 24,
}

PAPER = {
    "starting_equity_usd": 1_000,
    "fee_pct": 0.01,               # pump.fun charges ~1% per swap on the curve
    "slippage_pct": 0.02,          # assume 2% worse than the quoted price
}

CYCLE_SECONDS = 60                 # crypto scan cycle
STOCK_CYCLE_SECONDS = 15 * 60      # stocks: every 15 min while the market is open

# How long a rejected token sits out, by the check that failed (minutes)
BENCH_MINUTES = {
    "exited": 360,                 # stopped out or closed: no revenge re-entry for 6h
    "mint_authority": 100_000, "freeze_authority": 100_000,
    "top_wallet": 120, "top_10": 120, "no_sells": 240,
    "skip": 60, "watch": 15, "score": 20,
    "age": 10, "liquidity": 10, "volume": 10, "mcap": 15, "trades": 10,
}
DEFAULT_BENCH = 30
