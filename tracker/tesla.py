"""Stock data via yfinance — TSLA and SPCX."""

import yfinance as yf


# ---------------------------------------------------------------------------
# Generic helper
# ---------------------------------------------------------------------------

def get_stock_data(ticker: str = "TSLA") -> dict:
    """Return a dict with current stock info for *ticker*.

    Works for any symbol supported by yfinance.  If data is unavailable
    (e.g. the ticker does not yet trade publicly) the returned dict will
    have ``available: False``.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info

        price = getattr(info, "last_price", None)
        prev_close = getattr(info, "previous_close", None)
        day_high = getattr(info, "day_high", None)
        day_low = getattr(info, "day_low", None)
        volume = getattr(info, "last_volume", None)

        if price is None or prev_close is None:
            # Fallback: try history
            hist = t.history(period="2d")
            if hist.empty:
                return _unavailable(ticker)
            price = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
            day_high = float(hist["High"].iloc[-1])
            day_low = float(hist["Low"].iloc[-1])
            volume = int(hist["Volume"].iloc[-1])

        change = float(price) - float(prev_close)
        pct_change = (change / float(prev_close)) * 100 if prev_close else 0.0

        return {
            "symbol": ticker,
            "price": round(float(price), 2),
            "change": round(change, 2),
            "pct_change": round(pct_change, 2),
            "day_high": round(float(day_high), 2) if day_high else None,
            "day_low": round(float(day_low), 2) if day_low else None,
            "volume": int(volume) if volume else None,
            "available": True,
        }
    except Exception:
        return _unavailable(ticker)


def _unavailable(ticker: str = "TSLA") -> dict:
    return {
        "symbol": ticker,
        "price": None,
        "change": None,
        "pct_change": None,
        "day_high": None,
        "day_low": None,
        "volume": None,
        "available": False,
    }


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------

def get_tsla_data() -> dict:
    """Return TSLA stock data."""
    return get_stock_data("TSLA")


def get_spcx_data() -> dict:
    """Return SPCX ETF data.

    SPCX is an ETF with SpaceX exposure.  If yfinance returns no price data
    (e.g. the ETF is not yet tradeable), the returned dict will have
    ``available: False``.
    """
    return get_stock_data("SPCX")
