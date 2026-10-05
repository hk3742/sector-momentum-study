"""
Sector momentum signal + long/short backtest.

Signal (fixed in advance, matching the README — not tuned on this data):
    At the point where we decide what to hold during month t, use each
    sector's cumulative return over the 6-month window ending at month
    t-2 (i.e. skip month t-1, the most recently completed month). The
    skip isn't about lookahead — month t-1's return is fully known before
    month t starts either way — it's the standard "6-1" construction from
    the industry-momentum literature, used to keep short-term reversal
    out of a signal that's supposed to capture medium-term persistence.

Portfolio: each month, equal-weight long the top 3 sectors by that
signal and equal-weight short the bottom 3, of the 9 original sector
SPDRs. Hold one month, then re-rank.

This script only builds the return series. Significance testing
(block bootstrap), cost sensitivity, and baselines are reported here
at a glance but the rigorous version is stats.py (next step).

Usage:
    python src/backtest.py
Reads:
    data/monthly_returns.csv   (from data.py)
Writes:
    data/backtest_results.csv  monthly long/short, SPY, and equal-weight returns
"""

from pathlib import Path

import numpy as np
import pandas as pd

from data import SECTOR_TICKERS, BENCHMARK

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

FORMATION_MONTHS = 6   # trailing window length
SKIP_MONTHS = 1        # most recent completed month excluded from the window
N_LEGS = 3              # sectors per side (top 3 long, bottom 3 short, of 9)


def drop_incomplete_current_month(monthly_returns: pd.DataFrame) -> pd.DataFrame:
    """The most recent row is a partial month if today falls inside it."""
    today = pd.Timestamp.today()
    last = monthly_returns.index[-1]
    if (last.year, last.month) == (today.year, today.month):
        return monthly_returns.iloc[:-1]
    return monthly_returns


def compute_signal(sector_returns: pd.DataFrame) -> pd.DataFrame:
    """6-month trailing cumulative return, skipping the most recent month.

    rolling(6) at row t covers rows [t-5, t]; shifting by SKIP_MONTHS+1=2
    moves that same 6-month window so it lands on row t but covers
    [t-7, t-2] — a 6-month formation window ending 2 months before t,
    i.e. 1 month skipped between the window and month t itself.
    """
    cumulative = (1.0 + sector_returns).rolling(FORMATION_MONTHS).apply(
        lambda w: np.prod(w) - 1.0, raw=True
    )
    return cumulative.shift(SKIP_MONTHS + 1)


def build_long_short_returns(
    sector_returns: pd.DataFrame, signal: pd.DataFrame
) -> pd.DataFrame:
    """For each month with a complete signal, rank sectors and compute the
    equal-weighted long-top-3/short-bottom-3 spread return."""
    records = []
    for date in sector_returns.index:
        sig_row = signal.loc[date]
        if sig_row.isna().any():
            continue  # burn-in period, not enough trailing history yet
        ranked = sig_row.sort_values(ascending=False)
        longs = ranked.index[:N_LEGS]
        shorts = ranked.index[-N_LEGS:]
        realized = sector_returns.loc[date]
        long_ret = realized[longs].mean()
        short_ret = realized[shorts].mean()
        records.append(
            {
                "date": date,
                "long_short_return": long_ret - short_ret,
                "long_leg": ",".join(longs),
                "short_leg": ",".join(shorts),
            }
        )
    return pd.DataFrame(records).set_index("date")


def summarize(label: str, monthly_returns: pd.Series) -> None:
    n = len(monthly_returns)
    mean_m = monthly_returns.mean()
    ann = (1 + mean_m) ** 12 - 1
    vol_ann = monthly_returns.std() * np.sqrt(12)
    cum = (1 + monthly_returns).prod() - 1
    print(
        f"{label:22s} n={n:4d}  mean/mo={mean_m:+.3%}  "
        f"ann.={ann:+.2%}  ann.vol={vol_ann:.2%}  total={cum:+.1%}"
    )


def main() -> None:
    monthly_returns = pd.read_csv(
        DATA_DIR / "monthly_returns.csv", index_col=0, parse_dates=True
    )
    monthly_returns = drop_incomplete_current_month(monthly_returns)
    monthly_returns = monthly_returns.dropna(how="any")  # drop first (NaN) row

    sector_returns = monthly_returns[SECTOR_TICKERS]
    signal = compute_signal(sector_returns)

    long_short = build_long_short_returns(sector_returns, signal)

    results = long_short.join(
        monthly_returns[[BENCHMARK]].rename(columns={BENCHMARK: "spy_return"})
    )
    results["equal_weight_return"] = sector_returns.loc[results.index].mean(axis=1)
    results = results[
        ["long_short_return", "spy_return", "equal_weight_return", "long_leg", "short_leg"]
    ]

    results.to_csv(DATA_DIR / "backtest_results.csv")

    print(f"Usable months: {len(results)} "
          f"({results.index.min().date()} -> {results.index.max().date()})\n")
    summarize("Long/short (gross)", results["long_short_return"])
    summarize("Buy & hold SPY", results["spy_return"])
    summarize("Equal-weight 9 sectors", results["equal_weight_return"])
    print(f"\nSaved: {DATA_DIR / 'backtest_results.csv'}")
    print(
        "\nNote: these are gross-of-cost, point-estimate numbers only. "
        "Significance (block bootstrap) and cost sensitivity come next in stats.py "
        "— do not treat the numbers above as a finding yet."
    )


if __name__ == "__main__":
    main()
