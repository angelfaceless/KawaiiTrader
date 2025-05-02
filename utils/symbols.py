# utils/symbols.py

def resolve_symbol_alias(symbol: str) -> str:
    """
    Map user-friendly aliases like 'ES' or 'NQ' to Databento symbology.
    """
    symbol_map = {
        "ES": "ES.c.0",
        "NQ": "NQ.c.0",
        "RTY": "RTY.c.0",
        "YM": "YM.c.0",
        "BTC": "CME.BTC/USD",
        "ETH": "CME.ETH/USD",
    }

    return symbol_map.get(symbol.upper(), symbol)
