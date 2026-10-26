"""Seat 1: the scanner. Pulls fresh Solana pools and kills everything a comparison can kill.

GeckoTerminal is free and needs no key, but allows about 10 calls a minute,
so one cycle spends `pages` calls here and nothing per token.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import requests

from config import SCAN

GT = "https://api.geckoterminal.com/api/v2"
DEX = "https://api.dexscreener.com/latest/dex/tokens"
HEADERS = {"Accept": "application/json", "User-Agent": "ai-trading-desk/1.0"}


def _f(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _age_minutes(iso: str | None) -> float:
    if not iso:
        return 0.0
    created = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return max(0.0, (datetime.now(timezone.utc) - created).total_seconds() / 60)


def parse_pool(pool: dict, symbols: dict[str, str]) -> dict | None:
    """One GeckoTerminal pool -> the desk's token dict. Field names are fixed here, once."""
    a = pool.get("attributes", {})
    rel = pool.get("relationships", {})
    base_id = ((rel.get("base_token") or {}).get("data") or {}).get("id", "")
    dex_id = ((rel.get("dex") or {}).get("data") or {}).get("id", "")
    if not base_id.startswith("solana_"):
        return None
    mint = base_id.split("_", 1)[1]
    tx_h1 = (a.get("transactions") or {}).get("h1") or {}
    vol = a.get("volume_usd") or {}
    chg = a.get("price_change_percentage") or {}
    return {
        "mint": mint,
        "symbol": symbols.get(base_id, a.get("name", "?").split(" / ")[0]),
        "pool": a.get("address"),
        "dex": dex_id,
        "price_usd": _f(a.get("base_token_price_usd")),
        "mcap_usd": _f(a.get("market_cap_usd")) or _f(a.get("fdv_usd")),
        "liquidity_usd": _f(a.get("reserve_in_usd")),
        "volume_m5": _f(vol.get("m5")), "volume_h1": _f(vol.get("h1")),
        "volume_h6": _f(vol.get("h6")), "volume_h24": _f(vol.get("h24")),
        "buys_h1": int(tx_h1.get("buys") or 0), "sells_h1": int(tx_h1.get("sells") or 0),
        "buyers_h1": int(tx_h1.get("buyers") or 0),
        "change_m5": _f(chg.get("m5")), "change_h1": _f(chg.get("h1")),
        "change_h6": _f(chg.get("h6")),
        "age_minutes": round(_age_minutes(a.get("pool_created_at")), 1),
    }


def new_tokens(session: requests.Session | None = None) -> list[dict]:
    """Fresh pools on Solana, newest first, deduplicated by mint."""
    s = session or requests.Session()
    out, seen = [], set()
    for page in range(1, SCAN["pages"] + 1):
        r = s.get(f"{GT}/networks/solana/new_pools",
                  params={"page": page, "include": "base_token,dex"},
                  headers=HEADERS, timeout=20)
        if r.status_code == 429:
            time.sleep(60)          # back off a full minute, never retry in place
            break
        r.raise_for_status()
        body = r.json()
        symbols = {i["id"]: i["attributes"].get("symbol", "?")
                   for i in body.get("included", []) if i.get("type") == "token"}
        for pool in body.get("data", []):
            t = parse_pool(pool, symbols)
            if not t or t["mint"] in seen:
                continue
            if SCAN["pump_only"] and t["dex"] not in SCAN["pump_dexes"]:
                continue
            seen.add(t["mint"])
            out.append(t)
    return out


def free_kill(t: dict) -> str | None:
    """Pass one. Pure arithmetic on data we already hold. Returns the failed check or None."""
    if not SCAN["min_age_minutes"] <= t["age_minutes"] <= SCAN["max_age_hours"] * 60:
        return "age"
    if t["liquidity_usd"] < SCAN["min_liquidity_usd"]:
        return "liquidity"
    if t["volume_h1"] < SCAN["min_volume_h1_usd"]:
        return "volume"
    if not SCAN["min_mcap_usd"] <= t["mcap_usd"] <= SCAN["max_mcap_usd"]:
        return "mcap"
    if t["buys_h1"] + t["sells_h1"] < SCAN["min_trades_h1"]:
        return "trades"
    if t["buys_h1"] and t["sells_h1"] / t["buys_h1"] < SCAN["min_sells_ratio_h1"]:
        return "no_sells"
    return None


def socials(mint: str, session: requests.Session | None = None) -> dict:
    """X / Telegram / site links as the project published them (DexScreener token info).
    Taken from the listing, never from a search: a search finds fan accounts."""
    s = session or requests.Session()
    try:
        pairs = s.get(f"{DEX}/{mint}", headers=HEADERS, timeout=20).json().get("pairs") or []
    except Exception:
        return {"x": None, "telegram": None, "website": None}
    info = {}
    for p in pairs:
        if p.get("info"):
            info = p["info"]
            break
    links = {x.get("type"): x.get("url") for x in info.get("socials", [])}
    sites = info.get("websites") or []
    return {"x": links.get("twitter"), "telegram": links.get("telegram"),
            "website": sites[0].get("url") if sites else None}


def quote(mint: str, session: requests.Session | None = None) -> dict | None:
    """Live price and volume for an open position, from the deepest pair."""
    s = session or requests.Session()
    try:
        pairs = s.get(f"{DEX}/{mint}", headers=HEADERS, timeout=20).json().get("pairs") or []
    except Exception:
        return None
    if not pairs:
        return None
    p = max(pairs, key=lambda x: (x.get("liquidity") or {}).get("usd") or 0)
    vol = p.get("volume") or {}
    return {"price_usd": _f(p.get("priceUsd")),
            "liquidity_usd": _f((p.get("liquidity") or {}).get("usd")),
            "volume_h6": _f(vol.get("h6")), "volume_h24": _f(vol.get("h24"))}
