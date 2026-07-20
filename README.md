# XAU → GLD Options Translator — Zero-PC Cloud Setup

Your app hosted free on **GitHub Pages**, with market data (GLD / GLDM / IBIT
prices + ATM implied volatility, XAU & BTC spot) refreshed automatically every
15 minutes during US market hours by **GitHub Actions**. No PC involved, no
server, $0/month.

```
┌─────────────────────────── GitHub (free) ───────────────────────────┐
│  Actions cron (every 15 min, market hours)                          │
│      └─ fetch_market_cloud.py                                       │
│            ├─ Tradier API ──── GLD/GLDM/IBIT price + ATM IV         │
│            ├─ stooq/goldprice ─ XAU spot (keyless)                  │
│            └─ Coinbase/Kraken ─ BTC spot (keyless)                  │
│      └─ commits market.js  ──►  GitHub Pages serves index.html      │
└──────────────────────────────────────────────────────────────────────┘
                                        ▲
                 you, from any phone/laptop, anywhere ──┘
```

## What's in this bundle

| File | Purpose |
|---|---|
| `index.html` | The translator app (unchanged logic, hosted-ready) |
| `fetch_market_cloud.py` | The fetcher that Actions runs |
| `.github/workflows/market-data.yml` | The schedule + commit automation |
| `market.js` | Seed data file (gets overwritten by the bot) |
| `tools/` | Optional local fetchers (IBKR gateway / Yahoo) — not used in the cloud |

---

## Setup — about 15 minutes, once

### Step 1 — one-minute data key (pick ONE, no KYC forms)
**Option A — MarketData.app (recommended).** Go to **marketdata.app** →
Sign Up (email or Google) → dashboard → copy your **API token**.
Free-forever plan, 100 credits/day; this pipeline uses ~3 per run, so the
15-minute schedule fits comfortably. No identity forms.

**Option B — Alpha Vantage.** Go to **alphavantage.co/support/#api-key**,
enter a name + email, and the key appears on screen instantly.
Free tier is 25 calls/day and its options data is previous-close, so if you
use ONLY this key, change the cron to hourly:  `0 13-21 * * 1-5`.

*(Prices themselves come from keyless sources — the key is only spent on
implied volatility. You can even run with no key at all: everything works
except the IV auto-fill, which you'd type from the IBKR chain header.)*

### Step 2 — Create the GitHub repository (~3 min)
1. Sign in / sign up at **github.com** → **New repository**.
2. Name it anything (e.g. `opt-translator`). Must be **Public**
   (GitHub Pages is only free on public repos — the app contains no
   credentials, and market.js is just public prices; pick an obscure name
   if you prefer).
3. Create it empty, then **Add file → Upload files** and drag in:
   `index.html`, `fetch_market_cloud.py`, `market.js`.
4. The workflow file must be added with its exact path. Easiest way:
   **Add file → Create new file**, type the name
   `.github/workflows/market-data.yml`
   (typing the `/` creates the folders), then paste the file's contents
   from this bundle and commit.
   *(If you push with git instead: a Personal Access Token needs the
   `workflow` permission to push workflow files.)*

### Step 3 — Add the token as a secret (~1 min)
Repo → **Settings → Secrets and variables → Actions → New repository secret**
- Name: `MARKETDATA_TOKEN` (or `ALPHAVANTAGE_KEY` if you chose Option B)
- Value: the token/key from Step 1.
- You can add both; the fetcher prefers MarketData and falls back to
  Alpha Vantage automatically.

### Step 4 — First run (~2 min)
1. Repo → **Actions** tab → enable workflows if prompted.
2. Click **market data** → **Run workflow** (manual trigger).
3. Green check ≈ 30 s later → `market.js` in the repo now has fresh data
   (open it to verify). Red run → click into it; almost always a
   missing/typoed secret.

### Step 5 — Turn on the website (~2 min)
Repo → **Settings → Pages** → Source: **Deploy from a branch** →
Branch: `main`, folder `/ (root)` → Save.
~1 minute later your app is live at:

```
https://<your-username>.github.io/<repo-name>/
```

Open it on your phone, tap **⟳ Fill from market data** — it pulls the
freshest committed data (no page reload needed). Add to home screen and
it behaves like an app.

---

## Daily use
1. Do your analysis on TradingView as always.
2. Open the app URL anywhere → pick instrument (GLD / GLDM / IBIT) →
   **Fill from market data** → enter target, invalidation, timeline,
   confidence, risk → **Translate**.
3. Shortlist 1–2 candidates → check their real asks in IBKR → paste into
   the card → decide → order + GTC take-profit in IBKR.
4. **Log this setup** on the card you took; record the outcome when it
   resolves. Use **Export JSON** to move the log between phone/desktop
   (it lives in each browser's local storage).

## Tuning
- **IV expiry distance**: edit `IV_DAYS: '12'` in the workflow (e.g. `20`
  if your buffered expiries usually sit ~3 weeks out).
- **Schedule**: the cron `*/15 13-21 * * 1-5` covers US market hours yearly
  (EST & EDT). Add a sparse weekend line for BTC spot if you want, e.g.
  `0 6,18 * * 0,6`.
- **Data freshness**: MarketData's free tier is delayed ~15 min;
  Alpha Vantage options are previous close. Both are fine for shortlisting —
  the execution price is always the live ask you check in IBKR.
- **Resilience**: if a source fails on a run, the previous good value is
  kept (the run log shows "kept previous"), so the app never goes blank.

## Good to know
- **Stays alive by itself**: GitHub pauses schedules after 60 days of repo
  inactivity — but the bot's own commits count as activity, so it never
  pauses while it's working.
- **Costs**: $0. Actions minutes are unlimited on public repos; Pages is
  free; ~4 commits/hour is far under every limit.
- **Data age**: the app shows "fetched N min ago" and warns when stale
  (outside market hours the last close is expected and correct).
- **If a keyless XAU/BTC source ever dies**: the fetcher tries three
  sources for each; if all fail, the field arrives empty and you type it
  from TradingView — nothing else breaks.
- **Security**: the Tradier token grants market-data access only (sandbox
  has no money in it) and lives encrypted in GitHub Secrets, never in the
  repo files.
