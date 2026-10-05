# Does sector relative strength persist?

A pre-specified test of 6-1 momentum across the nine original Select Sector
SPDR ETFs, August 1999 – September 2026 (326 months).

**Headline: the pre-specified test does not reject the null.** The raw
long/short spread averages +0.130%/month with t ≈ 0.6–0.7; every 95%
interval comfortably contains zero. A post-hoc risk adjustment turns up a
nominally significant alpha, but it does not survive the scrutiny I would
want before believing it, and the reasons are set out below.

**The null is weaker evidence than it looks.** A nine-asset top-3/bottom-3
sort is a coarse instrument: the design had only ~7–27% power against the
range of effect sizes that are actually plausible for sector momentum
(§5). This is *absence of evidence, not evidence of absence*, and the
distinction is the most important thing in this document.

---

## 1. Question

If a sector has outperformed its peers over the past several months, does
it keep outperforming next month? Sector/industry momentum is a documented
effect in the academic literature, with the usual economic story being slow
diffusion of information and slow rotation of institutional capital. The
question here is narrower than "is momentum real": it is whether the effect
shows up in *this* liquid, tradable universe over *this* sample, and
whether it is large enough to matter after costs.

## 2. Data and universe

| | |
|---|---|
| Sectors | XLK, XLF, XLE, XLV, XLY, XLP, XLI, XLU, XLB |
| Benchmark | SPY |
| Source | Yahoo Finance via `yfinance`, dividend-adjusted close |
| Sample | Aug 1999 – Sep 2026, 326 monthly observations |

All nine sector SPDRs launched 16 Dec 1998, so the panel is balanced.
XLRE and XLC are excluded deliberately: they began trading in Oct 2015 and
Jun 2018 respectively, and including them would unbalance the panel and
truncate the usable sample by two decades.

## 3. Method (fixed before looking at results)

- **Signal.** Cumulative return over the 6-month window ending two months
  before the holding month. The 6-month formation window is one of the
  original *J* values in Jegadeesh & Titman (1993), whose strategies ranked
  on returns over the past *J* months and held for *K* months with *J, K* ∈
  {3, 6, 9, 12}. Skipping the most recent month follows the standard
  convention for separating momentum from short-term reversal — the same
  convention behind the Fama–French momentum factor's 12-2 construction.
  The skip is *not* a lookahead fix; month *t−1* is already known before
  month *t* begins.
- **Portfolio.** Each month, equal-weight long the top 3 sectors by signal,
  equal-weight short the bottom 3. Hold one month, re-rank, repeat.
- **One parameterisation only.** No grid search over lookbacks, holding
  periods, or leg sizes. Searching would have made any resulting t-stat
  uninterpretable.

## 4. Primary result

Gross of costs, over 326 months:

| | mean/mo | ann. (geometric) | ann. vol |
|---|---|---|---|
| **Long/short spread** | **+0.130%** | **+0.55%** | 14.1% |
| Buy & hold SPY | +0.780% | +8.53% | 15.1% |
| Equal-weight 9 sectors | +0.794% | +8.78% | 14.6% |

Three routes to the same question, so the answer does not depend on how
serial dependence is handled:

| method | SE | t | 95% CI (monthly) |
|---|---|---|---|
| naive iid t-test | 0.225% | +0.58 | [−0.314%, +0.573%] |
| Newey–West, auto lag 5 | 0.180% | +0.72 | [−0.225%, +0.485%] |
| moving block bootstrap, b=6 | 0.181% | — | [−0.237%, +0.477%] |

All three contain zero. **The null that 6-1 sector momentum had no effect
in this universe cannot be rejected.**

Two details worth stating because they look wrong at first glance:

- The HAC and bootstrap intervals are *narrower* than the naive one. That
  is correct, not a bug. The spread's autocorrelation is mildly **negative**
  at lags 1–5, which reduces the variance of the sample mean. The familiar
  "dependence widens your interval" intuition only holds for positive
  dependence.
- Ljung–Box(6) returns p = 0.020, nominally rejecting independence. I would
  not lean on it. With n = 326 the standard error on each ACF estimate is
  ≈ 0.055, and the individual lags (−0.12 at lag 2, −0.11 at lag 4) sit
  right at the two-SE band.

**Costs.** Mean one-way traded notional is 1.15× capital per month, so the
gross edge is exhausted at roughly **10 bps** of round-trip trading cost.
Borrow on the short leg is a separate charge — a carry on the position, not
a per-trade cost — and is reported as a sensitivity because historical
borrow rates come from securities-lending vendors and are not public.
Sector SPDRs are general-collateral/easy-to-borrow, so realistic rates sit
at the low end of this grid:

