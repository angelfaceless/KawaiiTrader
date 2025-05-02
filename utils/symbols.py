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
        "BTC": "BTC.c.0",
        "ETH": "ETH.c.0",
        "MES": "MES.c.0",
        "MNQ": "MNQ.c.0",}
    return symbol_map.get(symbol.upper(), symbol)
