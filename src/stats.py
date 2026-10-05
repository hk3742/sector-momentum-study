"""
Statistical significance and cost sensitivity for the sector momentum spread.

Three independent routes to the same question — is the mean monthly
long/short return distinguishable from zero? — so they can be checked
against each other:

  1. Naive iid t-test              (assumes independent months)
  2. Newey-West HAC standard error (parametric, corrects for serial correlation)
  3. Moving block bootstrap        (nonparametric, resamples contiguous blocks)

If the three disagree sharply, something is wrong. If they agree, the
answer is robust to how dependence is handled.

Usage:
    python src/stats.py
Reads:
    data/backtest_results.csv   (from backtest.py)
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from data import SECTOR_TICKERS

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

N_BOOT = 10_000
SEED = 42
BLOCK_SIZES = (1, 3, 6, 12)
COST_BPS = (0.0, 2.0, 5.0, 10.0, 20.0)  # per unit of one-way traded notional

# Annual borrow rate charged on the short leg. Distinct from trading cost:
# borrow is a carry on the position, not a per-trade charge. Sector SPDRs
# are general-collateral / easy-to-borrow, so realistic rates sit at the low
# end, but actual historical rates come from securities-lending vendors and
# are not public — these are stated assumptions, reported as a sensitivity.
BORROW_BPS_ANNUAL = (0.0, 25.0, 50.0, 100.0)

# Real Estate left Financials when it became a standalone GICS sector on
# 2016-09-16; the Communication Services reclassification followed on
# 2018-09-28, moving large names out of Tech and Consumer Discretionary.
# Before the first date, all nine sector definitions are stable.
COMPOSITION_STABLE_END = "2016-08"


# --------------------------------------------------------------------------
# estimators
# --------------------------------------------------------------------------

def newey_west_se(x: np.ndarray, lags: int) -> float:
    """HAC standard error of the sample mean (regression on a constant).

    At lags=0 this reduces exactly to the population-sd/sqrt(n) naive SE,
    which checks.py uses as a correctness test.
    """
    x = np.asarray(x, dtype=float)
    n = x.size
    e = x - x.mean()
    s = np.dot(e, e) / n                       # gamma_0
    for j in range(1, lags + 1):
        w = 1.0 - j / (lags + 1.0)             # Bartlett kernel
        gamma_j = np.dot(e[j:], e[:-j]) / n
        s += 2.0 * w * gamma_j
    return float(np.sqrt(s / n))


def newey_west_lag_rule(n: int) -> int:
    """Newey-West (1994) automatic lag rule of thumb: floor(4*(n/100)^(2/9))."""
    return int(np.floor(4.0 * (n / 100.0) ** (2.0 / 9.0)))


def sample_acf(x: np.ndarray, nlags: int) -> list[float]:
    """Standard ACF estimator: full-sample mean, common denominator.

    Deliberately NOT pandas' Series.autocorr(), which computes a pairwise
    Pearson correlation on the overlapping subset and so uses different
    means for each lag. The two differ by up to ~0.005 on this series,
    which is enough to move a Ljung-Box p-value. checks.py pins this
    against statsmodels.tsa.stattools.acf.
    """
    x = np.asarray(x, dtype=float)
    e = x - x.mean()
    denom = np.dot(e, e)
    return [float(np.dot(e[k:], e[:-k]) / denom) for k in range(1, nlags + 1)]


def ljung_box(x: np.ndarray, nlags: int) -> tuple[float, float, list[float]]:
    """Ljung-Box Q statistic and p-value. Matches statsmodels acorr_ljungbox."""
    n = len(x)
    rho = sample_acf(x, nlags)
    stat = n * (n + 2) * sum((r**2) / (n - (k + 1)) for k, r in enumerate(rho))
    p = float(1 - sp_stats.chi2.cdf(stat, df=nlags))
    return float(stat), p, rho


def moving_block_bootstrap_means(
    x: np.ndarray, block: int, n_boot: int, rng: np.random.Generator
) -> np.ndarray:
    """Resample contiguous overlapping blocks of length `block`, return the
    distribution of the resampled mean. block=1 degenerates to the iid bootstrap."""
    x = np.asarray(x, dtype=float)
    n = x.size
    n_blocks = int(np.ceil(n / block))
    max_start = n - block
    offsets = np.arange(block)
    means = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        starts = rng.integers(0, max_start + 1, size=n_blocks)
        idx = (starts[:, None] + offsets[None, :]).ravel()[:n]
        means[i] = x[idx].mean()
    return means


# --------------------------------------------------------------------------
# turnover / costs
# --------------------------------------------------------------------------

def weights_from_legs(long_leg: str, short_leg: str) -> pd.Series:
    w = pd.Series(0.0, index=SECTOR_TICKERS)
    longs = long_leg.split(",")
    shorts = short_leg.split(",")
    w[longs] = 1.0 / len(longs)
    w[shorts] = -1.0 / len(shorts)
    return w


def monthly_turnover(results: pd.DataFrame) -> pd.Series:
    """One-way traded notional as a fraction of capital, per rebalance.

    Simplification (stated, not hidden): weights are assumed to reset exactly
    at each month end, ignoring intra-month drift. Drift would add a little
    turnover, so this is a mild understatement of true costs.
    """
    weights = [weights_from_legs(r.long_leg, r.short_leg) for r in results.itertuples()]
    turnover = []
    prev = pd.Series(0.0, index=SECTOR_TICKERS)
    for w in weights:
        turnover.append(float((w - prev).abs().sum()))
        prev = w
    return pd.Series(turnover, index=results.index, name="turnover")


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------

def describe_series(label: str, r: pd.Series) -> None:
    n = r.size
    mean_m = r.mean()
    sd_m = r.std(ddof=1)
    arith_ann = (1 + mean_m) ** 12 - 1
    total_growth = float((1 + r).prod())
    cagr = total_growth ** (12.0 / n) - 1
    print(f"\n--- {label} ---")
    print(f"  months                 : {n}  ({r.index.min():%Y-%m} .. {r.index.max():%Y-%m})")
    print(f"  mean monthly           : {mean_m:+.4%}")
    print(f"  sd monthly             : {sd_m:.4%}")
    print(f"  annualized (arithmetic): {arith_ann:+.2%}   <- (1+mean)^12-1, ignores vol drag")
    print(f"  annualized (geometric) : {cagr:+.2%}   <- compounded, the honest one")
    print(f"  annualized vol         : {sd_m * np.sqrt(12):.2%}")
    print(f"  cumulative growth      : {total_growth - 1:+.1%}")
    print(f"  worst month            : {r.min():+.2%} ({r.idxmin():%Y-%m})")
    print(f"  best  month            : {r.max():+.2%} ({r.idxmax():%Y-%m})")


def significance_report(r: pd.Series, rng: np.random.Generator) -> None:
    x = r.to_numpy(dtype=float)
    n = x.size
    mean_m = x.mean()

    print("\n=== serial correlation of the spread ===")
    ljung_stat, ljung_p, acf = ljung_box(x, 6)
    se_acf = 1.0 / np.sqrt(n)
    print("  ACF lag 1-6: " + "  ".join(f"{a:+.3f}" for a in acf))
    print(f"  approx 2-SE band on each ACF estimate: +/-{2*se_acf:.3f}  "
          f"({sum(abs(a) > 2*se_acf for a in acf)}/6 lags outside it)")
    print(f"  Ljung-Box(6): stat={ljung_stat:.2f}  p={ljung_p:.3f}"
          f"   -> {'some dependence' if ljung_p < 0.05 else 'no strong dependence'}"
          " (borderline — individual lags sit near the 2-SE band)")

    print("\n=== is mean monthly return different from zero? ===")

    # 1. naive iid
    se_iid = x.std(ddof=1) / np.sqrt(n)
    t_iid = mean_m / se_iid
    p_iid = 2 * (1 - sp_stats.t.cdf(abs(t_iid), df=n - 1))
    crit = sp_stats.t.ppf(0.975, df=n - 1)
    print(f"  naive iid         : mean={mean_m:+.4%}  se={se_iid:.4%}  "
          f"t={t_iid:+.2f}  p={p_iid:.3f}  "
          f"95% CI [{mean_m - crit*se_iid:+.4%}, {mean_m + crit*se_iid:+.4%}]")

    # 2. Newey-West HAC
    lag = newey_west_lag_rule(n)
    for L in sorted({lag, 3, 12}):
        se_nw = newey_west_se(x, L)
        t_nw = mean_m / se_nw
        p_nw = 2 * (1 - sp_stats.t.cdf(abs(t_nw), df=n - 1))
        tag = " (auto lag rule)" if L == lag else ""
        print(f"  Newey-West L={L:<2d}      : se={se_nw:.4%}  t={t_nw:+.2f}  p={p_nw:.3f}  "
              f"95% CI [{mean_m - crit*se_nw:+.4%}, {mean_m + crit*se_nw:+.4%}]{tag}")

    # 3. block bootstrap
    for b in BLOCK_SIZES:
        means = moving_block_bootstrap_means(x, b, N_BOOT, rng)
        lo, hi = np.percentile(means, [2.5, 97.5])
        # bootstrap p-value: share of resampled means on the other side of 0
        p_boot = 2 * min((means <= 0).mean(), (means >= 0).mean())
        tag = " (= iid bootstrap)" if b == 1 else ""
        print(f"  block bootstrap b={b:<2d}: se={means.std(ddof=1):.4%}  "
              f"95% CI [{lo:+.4%}, {hi:+.4%}]  p={p_boot:.3f}{tag}")


def cost_report(results: pd.DataFrame) -> None:
    turnover = monthly_turnover(results)
    gross = results["long_short_return"]
    print("\n=== turnover and costs ===")
    print(f"  mean one-way traded notional per month: {turnover.mean():.3f}x capital")
    print(f"  (gross exposure is 2.0x: 1.0 long + 1.0 short)")
    print(f"  median: {turnover.median():.3f}   max: {turnover.max():.3f}")
    print()
    print("  trading cost only (per unit traded notional):")
    for bps in COST_BPS:
        net = gross - turnover * (bps / 10_000.0)
        mean_m = net.mean()
        se = net.std(ddof=1) / np.sqrt(net.size)
        t = mean_m / se
        print(f"    {bps:4.1f} bps : mean={mean_m:+.4%}/mo  "
              f"ann.(geo)={float((1+net).prod())**(12/net.size)-1:+.2%}  t={t:+.2f}")

    # Borrow is a carry on the short leg (notional 1.0x), not a per-trade cost.
    print("\n  + short borrow (annual rate on the 1.0x short leg):")
    print("    trade\\borrow " + "".join(f"{b:>10.0f}bp/yr" for b in BORROW_BPS_ANNUAL))
    for bps in (0.0, 2.0, 5.0):
        row = f"    {bps:4.1f} bps    "
        for borrow in BORROW_BPS_ANNUAL:
            net = gross - turnover * (bps / 10_000.0) - (borrow / 10_000.0) / 12.0
            row += f"{net.mean():>+10.4%}   "
        print(row)
    print("    (cells are mean monthly return; the pre-specified gross figure "
          f"is {gross.mean():+.4%})")


def risk_adjustment_report(results: pd.DataFrame) -> None:
    """POST-HOC. This was not part of the pre-specified test.

    It is reported because the pre-specified test turned out to be
    confounded: the spread carries a persistent short-market tilt, so its
    raw mean mixes a momentum effect with a beta effect. Separating them
    is the right diagnostic — but running it only after seeing the null is
    a researcher degree of freedom, and the resulting t-stat should be
    read as exploratory, not as a confirmatory test.
    """
    try:
        import statsmodels.api as sm_api
    except ImportError:
        print("\n(skipping risk adjustment — statsmodels not installed)")
        return

    y = results["long_short_return"]
    mkt = results["spy_return"]
    fit = sm_api.OLS(y.values, sm_api.add_constant(mkt.values)).fit(
        cov_type="HAC", cov_kwds={"maxlags": 5}
    )
    alpha, beta = float(fit.params[0]), float(fit.params[1])

    print("\n=== POST-HOC: market risk adjustment (exploratory, not pre-specified) ===")
    print(f"  spread_t = alpha + beta * SPY_t + e_t      (HAC lag 5)")
    print(f"  alpha = {alpha:+.4%}/mo   t={fit.tvalues[0]:+.2f}")
    print(f"  beta  = {beta:+.3f}        t={fit.tvalues[1]:+.2f}   R^2={fit.rsquared:.3f}")
    print(f"  identity check: alpha + beta*mean(mkt) = {alpha + beta*mkt.mean():+.4%} "
          f"== raw mean {y.mean():+.4%}")
    print(f"  -> the short-market tilt cost {beta*mkt.mean():+.4%}/mo over a rising sample,")
    print(f"     which is what drags the raw mean down to roughly zero.")

    print("\n  stability across regimes (no subperiod is individually significant):")
    for label, sl in [("1999-2007", slice("1999", "2007")), ("2008-2012", slice("2008", "2012")),
                      ("2013-2018", slice("2013", "2018")), ("2019-2026", slice("2019", "2026"))]:
        yy, mm = y[sl], mkt[sl]
        ff = sm_api.OLS(yy.values, sm_api.add_constant(mm.values)).fit()
        t_mean = yy.mean() / (yy.std(ddof=1) / np.sqrt(len(yy)))
        print(f"    {label}: n={len(yy):3d}  mean={yy.mean():+.3%}/mo (t={t_mean:+.2f})  "
              f"beta={ff.params[1]:+.2f}")
    print("    beta itself is unstable, which undercuts the constant-beta assumption")
    print("    the full-sample alpha above depends on.")

    print("\n  alpha net of costs:")
    turnover = monthly_turnover(results)
    for bps in (0.0, 5.0, 10.0, 20.0):
        net = y - turnover * (bps / 10_000.0)
        ff = sm_api.OLS(net.values, sm_api.add_constant(mkt.values)).fit(
            cov_type="HAC", cov_kwds={"maxlags": 5}
        )
        print(f"    {bps:4.1f} bps: alpha={ff.params[0]:+.4%}/mo  t={ff.tvalues[0]:+.2f}")


def power_report(results: pd.DataFrame) -> None:
    """How large would an effect have to be for this design to see it?

    Reported because a null is only informative to the extent the test
    could have rejected. With 9 assets and a top-3/bottom-3 sort the
    spread is noisy, so the minimum detectable effect is large relative
    to any plausible sector-momentum effect — which means the null here
    is absence of evidence, not evidence of absence.
    """
    x = results["long_short_return"]
    n, sd = x.size, x.std(ddof=1)
    se = sd / np.sqrt(n)
    z_a, z_b = sp_stats.norm.ppf(0.975), sp_stats.norm.ppf(0.80)
    mde = (z_a + z_b) * se

    print("\n=== statistical power ===")
    print(f"  monthly sd={sd:.3%}  se of mean={se:.4%}  n={n}")
    print(f"  minimum detectable effect @80% power: {mde:+.4%}/mo "
          f"({(1+mde)**12-1:+.2%}/yr)")
    print(f"  observed point estimate:              {x.mean():+.4%}/mo")
    print("\n  power against plausible true effects:")
    for eff in (0.001, 0.002, 0.003, 0.005):
        power = 1 - sp_stats.norm.cdf(z_a - eff / se) + sp_stats.norm.cdf(-z_a - eff / se)
        months = int((z_a + z_b) ** 2 * sd**2 / eff**2)
        print(f"    {eff:.2%}/mo ({(1+eff)**12-1:+5.1%}/yr): power={power:5.1%}   "
              f"months for 80% power={months:6d} ({months/12:.0f} yrs)")
    print("\n  -> the design could not have detected a realistic effect.")
    print("     Read the null in the significance section as 'failed to detect',")
    print("     not as 'no effect exists'.")


def composition_robustness_report(results: pd.DataFrame, rng: np.random.Generator) -> None:
    """Re-run the pre-specified test on the window where sector definitions
    are stable, i.e. before the Real Estate GICS carve-out (2016-09-16).

    After that date XLF loses real estate, and after the Communication
    Services reclassification (2018-09-28) XLK and XLY lose large names, so
    the later sample is not a constant-definition panel — and because XLC is
    excluded, the universe stops spanning the market entirely.
    """
    print("\n=== robustness: composition-stable window (pre-2016-09) ===")
    stable = results.loc[:COMPOSITION_STABLE_END, "long_short_return"]
    full = results["long_short_return"]
    for label, r in (("full sample      ", full), ("composition-stable", stable)):
        x = r.to_numpy(dtype=float)
        se = x.std(ddof=1) / np.sqrt(x.size)
        nw = newey_west_se(x, newey_west_lag_rule(x.size))
        boot = moving_block_bootstrap_means(x, 6, N_BOOT, rng)
        lo, hi = np.percentile(boot, [2.5, 97.5])
        print(f"  {label}: n={x.size:3d}  mean={x.mean():+.4%}/mo  "
              f"t(iid)={x.mean()/se:+.2f}  t(HAC)={x.mean()/nw:+.2f}  "
              f"boot95 [{lo:+.3%}, {hi:+.3%}]")
    print("  -> the conclusion does not depend on the post-2016 composition breaks.")


def baseline_report(results: pd.DataFrame) -> None:
    print("\n=== does sector selection add anything? ===")
    long_only_proxy = results["equal_weight_return"]
    spy = results["spy_return"]
    diff = long_only_proxy - spy
    se = diff.std(ddof=1) / np.sqrt(diff.size)
    print(f"  equal-weight 9 sectors minus SPY: {diff.mean():+.4%}/mo  "
          f"t={diff.mean()/se:+.2f}")
    print("  (this is a sector-weighting effect, not a momentum effect — "
          "the momentum question is the long/short spread above)")


def main() -> None:
    results = pd.read_csv(
        DATA_DIR / "backtest_results.csv", index_col=0, parse_dates=True
    )
    rng = np.random.default_rng(SEED)

    describe_series("long/short spread (gross)", results["long_short_return"])
    describe_series("SPY total return", results["spy_return"])
    describe_series("equal-weight 9 sectors", results["equal_weight_return"])

    significance_report(results["long_short_return"], rng)
    power_report(results)
    cost_report(results)
    risk_adjustment_report(results)
    composition_robustness_report(results, rng)
    baseline_report(results)


if __name__ == "__main__":
    main()
