from app.services.symbols import quote_symbol


def test_google_alias_uses_alphabet_class_a_ticker():
    assert quote_symbol("GOOGLE") == "GOOGL"
    assert quote_symbol(" google ") == "GOOGL"


def test_other_tickers_are_normalized_without_aliasing():
    assert quote_symbol("aapl") == "AAPL"
    assert quote_symbol("GOOG") == "GOOG"