| trading \ borrow | 0 bp/yr | 25 bp/yr | 50 bp/yr | 100 bp/yr |
|---|---|---|---|---|
| **0 bps** | +0.130% | +0.109% | +0.088% | +0.046% |
| **2 bps** | +0.107% | +0.086% | +0.065% | +0.023% |
| **5 bps** | +0.072% | +0.051% | +0.030% | −0.011% |

(mean monthly return). All of this is secondary: the gross effect is not
distinguishable from zero to begin with, so costs are a footnote rather
than the finding.

**Composition robustness.** Sector definitions are not constant across the
sample — Real Estate left Financials when it became a standalone GICS
sector (16 Sep 2016), and the Communication Services reclassification
(28 Sep 2018) moved large names out of Tech and Consumer Discretionary.
Restricting to the window where all nine definitions are stable does not
change the answer:

| | n | mean/mo | t (iid) | t (HAC) | bootstrap 95% |
|---|---|---|---|---|---|
| full sample | 326 | +0.130% | +0.58 | +0.72 | [−0.233%, +0.474%] |
| pre-2016-09 | 205 | +0.165% | +0.56 | +0.70 | [−0.278%, +0.617%] |

## 5. How much does the null actually tell us?

Very little, and this deserves to be said plainly. A null is only
informative to the extent the test could have rejected. With nine assets
and a top-3/bottom-3 sort, the spread's monthly standard deviation is
4.07%, so the standard error on the mean is 0.225%/month. That implies:

**Minimum detectable effect at 80% power: +0.63%/month = +7.8%/year.**

| true effect | power to detect it | months needed for 80% power |
|---|---|---|
| 0.10%/mo (+1.2%/yr) | 7.3% | 12,977 (1,081 yrs) |
| 0.20%/mo (+2.4%/yr) | 14.4% | 3,244 (270 yrs) |
| 0.30%/mo (+3.7%/yr) | 26.6% | 1,441 (120 yrs) |
| 0.50%/mo (+6.2%/yr) | 60.3% | 519 (43 yrs) |

For context, classic stock-level momentum on extreme deciles of thousands
of names ran on the order of 1%/month in its original samples. A nine-asset
sector sort cannot produce spreads that extreme — the "winners" and
"losers" are far closer to the middle of the distribution — so the
plausible effect size here is a fraction of that, squarely in the region
where this test has 7–27% power.

**The null was therefore substantially determined by the design, not
discovered from the market.** The 95% interval [−0.31%, +0.57%] comfortably
contains +0.5%/month, an effect anyone would happily trade. Nothing in §4
rules that out.

Three reasons a null was the expected outcome regardless, in increasing
order of importance:

1. *Post-publication decay.* The sample begins Aug 1999 — after Jegadeesh
   & Titman (1993) and contemporaneous with the industry-momentum
   literature. Anomaly returns are known to attenuate once published.
2. *Arbitrage.* Sector SPDRs are among the most liquid and most-watched
   instruments in existence, and this is a monthly sort on public price
   data. It is close to the least likely place for a simple edge to
   survive.
3. *Power.* The above.

## 6. Post-hoc: the raw mean is confounded

The pre-specified test turned out to measure the wrong thing. Regressing
the spread on SPY (HAC, lag 5):

```
spread_t = alpha + beta * SPY_t + e_t

alpha = +0.371%/mo   t = +2.33
beta  = -0.309       t = -4.33      R^2 = 0.110
```

The decomposition is exact: `0.371% + (−0.309 × 0.780%) = 0.130%`, the raw
mean, to within 1e-18. The spread carries a persistent **short-market
tilt** — momentum is long defensives and short cyclicals more often than
the reverse — and over a sample where the market compounded at 8.5%/yr that
tilt cost about 0.24%/month. That is what drags the raw mean to roughly
zero.

So the honest statement is: *the raw spread is flat, and that flatness is
the sum of a positive residual and a negative beta contribution.*

## 7. Why I do not believe the alpha yet

A +2.33 t-stat is the kind of number it is tempting to lead with. Four
reasons not to:

1. **It was not pre-specified.** I ran this regression only after seeing
   the null. That is a researcher degree of freedom, and I cannot honestly
   multiple-test-correct it because I cannot enumerate how many
   alternatives I would have tried had this one also come back flat.
2. **Beta is unstable, and the model assumes it is constant.** By regime:
   −0.32, −0.38, **+0.01**, −0.35. A constant-beta regression is the wrong
   specification for a series whose beta visibly moves, which makes the
   full-sample alpha estimate less trustworthy than its t-stat suggests.
