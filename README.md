# Options Scenario Planner (GLD / IBIT) — Zero-PC Cloud Setup

Your app hosted free on **GitHub Pages**, with market data (GLD / IBIT
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
| `index.html` | The planner app (single page, no build step) |
| `fetch_market_cloud.py` | The fetcher that Actions runs |
| `.github/workflows/market-data.yml` | The schedule + commit automation |
| `market.js` | Seed data file (gets overwritten by the bot) |
| `tools/` | Optional local fetchers (IBKR gateway / Yahoo) — not used in the cloud |

## How the app works

Three steps, then results:

1. **Market** — pick Bitcoin (IBIT options) or Gold (GLD options), press **Fill from market data** (or type the ETF price, your chart price and the IV from the top of IBKR's option chain).
2. **Your trade** — direction, **entry level** (today's price or a future level you are waiting for), stop, target, days to reach the target, entry date, risk budget. Advanced: rate, commission, expiry buffer, a volatility shift for the projections, and which position types to show.
3. **Results**
   - a plain-words card: what to buy, what you pay, the most you can lose, the profit at your target, the cap, and why it was chosen;
   - **Positions compared**: up to four vertical debit spreads and two single options, ranked by **R** (profit at your target on expiry day ÷ max loss); click a row to make it the plan;
   - **What happens at each price and date**: stop, entry, break-even, target and past-target rows against at-entry, two weeks before expiry, one week before, and expiry day;
   - **Profit and loss by price**: one line per date, hover for exact figures, table view;
   - **Do this on Interactive Brokers**: the legs, quantity and limit for Strategy Builder, a copy line, and the exit plan (close the day before expiry).

| | Single option | Vertical spread |
|---|---|---|
| What you do | Buy one call or put | Buy one near your entry **and sell one near your target** |
| Cost (= max loss) | The whole premium | Premium bought minus premium sold |
| Break-even | Far: the whole premium must be earned back | Nearer: the sold leg paid for part of it |
| Profit | Uncapped | Stops at the sold strike |
| Best when | You expect a move much bigger than your target | You expect roughly your target |

**Accuracy.** This site cannot reach IBKR, so costs are Black–Scholes estimates at the IV you enter, on the strike and expiry pattern IBKR lists (IBIT: Fridays; GLD: Mon/Wed/Fri; plus monthlies). Paste IBKR's real net debit (or ask, for a single option) into the box on the plan card and the whole plan recomputes from that price. Projections before expiry use the same volatility; expiry-day values are exact. The claude.ai version of this planner reads live IBKR bid/ask and each option's own IV through your IBKR connector and can send the order to IBKR for review.

**Setup log & calibration** at the bottom records each plan you take (**Log this setup** on the plan card) and the outcome you enter later, so you can see your hit rate by confidence and how your time estimates compare with reality. It lives in the browser; use Export/Import to move it between devices.

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
2. Open the app URL anywhere → pick instrument (IBIT / GLD) →
   **Fill from market data** → enter entry, stop, target, days, risk →
   **Build my plan**.
3. Read the plan card and the price-by-date table → check the real net
   debit in IBKR's Strategy Builder → paste it into the plan card →
   decide → place the order in IBKR, then set the closing order for the
   day before expiry.
4. **Log this setup** on the plan card; record the outcome when it
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
