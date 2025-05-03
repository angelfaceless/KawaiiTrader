from datetime import datetime, timezone


def resolve_btc_contract() -> str:
    """Resolve BTC to its active front-month contract (e.g. BTCK5)."""
    month_codes = {
        1: "F",  2: "G", 3: "H", 4: "J",
        5: "K",  6: "M", 7: "N", 8: "Q",
        9: "U", 10: "V", 11: "X", 12: "Z"
    }

    now = datetime.now(timezone.utc)
    month = now.month
    year = now.year

    code = month_codes[month]
    short_year = str(year)[-1]  # '2025' → '5'

    return f"BTC{code}{short_year}"


def resolve_symbol_alias(symbol: str) -> str:
    aliases = {
        "ES": "ES.c.0",
        "MES": "MES.c.0",
        "NQ": "NQ.c.0",
        "MNQ": "MNQ.c.0",
        "RTY": "RTY.c.0",
        "YM": "YM.c.0",
        "BTC": resolve_btc_contract(),
    }
    return aliases.get(symbol.upper(), symbol)
