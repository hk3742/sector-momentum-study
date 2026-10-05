"""
Data pipeline: pull daily adjusted-close prices for SPY and the 9 original
Select Sector SPDR ETFs, then build a monthly return panel.

The 9 "classic" sector SPDRs (XLK, XLF, XLE, XLV, XLY, XLP, XLI, XLU, XLB)
all launched Dec 16, 1998, so they share a long, balanced history. XLRE
(2015) and XLC (2018) are deliberately excluded — including them would
unbalance the panel and shrink the usable sample.

Usage:
    python src/data.py
Outputs (gitignored, regenerate on demand):
    data/raw_prices.csv       daily adjusted close, one column per ticker
    data/monthly_returns.csv  month-end simple returns, one column per ticker
"""

from pathlib import Path

import pandas as pd
import yfinance as yf

BENCHMARK = "SPY"
SECTOR_TICKERS = ["XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLU", "XLB"]
ALL_TICKERS = [BENCHMARK] + SECTOR_TICKERS

START = "1998-12-01"  # just before the sector SPDRs' Dec 16, 1998 inception
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def fetch_daily_prices(tickers: list[str], start: str) -> pd.DataFrame:
    """Download daily adjusted close for each ticker, aligned into one wide frame."""
    raw = yf.download(tickers, start=start, auto_adjust=True, progress=False)
    prices = raw["Close"].copy()
    prices = prices[tickers]  # fixed column order
    prices.index.name = "date"
    return prices


def to_monthly_returns(daily_prices: pd.DataFrame) -> pd.DataFrame:
    """Month-end simple returns from daily adjusted close."""
    monthly_prices = daily_prices.resample("ME").last()
    monthly_returns = monthly_prices.pct_change()
    return monthly_returns


def sanity_report(daily_prices: pd.DataFrame, monthly_returns: pd.DataFrame) -> None:
    print("\n=== daily price coverage ===")
    for col in daily_prices.columns:
        s = daily_prices[col].dropna()
        print(f"{col:5s}  {s.index.min().date()} -> {s.index.max().date()}  "
              f"({len(s)} obs, {daily_prices[col].isna().sum()} NaN)")

    print("\n=== monthly return panel ===")
    print(f"shape: {monthly_returns.shape}")
    print(f"first usable (all tickers non-NaN) month: "
          f"{monthly_returns.dropna().index.min().date()}")
    print(f"last month: {monthly_returns.index.max().date()}")
    na_counts = monthly_returns.isna().sum()
    if na_counts.sum():
        print(f"NaN months per ticker:\n{na_counts}")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Fetching {len(ALL_TICKERS)} tickers from {START}...")
    daily = fetch_daily_prices(ALL_TICKERS, START)

    monthly = to_monthly_returns(daily)

    daily.to_csv(DATA_DIR / "raw_prices.csv")
    monthly.to_csv(DATA_DIR / "monthly_returns.csv")

    sanity_report(daily, monthly)
    print(f"\nSaved: {DATA_DIR / 'raw_prices.csv'}")
    print(f"Saved: {DATA_DIR / 'monthly_returns.csv'}")


if __name__ == "__main__":
    main()
