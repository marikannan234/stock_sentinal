"""Canonical quote-provider symbol mapping for legacy/user-entered tickers."""

# Keep display/user symbols stable while querying the providers with their
# canonical ticker. GOOGLE is a common informal label for Alphabet, but GOOGL
# is the valid class-A ticker used by the quote providers.
QUOTE_SYMBOL_ALIASES = {
    "GOOGLE": "GOOGL",
}


def quote_symbol(symbol: str) -> str:
    """Return the canonical provider ticker for a user/display ticker."""
    normalized = symbol.strip().upper()
    return QUOTE_SYMBOL_ALIASES.get(normalized, normalized)
