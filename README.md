# Sector Momentum Study

Does sector relative strength persist? This tests whether the 9 original
Select Sector SPDR ETFs that outperformed over a trailing ~6-month window
continue to outperform over the following month — the classic "6-1"
industry momentum construction (6-month formation, most recent month
skipped to avoid short-term reversal).

This isn't a trading strategy pitch. The goal is a careful, honest answer
to a narrow question, with the statistical rigor to back up that answer —
specifically, a block-bootstrapped confidence interval (resampling
contiguous time blocks, not individual months, since monthly returns
within the same cross-section are correlated) rather than a single point
estimate.

## Universe

- Benchmark: `SPY`
- Sectors: `XLK XLF XLE XLV XLY XLP XLI XLU XLB` — the 9 sector SPDRs that
  launched Dec 16, 1998, giving a balanced ~27-year panel. `XLRE` (2015)
  and `XLC` (2018) are excluded on purpose — including them would
  unbalance the panel and shrink the usable sample.

## Methodology (fixed in advance, not tuned on the data)

- Monthly rebalancing.
- Formation signal: trailing 6-month return, skipping the most recent
  month.
- Each month: long the top 3 sectors by that signal, short the bottom 3,
  equal-weighted.
- One lookback, one holding period — no grid search over parameters. The
  6-month formation window is one of Jegadeesh & Titman's (1993) original
  *J* values and the 1-month skip is the standard convention for separating
  momentum from short-term reversal; neither was chosen because it looks
  good on this sample.

## Status

- [x] Data pipeline (`src/data.py`) — pulls daily adjusted close via
      `yfinance`, builds a month-end return panel.
- [x] Momentum signal + long/short backtest (`src/backtest.py`)
- [x] Significance testing + cost sensitivity (`src/stats.py`)
- [x] Validation suite (`src/checks.py`) — 31 checks
- [x] Write-up — see [WRITEUP.md](WRITEUP.md)
- [x] Visual summary — [index.html](index.html), a self-contained page
      (open it directly in a browser; no server or build step)

## Result

Over 326 months (Aug 1999 – Sep 2026) the 6-1 sector momentum spread
returned **+0.130% per month gross (t ≈ 0.6–0.7, p ≈ 0.47–0.57)**. The
null that sector momentum had no effect in this universe **cannot be
rejected** — every 95% interval comfortably contains zero:

| method | SE | 95% CI (monthly) |
|---|---|---|
| naive iid t-test | 0.225% | [−0.314%, +0.573%] |
| Newey-West (auto lag 5) | 0.180% | [−0.225%, +0.485%] |
| moving block bootstrap (b=6) | 0.181% | [−0.237%, +0.477%] |

Three independent methods agree, so the conclusion isn't an artifact of
how serial dependence was handled.

Note the HAC and block-bootstrap intervals are *narrower* than the naive
one. That is the correct behavior here, not a bug: the spread's
autocorrelation is mildly **negative** at lags 1–5, which reduces the
variance of the sample mean. The usual "clustering widens intervals"
intuition only holds for positive dependence.

Mean one-way turnover is 1.15x capital per month, so the gross edge is
roughly exhausted at **~10 bps** of round-trip trading cost, before the
short-leg borrow carry (reported as a 0–100 bp/yr sensitivity in
[WRITEUP.md](WRITEUP.md) §4). The conclusion also holds on the
composition-stable pre-2016 window, before the GICS sector
reclassifications. But the honest headline is the first one: the gross
effect is not statistically distinguishable from zero to begin with, so
the cost result is secondary.

**How much does this null tell us? Less than it looks.** A nine-asset
top-3/bottom-3 sort is coarse, so the minimum detectable effect at 80%
power is **+0.63%/mo (+7.8%/yr)** — larger than any plausible sector
momentum effect. Power against realistic effects (0.1–0.3%/mo) is only
**7–27%**. This is absence of evidence, not evidence of absence. See
[WRITEUP.md](WRITEUP.md) §5.

**One caveat that matters.** The raw mean is confounded. The spread carries
a persistent short-market tilt (beta = −0.31, t = −4.33), and a post-hoc
CAPM regression gives alpha = +0.371%/mo (t = +2.33) — nominally
significant. I do not report that as a finding: it was not pre-specified,
the beta is unstable across regimes (−0.38 to +0.01), no subperiod is
individually significant, and it decays to insignificance by ~10 bps of
cost. See [WRITEUP.md](WRITEUP.md) §6–7.

## Validation

`src/checks.py` re-derives every headline number by a second route:
hand-recomputed signal vs. `compute_signal()`, a lookahead test that
rebuilds the signal from truncated history, Newey-West pinned against
`statsmodels` HAC (and at lag 0 against the closed-form naive SE), the
block bootstrap at block=1 reproducing the iid SE, and the ACF/Ljung-Box
pinned against `statsmodels` — a check that caught a real bug, since
`pandas.Series.autocorr()` is not the standard ACF estimator.

Our data is checked against **externally published annual total returns
for all ten tickers** (44 ticker-years, max deviation 0.07pp): compounding
our monthly returns reproduces e.g. SPY 2008 at −36.79% vs −36.81%
published, XLF 2008 at −54.90%, XLE 2022 at +64.32% vs +64.25%.

The strongest single check is behavioral: the spread's worst month
(Apr 2009, −16.71%) is long defensives / short financials as financials
rallied +21.8% — the documented post-GFC momentum crash — and its best
month (Mar 2020, +13.61%) is short energy as XLE fell −34.4%. A
misaligned or sign-flipped implementation would not reproduce both.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/data.py      # fetch prices, build monthly panel
python src/backtest.py  # signal + long/short spread
python src/stats.py     # significance, costs, baselines
python src/checks.py    # validation suite (exits nonzero on failure)
```

`data.py` outputs `data/raw_prices.csv` and `data/monthly_returns.csv`.
`backtest.py` reads those and outputs `data/backtest_results.csv`. All
gitignored — regenerate on demand rather than committing fetched/derived
data.

## Known data caveat

The most recent month in `monthly_returns.csv` is partial (today's date
falls mid-month) — `backtest.py` already drops it rather than treating it
as a completed month.
