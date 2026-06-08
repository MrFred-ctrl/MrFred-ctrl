"""Tesla (TSLA) stock data via yfinance."""

import yfinance as yf


TICKER = "TSLA"


def get_stock_data():
    """Return a dict with current TSLA stock info."""
    try:
        ticker = yf.Ticker(TICKER)
        info = ticker.fast_info

        price = getattr(info, "last_price", None)
        prev_close = getattr(info, "previous_close", None)
        day_high = getattr(info, "day_high", None)
        day_low = getattr(info, "day_low", None)
        volume = getattr(info, "last_volume", None)

        if price is None or prev_close is None:
            # Fallback: try history
            hist = ticker.history(period="2d")
            if hist.empty:
                return _unavailable()
            price = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
            day_high = float(hist["High"].iloc[-1])
            day_low = float(hist["Low"].iloc[-1])
            volume = int(hist["Volume"].iloc[-1])

        change = float(price) - float(prev_close)
        pct_change = (change / float(prev_close)) * 100 if prev_close else 0.0

        return {
            "symbol": TICKER,
            "price": round(float(price), 2),
            "change": round(change, 2),
            "pct_change": round(pct_change, 2),
            "day_high": round(float(day_high), 2) if day_high else None,
            "day_low": round(float(day_low), 2) if day_low else None,
            "volume": int(volume) if volume else None,
            "available": True,
        }
    except Exception:
        return _unavailable()


def _unavailable():
    return {
        "symbol": TICKER,
        "price": None,
        "change": None,
        "pct_change": None,
        "day_high": None,
        "day_low": None,
        "volume": None,
        "available": False,
    }
