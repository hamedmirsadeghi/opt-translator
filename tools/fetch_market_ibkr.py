#!/usr/bin/env python3
"""
fetch_market_ibkr.py — IBKR-powered fetcher for gld-options-translator.html

Pulls quotes + ATM implied volatility from YOUR Interactive Brokers account
via the Client Portal Gateway, writes market.js, and (optionally) pushes it
to a GitHub Pages repo so the hosted app updates from anywhere.

──────────────────────────────────────────────────────────────────────────
ONE-TIME SETUP
  1. Download "Client Portal Gateway" from IBKR:
       https://interactivebrokers.github.io/cpwebapi/  → "Download Gateway"
  2. Unzip, then run:   bin/run.bat root/conf.yaml      (Windows)
                        bin/run.sh  root/conf.yaml      (Linux/WSL)
  3. Browse to https://localhost:5000 and log in (accept the cert warning).
     Keep that window running — it IS your API session.
  4. pip install requests

EACH SESSION
     python fetch_market_ibkr.py          # IV read from ~12-day expiry
     python fetch_market_ibkr.py 20       # IV read from ~20-day expiry

OPTIONAL — publish to GitHub Pages (access the app anywhere):
  Create publish_config.json next to this script:
     {"token":"ghp_xxx", "repo":"youruser/yourrepo",
      "path":"market.js", "branch":"main"}
  token = fine-grained PAT with "Contents: read/write" on that repo only.
──────────────────────────────────────────────────────────────────────────
Data notes: quotes come at your account's entitlement (enable free delayed
data in IBKR account settings if you have no live subscription). The app's
"real IBKR ask" field on each card remains the execution truth.
"""
import base64
import datetime as dt
import json
import os
import sys

import requests
import urllib3

urllib3.disable_warnings()

BASE = "https://localhost:5000/v1/api"
IV_DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 12
UNDERLYINGS = ["GLD", "GLDM", "IBIT"]
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

S = requests.Session()
S.verify = False


def api(path, method="GET", **params):
    r = S.request(method, BASE + path, params=params or None, timeout=25)
    r.raise_for_status()
    return r.json()


def num(v):
    """IBKR snapshots return strings, sometimes prefixed C/D (close/delayed)."""
    if v is None:
        return None
    s = str(v).replace("%", "").replace(",", "")
    while s and s[0] not in "0123456789.-":
        s = s[1:]
    try:
        return float(s)
    except ValueError:
        return None


def check_auth():
    try:
        st = api("/iserver/auth/status", method="POST")
    except Exception:
        sys.exit("Gateway not reachable at https://localhost:5000 — start it "
                 "(bin/run.bat root/conf.yaml) and log in first.")
    if not st.get("authenticated"):
        sys.exit("Gateway is running but NOT logged in — open "
                 "https://localhost:5000 in a browser and sign in.")


def conid_of(symbol, sectype_pref=("STK", "ETF")):
    res = api("/iserver/secdef/search", symbol=symbol)
    for pref in sectype_pref:
        for item in res:
            secs = [s.get("secType") for s in item.get("sections", [])]
            if pref in secs or item.get("secType") == pref:
                return int(item["conid"])
    return int(res[0]["conid"]) if res else None


def snapshot(conids, fields):
    cs = ",".join(str(c) for c in conids)
    api("/iserver/marketdata/snapshot", conids=cs, fields=fields)  # preflight
    return api("/iserver/marketdata/snapshot", conids=cs, fields=fields)


def last_price(conid):
    if not conid:
        return None
    for _ in range(2):
        rows = snapshot([conid], "31,84,86")
        px = num(rows[0].get("31")) or num(rows[0].get("86")) or num(rows[0].get("84"))
        if px:
            return round(px, 2)
    return None


def month_str(d):
    return MONTHS[d.month - 1] + d.strftime("%y")


