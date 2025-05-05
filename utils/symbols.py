from datetime import datetime, timezone

def resolve_btc_contract() -> str:
    """Resolve BTC to its active front-month contract (e.g. BTCK5)."""
    month_codes = {
        1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
        7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z"
    }
    now = datetime.now(timezone.utc)
    month = now.month
    year = now.year
    code = month_codes[month]
    short_year = str(year)[-1]
    return f"BTC{code}{short_year}"

def resolve_gc_contract() -> str:
    """Resolve GC to its active front-month contract (e.g. GCM5)."""
    month_codes = {
        1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
        7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z"
    }
    now = datetime.now(timezone.utc)
    month = now.month
    year = now.year
    code = month_codes[month]
    short_year = str(year)[-1]
    return f"GC{code}{short_year}"

def resolve_mgc_contract() -> str:
    """Resolve MGC to its active front-month contract (e.g. MGCM5)."""
    month_codes = {
        1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
        7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z"
    }
    now = datetime.now(timezone.utc)
    month = now.month
    year = now.year
    code = month_codes[month]
    short_year = str(year)[-1]
    return f"MGCM{short_year}"

def resolve_symbol_alias(symbol: str) -> str:
    """
    Resolve user-facing aliases to correct Databento symbols.

    - Leaves futures roots (e.g., ES, NQ) untouched for .FUT logic.
    - Resolves BTC, GC, MGC to active month contracts.
    """
    symbol = symbol.upper()

    # Let root futures symbols pass through untouched
    if symbol in {"ES", "MES", "NQ", "MNQ", "RTY", "YM"}:
        return symbol

    aliases = {
        "BTC": resolve_btc_contract(),
        "GC": resolve_gc_contract(),
        "MGC": resolve_mgc_contract(),
    }

    return aliases.get(symbol, symbol)