3. **No subperiod is individually significant, and the signs flip.**

   | period | n | mean/mo | t | beta |
   |---|---|---|---|---|
   | 1999–2007 | 101 | +0.414% | +0.98 | −0.32 |
   | 2008–2012 | 60 | −0.267% | −0.42 | −0.38 |
   | 2013–2018 | 72 | +0.403% | +1.27 | +0.01 |
   | 2019–2026 | 93 | −0.135% | −0.31 | −0.35 |

4. **It decays quickly under costs.** At 5 bps alpha is +0.313% (t = 1.96),
   right on the boundary; at 10 bps it is +0.256% (t = 1.60) and no longer
   significant at conventional levels — before adding the short borrow
   carry in §4, which pushes it down further.

A defensible summary: there is a *hint* of a risk-adjusted effect that is
worth a proper, pre-registered test on an independent sample. It is not a
finding.

## 8. Validation

A null is only worth reporting if the pipeline is right, so every headline
number is re-derived by a second route (`src/checks.py`, 31 checks).

**Against reference implementations.** The hand-rolled Newey–West SE matches
`statsmodels` HAC to 7e-16 at every lag tested. This process caught a real
bug: the Ljung–Box test was originally built on `pandas.Series.autocorr()`,
which computes a pairwise Pearson correlation over the overlapping subset
rather than the standard ACF estimator. The two differ by up to 0.005 here
— enough to move the statistic from 15.67 (p = 0.0156) to the correct
15.03 (p = 0.0200). `sample_acf()` now matches `statsmodels` exactly.

**Against published returns.** Compounding our monthly returns reproduces
externally published annual total returns for **all ten tickers** — 44
ticker-years in total, max deviation **0.07pp**, most under 0.01pp. SPY is
checked across 6 years (2008: ours −36.79% vs −36.81% published), XLK
across 10, and each of the other eight sectors across 2–4 years spanning
2008, 2013, 2020 and 2022. This jointly rules out wrong ticker,
price-vs-total-return confusion, bad dividend adjustment, and
month-boundary misalignment across the entire universe, not just the
benchmark.

**Against market history.** The strongest check is behavioral. The spread's
worst month (Apr 2009, −16.71%) is long defensives / short financials as
financials rallied +21.8% in the junk rally off the March 2009 low — the
documented post-GFC momentum crash. Its best month (Mar 2020, +13.61%) is
short energy as XLE fell −34.4% in the oil price war. A sign-flipped or
misaligned implementation would not reproduce both.

**Against lookahead.** The signal is rebuilt from history truncated at
*t−2* and must come out identical, and the formation window is asserted to
end exactly two months before the holding month.

## 9. What remains unverified

In descending order of how much it would change the conclusion:

- **The post-hoc alpha cannot be honestly assessed on this sample.** This
  is not a gap that more work here can close — it is what "post-hoc" means.
  See §10.
- **Short borrow rates are assumed, not measured.** §4 reports a
  sensitivity grid rather than an omission, but actual historical rates for
  these ETFs come from securities-lending vendors and are not public. The
  assumption that sector SPDRs were general collateral throughout is
  reasonable but unverified.
- **Turnover ignores intra-month weight drift**, mildly understating costs.
- **The universe stops spanning the market after 2018.** Excluding XLC is
  the right call for panel balance, but it means the post-2018 sample omits
  a large and fast-growing part of the index. §4 shows the conclusion holds
  on the composition-stable window, which addresses the definition breaks
  but not this coverage point.
- **Yahoo restates historical adjusted closes.** A rerun could shift
  numbers slightly. The 44 ticker-year checks would catch a material
  restatement, not a small one.

Closed since the first draft: all ten tickers are now verified against
published annual returns (was: two of ten); borrow is now a reported
sensitivity (was: omitted); the composition breaks now have a named
robustness check (was: flagged only); and the construction is now tied to
Jegadeesh & Titman's original *J* values and the standard skip convention
(was: an unverified appeal to "the literature").

## 10. What would change my mind

Both open threads — the post-hoc alpha (§6–7) and the power problem (§5)
— have the same fix, which is the useful thing to notice: **a longer,
finer cross-section.**

Fama–French industry portfolios extend back to 1926 and come in 30- and
48-industry versions. That attacks both constraints at once: roughly four
times the sample length, and a cross-section fine enough to sort into
genuinely extreme deciles rather than top-3-of-9. Both raise power
substantially, and the pre-1999 period is data this sample cannot have
contaminated, so it is a real out-of-sample test of the §6 alpha rather
than another look at the same observations.

A conditional-beta or regime-aware specification would also address the
instability in §7.2 directly rather than averaging over it.

Until then the reportable result is the one in §4: **no effect detected.**