def atm_iv(und_conid, spot, target_days):
    """IV of the ATM call at the listed expiry nearest today+target_days."""
    want = dt.date.today() + dt.timedelta(days=target_days)
    months = {month_str(want), month_str(want + dt.timedelta(days=15)),
              month_str(want - dt.timedelta(days=15))}
    best = None  # (gap_days, option_conid, maturity)
    for m in months:
        try:
            st = api("/iserver/secdef/strikes", conid=und_conid,
                     secType="OPT", month=m, exchange="SMART")
            calls = st.get("call") or []
            if not calls:
                continue
            strike = min(calls, key=lambda k: abs(k - spot))
            infos = api("/iserver/secdef/info", conid=und_conid, secType="OPT",
                        month=m, strike=strike, right="C")
            for it in infos:
                mat = it.get("maturityDate")
                if not mat:
                    continue
                d = dt.date(int(mat[:4]), int(mat[4:6]), int(mat[6:8]))
                gap = abs((d - want).days)
                if best is None or gap < best[0]:
                    best = (gap, int(it["conid"]), d.isoformat())
        except Exception:
            continue
    if not best:
        return None, None
    for _ in range(2):
        rows = snapshot([best[1]], "7283")
        iv = num(rows[0].get("7283"))
        if iv:
            if iv < 3:          # some entitlements return decimal form
                iv *= 100
            return round(iv, 1), best[2]
    return None, best[2]


def publish_github(payload_text):
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "publish_config.json")
    if not os.path.exists(cfg_path):
        return
    cfg = json.load(open(cfg_path))
    hdr = {"Authorization": "Bearer " + cfg["token"],
           "Accept": "application/vnd.github+json"}
    url = "https://api.github.com/repos/{}/contents/{}".format(
        cfg["repo"], cfg.get("path", "market.js"))
    sha = None
    r = requests.get(url, headers=hdr,
                     params={"ref": cfg.get("branch", "main")}, timeout=20)
    if r.status_code == 200:
        sha = r.json().get("sha")
    body = {"message": "market data " + dt.datetime.now().isoformat(timespec="minutes"),
            "content": base64.b64encode(payload_text.encode()).decode(),
            "branch": cfg.get("branch", "main")}
    if sha:
        body["sha"] = sha
    r = requests.put(url, headers=hdr, json=body, timeout=20)
    print("GitHub publish:", "ok — hosted app will refresh" if r.ok
          else "FAILED {} {}".format(r.status_code, r.text[:120]))


def main():
    check_auth()
    print("IBKR session OK. Fetching (IV expiry ≈ {} days out)…".format(IV_DAYS))

    und = {}
    for sym in UNDERLYINGS:
        try:
            cid = conid_of(sym)
            px = last_price(cid)
            iv, exp = (None, None)
            if px:
                iv, exp = atm_iv(cid, px, IV_DAYS)
            und[sym] = {"px": px, "iv": iv, "ivExp": exp}
            print("  {:<5} px {}   IV {}%  ({})".format(sym, px, iv, exp))
        except Exception as e:
            und[sym] = {"px": None, "iv": None, "ivExp": None}
            print("  ! {}: {}".format(sym, e))

    xau = btc = None
    try:  # spot gold — entitlement varies by IBKR entity; harmless if absent
        xau = last_price(conid_of("XAUUSD", ("CMDTY", "CASH")))
    except Exception:
        pass
    try:  # spot bitcoin via Paxos/Zero Hash
        btc = last_price(conid_of("BTC", ("CRYPTO",)))
    except Exception:
        pass
    print("  XAU spot: {}   BTC spot: {}".format(
        xau or "n/a (type from TradingView)", btc or "n/a (type from TradingView)"))

    data = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "xau": xau, "btc": btc, "und": und}
    text = "window.MARKET=" + json.dumps(data) + ";"
    with open("market.js", "w") as f:
        f.write(text)
    print("Wrote market.js.")
    publish_github(text)


if __name__ == "__main__":
    main()
