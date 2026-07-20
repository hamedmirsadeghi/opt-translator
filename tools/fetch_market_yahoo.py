#!/usr/bin/env python3
"""
fetch_market.py — companion fetcher for gld-options-translator.html

Pulls current market data via Yahoo Finance (yfinance) and writes market.js
next to the app. Open/refresh the app and press "Fill from market data".

Fetches:
  - XAU spot   (XAUUSD=X, falls back to GC=F front-month futures)
  - BTC spot   (BTC-USD)
  - GLD / GLDM / IBIT last price
  - ATM implied volatility per underlying, from the option chain expiry
    nearest your typical buffer (default 12 days; pass another number as arg)

Usage:
  pip install yfinance          (once)
  python fetch_market.py        (before each session)
  python fetch_market.py 20     (use ~20-day expiry for the IV read)

Notes:
  - Yahoo data is delayed/unofficial; premiums to trade on still come from
    IBKR ("real IBKR ask" field on each card).
  - If Yahoo changes its API, update yfinance:  pip install -U yfinance
"""
import json, sys, datetime as dt

try:
    import yfinance as yf
except ImportError:
    sys.exit("yfinance missing — run:  pip install yfinance")

IV_DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 12
UNDERLYINGS = ["GLD", "GLDM", "IBIT"]


def last_price(symbol):
    try:
        t = yf.Ticker(symbol)
        p = None
        try:
            p = t.fast_info["last_price"]
        except Exception:
            pass
        if not p:
            hist = t.history(period="1d")
            if len(hist):
                p = float(hist["Close"].iloc[-1])
        return round(float(p), 2) if p else None
    except Exception as e:
        print(f"  ! {symbol}: {e}")
        return None


def atm_iv(symbol, spot, target_days):
    """IV of the ATM call on the listed expiry nearest today+target_days."""
    try:
        t = yf.Ticker(symbol)
        exps = t.options
        if not exps:
            return None, None
        today = dt.date.today()
        want = today + dt.timedelta(days=target_days)
        exp = min(exps, key=lambda e: abs((dt.date.fromisoformat(e) - want).days))
        calls = t.option_chain(exp).calls
        calls = calls[calls["impliedVolatility"].notna() & (calls["impliedVolatility"] > 0.01)]
        if not len(calls):
            return None, exp
        row = calls.iloc[(calls["strike"] - spot).abs().argsort().iloc[0]]
        return round(float(row["impliedVolatility"]) * 100, 1), exp
    except Exception as e:
        print(f"  ! {symbol} IV: {e}")
        return None, None


def main():
    print(f"Fetching (IV expiry target ≈ {IV_DAYS} days out)…")
    xau = last_price("XAUUSD=X") or last_price("GC=F")
    btc = last_price("BTC-USD")
    print(f"  XAU spot : {xau}")
    print(f"  BTC spot : {btc}")

    und = {}
    for sym in UNDERLYINGS:
        px = last_price(sym)
        iv, exp = (None, None)
        if px:
            iv, exp = atm_iv(sym, px, IV_DAYS)
        und[sym] = {"px": px, "iv": iv, "ivExp": exp}
        print(f"  {sym:<5}: px {px}   IV {iv}%  ({exp})")

    data = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "xau": xau, "btc": btc, "und": und}
    with open("market.js", "w") as f:
        f.write("window.MARKET=" + json.dumps(data) + ";")
    print("\nWrote market.js — refresh the app and press “Fill from market data”.")
    if xau and und["GLD"]["px"]:
        print(f"Sanity ratio GLD/XAU = {und['GLD']['px']/xau:.5f} (expect ≈ 0.091–0.093)")


if __name__ == "__main__":
    main()
