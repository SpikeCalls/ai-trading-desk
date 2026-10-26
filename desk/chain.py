"""Seat 2: chain facts. Straight from a Solana RPC node, no model involved.

Facts kill before judgements do: an open mint authority is not an opinion,
so it never reaches the analyst.
"""
from __future__ import annotations

import os

import requests

from config import CHAIN

RPC = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
SYSTEM_PROGRAM = "11111111111111111111111111111111"


def rpc(method: str, params: list, session: requests.Session | None = None):
    s = session or requests.Session()
    r = s.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
               timeout=20)
    r.raise_for_status()
    body = r.json()
    if "error" in body:
        raise RuntimeError(f"{method}: {body['error']}")
    return body["result"]


def facts(mint: str, session: requests.Session | None = None) -> dict:
    """Mint/freeze authority, supply, and holder concentration of REAL wallets.

    The bonding curve and the AMM pool hold huge balances by design. Their token
    accounts belong to program-owned addresses, not to wallets, so we look up who
    owns each top account and drop anything not owned by the System Program.
    """
    info = rpc("getAccountInfo", [mint, {"encoding": "jsonParsed"}], session)
    parsed = info["value"]["data"]["parsed"]["info"]
    decimals = int(parsed["decimals"])
    supply = int(parsed["supply"]) / 10 ** decimals

    largest = rpc("getTokenLargestAccounts", [mint], session)["value"]
    largest = largest[: CHAIN["largest_accounts_checked"]]
    token_accts = [x["address"] for x in largest]

    # token account -> its owner address
    accts = rpc("getMultipleAccounts", [token_accts, {"encoding": "jsonParsed"}],
                session)["value"]
    owners = [((a or {}).get("data", {}).get("parsed", {}).get("info", {}) or {}).get("owner")
              for a in accts]

    # owner address -> which program owns it (System Program = a normal wallet)
    uniq = [o for o in dict.fromkeys(owners) if o]
    owner_accts = rpc("getMultipleAccounts", [uniq, {"encoding": "base64"}],
                      session)["value"] if uniq else []
    program_of = {o: (acc or {}).get("owner") for o, acc in zip(uniq, owner_accts)}

    wallets: dict[str, float] = {}
    excluded = 0.0
    for row, owner in zip(largest, owners):
        amount = float(row.get("uiAmount") or 0)
        prog = program_of.get(owner)
        if owner and prog not in (None, SYSTEM_PROGRAM):
            excluded += amount            # curve, pool, vault: not a seller in the usual sense
            continue
        wallets[owner or row["address"]] = wallets.get(owner or row["address"], 0) + amount

    ranked = sorted(wallets.values(), reverse=True)
    share = lambda xs: (sum(xs) / supply) if supply else None
    return {
        "mint_authority": parsed.get("mintAuthority"),
        "freeze_authority": parsed.get("freezeAuthority"),
        "supply": supply,
        "top_wallet_pct": share(ranked[:1]),
        "top_10_pct": share(ranked[:10]),
        "program_held_pct": share([excluded]),
        "wallets_counted": len(ranked),
    }


def chain_kill(f: dict) -> str | None:
    """Plain facts against plain limits. First failure wins."""
    if f["mint_authority"] and not CHAIN["allow_mint_authority"]:
        return "mint_authority"
    if f["freeze_authority"] and not CHAIN["allow_freeze_authority"]:
        return "freeze_authority"
    if f["top_wallet_pct"] is not None and f["top_wallet_pct"] > CHAIN["max_top_wallet"]:
        return "top_wallet"
    if f["top_10_pct"] is not None and f["top_10_pct"] > CHAIN["max_top_10"]:
        return "top_10"
    return None
