#!/usr/bin/env python3
"""Where the GHG reduction in the BA climate credit line actually came from.

Specification
-------------
Primary model (OLS, HC3 robust SEs):

    log(ghg_tco2_yr) = β0 + β1 log(loan_usd)
                       + AssetType + Sector + Region + BorrowerSize + Year + ε

Reference levels: Efficient boiler, Manufacturing, Urban, Small, 2021.

Why this spec
-------------
GHG and ticket size are strictly positive and right-skewed. A levels OLS would
be identified off a handful of industrial-process outliers and would mix two
different mechanisms (bigger loans vs higher-intensity assets). Log-log
separates scale from technology: β1 is an elasticity; asset-type coefficients
are multiplicative intensity premia holding loan size fixed. Year dummies
absorb vintage/reporting drift. HC3 SEs allow residual variance to differ by
asset class.

This is an accounting / association model on reported figures, not a causal
impact estimate.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor

CSV = Path(__file__).resolve().parent / "data" / "ba_loan_climate_subloans.csv"
TARGET_TCO2 = 20_469.0
OUT = Path("/tmp/ba_loan_ghg_analysis.json")


def fmt(n: float, digits: int = 1) -> float:
    return round(float(n), digits)


def share(part: float, total: float) -> float:
    return round(100.0 * part / total, 1)


def group_table(df: pd.DataFrame, col: str, total_ghg: float, total_usd: float) -> list[dict]:
    g = (
        df.groupby(col, observed=True)
        .agg(
            n=("loan_id", "count"),
            loan_usd=("loan_usd", "sum"),
            ghg=("ghg_tco2_yr", "sum"),
            median_ghg=("ghg_tco2_yr", "median"),
            mean_ghg=("ghg_tco2_yr", "mean"),
        )
        .reset_index()
    )
    g["intensity"] = g["ghg"] / g["loan_usd"] * 1_000_000
    g["ghg_share"] = 100.0 * g["ghg"] / total_ghg
    g["usd_share"] = 100.0 * g["loan_usd"] / total_usd
    g = g.sort_values("ghg", ascending=False)
    rows = []
    for _, r in g.iterrows():
        rows.append(
            {
                "name": str(r[col]),
                "n": int(r["n"]),
                "loan_usd": fmt(r["loan_usd"], 0),
                "ghg": fmt(r["ghg"], 1),
                "median_ghg": fmt(r["median_ghg"], 1),
                "mean_ghg": fmt(r["mean_ghg"], 1),
                "intensity": fmt(r["intensity"], 1),
                "ghg_share": fmt(r["ghg_share"], 1),
                "usd_share": fmt(r["usd_share"], 1),
            }
        )
    return rows


def coef_table(res, terms: list[str] | None = None) -> list[dict]:
    rows = []
    for name in res.params.index:
        if terms is not None and name not in terms:
            continue
        ci = res.conf_int().loc[name]
        rows.append(
            {
                "term": name,
                "coef": fmt(res.params[name], 4),
                "se": fmt(res.bse[name], 4),
                "t": fmt(res.tvalues[name], 2),
                "p": fmt(res.pvalues[name], 4),
                "ci_low": fmt(ci.iloc[0], 4),
                "ci_high": fmt(ci.iloc[1], 4),
                "mult": fmt(np.exp(res.params[name]), 3)
                if name != "Intercept"
                else None,
            }
        )
    return rows


def main() -> None:
    df = pd.read_csv(CSV)
    assert len(df) == 214, len(df)
    assert df.isna().sum().sum() == 0

    df["log_ghg"] = np.log(df["ghg_tco2_yr"])
    df["log_loan"] = np.log(df["loan_usd"])
    df["intensity"] = df["ghg_tco2_yr"] / df["loan_usd"] * 1_000_000
    df["year"] = df["year"].astype("category")
    df["asset_type"] = pd.Categorical(
        df["asset_type"],
        categories=[
            "Efficient boiler",
            "Cold chain",
            "Fleet renewal",
            "EDGE green building",
            "Solar PV",
            "Industrial process",
        ],
    )
    df["sector"] = pd.Categorical(
        df["sector"],
        categories=[
            "Manufacturing",
            "Agribusiness",
            "Real estate",
            "Retail & services",
            "Transport",
        ],
    )
    df["region"] = pd.Categorical(df["region"], categories=["Urban", "Rural"])
    df["borrower_size"] = pd.Categorical(
        df["borrower_size"], categories=["Small", "Micro", "Medium"]
    )

    total_ghg = float(df["ghg_tco2_yr"].sum())
    total_usd = float(df["loan_usd"].sum())
    n = len(df)

    ranked = df.sort_values("ghg_tco2_yr", ascending=False).reset_index(drop=True)
    ranked["cum_ghg"] = ranked["ghg_tco2_yr"].cumsum()
    ranked["cum_share"] = ranked["cum_ghg"] / total_ghg
    ranked["rank"] = np.arange(1, n + 1)
    ranked["deal_share"] = ranked["rank"] / n

    def deals_for(threshold: float) -> int:
        return int((ranked["cum_share"] < threshold).sum() + 1)

    top_ns = [1, 5, 10, 15, 20]
    top_shares = {
        f"top_{k}": {
            "n": k,
            "deal_pct": round(100.0 * k / n, 1),
            "ghg": fmt(ranked.loc[: k - 1, "ghg_tco2_yr"].sum(), 1),
            "ghg_share": share(ranked.loc[: k - 1, "ghg_tco2_yr"].sum(), total_ghg),
            "usd_share": share(ranked.loc[: k - 1, "loan_usd"].sum(), total_usd),
        }
        for k in top_ns
    }

    # Gini on GHG
    x = np.sort(df["ghg_tco2_yr"].to_numpy())
    gini = float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))

    # Lorenz points for canvas (every ~5 deals plus endpoints)
    lorenz_idx = sorted(set([0] + list(range(4, n, 5)) + [n - 1]))
    lorenz = [
        {
            "deals": int(ranked.loc[i, "rank"]),
            "deal_pct": fmt(100.0 * ranked.loc[i, "deal_share"], 1),
            "ghg_share": fmt(100.0 * ranked.loc[i, "cum_share"], 1),
        }
        for i in lorenz_idx
    ]
    # equal-volume Lorenz for comparison
    vol = df.sort_values("loan_usd", ascending=False).reset_index(drop=True)
    vol["cum_share"] = vol["loan_usd"].cumsum() / total_usd
    vol_lorenz = [
        fmt(100.0 * vol.loc[i, "cum_share"], 1) for i in lorenz_idx
    ]

    top10 = []
    for _, r in ranked.head(10).iterrows():
        top10.append(
            {
                "loan_id": r["loan_id"],
                "year": int(r["year"]),
                "asset_type": r["asset_type"],
                "sector": r["sector"],
                "region": r["region"],
                "borrower_size": r["borrower_size"],
                "loan_usd": fmt(r["loan_usd"], 0),
                "ghg": fmt(r["ghg_tco2_yr"], 1),
                "ghg_share": share(r["ghg_tco2_yr"], total_ghg),
                "intensity": fmt(r["intensity"], 1),
            }
        )

    industrial = df[df["asset_type"] == "Industrial process"]
    rest = df[df["asset_type"] != "Industrial process"]
    solar = df[df["asset_type"] == "Solar PV"]
    without_top10 = ranked.iloc[10:]

    formula = (
        "log_ghg ~ log_loan + C(asset_type) + C(sector) + C(region) "
        "+ C(borrower_size) + C(year)"
    )
    model = smf.ols(formula, data=df).fit(cov_type="HC3")

    nested = {
        "size_only": smf.ols("log_ghg ~ log_loan", data=df).fit(cov_type="HC3"),
        "size_asset": smf.ols(
            "log_ghg ~ log_loan + C(asset_type)", data=df
        ).fit(cov_type="HC3"),
        "size_asset_sector": smf.ols(
            "log_ghg ~ log_loan + C(asset_type) + C(sector)", data=df
        ).fit(cov_type="HC3"),
        "full": model,
    }
    nested_fit = {
        k: {
            "r2": fmt(v.rsquared, 3),
            "r2_adj": fmt(v.rsquared_adj, 3),
            "n": int(v.nobs),
            "aic": fmt(v.aic, 1),
            "elasticity": fmt(v.params["log_loan"], 3),
            "elasticity_se": fmt(v.bse["log_loan"], 3),
            "elasticity_p": fmt(v.pvalues["log_loan"], 4),
        }
        for k, v in nested.items()
    }

    # Type II ANOVA on the OLS (non-robust, for variance shares)
    anova = sm.stats.anova_lm(model, typ=2)
    ss_total = float(anova["sum_sq"].sum())
    anova_rows = []
    for term, r in anova.iterrows():
        anova_rows.append(
            {
                "term": term,
                "sum_sq": fmt(r["sum_sq"], 3),
                "df": int(r["df"]),
                "f": None if pd.isna(r["F"]) else fmt(r["F"], 2),
                "p": None if pd.isna(r["PR(>F)"]) else fmt(r["PR(>F)"], 4),
                "share_of_explained": fmt(100.0 * r["sum_sq"] / (ss_total - anova.loc["Residual", "sum_sq"]), 1)
                if term != "Residual"
                else None,
            }
        )

    # VIF on the design matrix excluding intercept
    exog = model.model.exog
    names = model.model.exog_names
    vif_rows = []
    for i, name in enumerate(names):
        if name == "Intercept":
            continue
        vif_rows.append({"term": name, "vif": fmt(variance_inflation_factor(exog, i), 2)})

    # Influence: how much the top GHG deals pull the elasticity
    infl = model.get_influence()
    cooks = infl.cooks_distance[0]
    influence = (
        pd.DataFrame(
            {
                "loan_id": df["loan_id"].to_numpy(),
                "asset_type": df["asset_type"].to_numpy(),
                "ghg": df["ghg_tco2_yr"].to_numpy(),
                "cooks": cooks,
                "student_resid": infl.resid_studentized_internal,
            }
        )
        .sort_values("cooks", ascending=False)
        .head(8)
    )
    influence_rows = [
        {
            "loan_id": r["loan_id"],
            "asset_type": r["asset_type"],
            "ghg": fmt(r["ghg"], 1),
            "cooks": fmt(r["cooks"], 4),
            "student_resid": fmt(r["student_resid"], 2),
        }
        for _, r in influence.iterrows()
    ]

    # Residual diagnostics
    resid = model.resid
    fitted = model.fittedvalues
    jb = sm.stats.jarque_bera(resid)
    bp = sm.stats.het_breuschpagan(resid, model.model.exog)

    # Leave-out industrial process: does the overshoot survive?
    rest_ghg = float(rest["ghg_tco2_yr"].sum())
    no_top10_ghg = float(without_top10["ghg_tco2_yr"].sum())
    industrial_only = float(industrial["ghg_tco2_yr"].sum())
    solar_plus_ind = float(
        df[df["asset_type"].isin(["Industrial process", "Solar PV"])]["ghg_tco2_yr"].sum()
    )

    # Intensity OLS as robustness: what drives tCO2 per $m, not scale
    intensity_model = smf.ols(
        "np.log(intensity) ~ C(asset_type) + C(sector) + C(region) "
        "+ C(borrower_size) + C(year)",
        data=df,
    ).fit(cov_type="HC3")

    asset_mult = []
    for name, coef in model.params.items():
        if not name.startswith("C(asset_type)"):
            continue
        label = name.split("[T.")[1].rstrip("]")
        asset_mult.append(
            {
                "asset": label,
                "log_coef": fmt(coef, 3),
                "se": fmt(model.bse[name], 3),
                "p": fmt(model.pvalues[name], 4),
                "multiplier_vs_boiler": fmt(np.exp(coef), 2),
                "ci_low": fmt(np.exp(model.conf_int().loc[name].iloc[0]), 2),
                "ci_high": fmt(np.exp(model.conf_int().loc[name].iloc[1]), 2),
            }
        )

    # Predicted GHG at median loan, by asset type (others at reference)
    median_loan = float(df["loan_usd"].median())
    grid = []
    for asset in df["asset_type"].cat.categories:
        row = pd.DataFrame(
            {
                "log_loan": [np.log(median_loan)],
                "asset_type": pd.Categorical([asset], categories=df["asset_type"].cat.categories),
                "sector": pd.Categorical(["Manufacturing"], categories=df["sector"].cat.categories),
                "region": pd.Categorical(["Urban"], categories=df["region"].cat.categories),
                "borrower_size": pd.Categorical(["Small"], categories=df["borrower_size"].cat.categories),
                "year": pd.Categorical([2023], categories=df["year"].cat.categories),
            }
        )
        pred_log = float(model.predict(row).iloc[0])
        grid.append(
            {
                "asset": asset,
                "pred_ghg_at_median_loan": fmt(np.exp(pred_log), 1),
            }
        )

    # Pareto points for bar: cumulative GHG share at selected ranks
    pareto_ranks = [1, 5, 10, 20, 50, 100, 214]
    pareto = []
    for k in pareto_ranks:
        pareto.append(
            {
                "label": f"{k}" if k < 214 else "214 (all)",
                "ghg_share": share(ranked.loc[: k - 1, "ghg_tco2_yr"].sum(), total_ghg),
                "usd_share": share(ranked.loc[: k - 1, "loan_usd"].sum(), total_usd),
            }
        )

    payload = {
        "n": n,
        "years": [int(y) for y in sorted(df["year"].unique())],
        "target": TARGET_TCO2,
        "total_ghg": fmt(total_ghg, 1),
        "total_usd": fmt(total_usd, 0),
        "multiple": fmt(total_ghg / TARGET_TCO2, 2),
        "mean_ghg": fmt(df["ghg_tco2_yr"].mean(), 1),
        "median_ghg": fmt(df["ghg_tco2_yr"].median(), 1),
        "p90_ghg": fmt(df["ghg_tco2_yr"].quantile(0.9), 1),
        "max_ghg": fmt(df["ghg_tco2_yr"].max(), 1),
        "mean_loan": fmt(df["loan_usd"].mean(), 0),
        "median_loan": fmt(median_loan, 0),
        "mean_intensity": fmt(df["intensity"].mean(), 1),
        "median_intensity": fmt(df["intensity"].median(), 1),
        "gini_ghg": fmt(gini, 3),
        "deals_for_50": deals_for(0.50),
        "deals_for_80": deals_for(0.80),
        "deals_for_90": deals_for(0.90),
        "top_shares": top_shares,
        "lorenz": lorenz,
        "vol_lorenz": vol_lorenz,
        "pareto": pareto,
        "top10": top10,
        "by_asset": group_table(df, "asset_type", total_ghg, total_usd),
        "by_sector": group_table(df, "sector", total_ghg, total_usd),
        "by_region": group_table(df, "region", total_ghg, total_usd),
        "by_size": group_table(df, "borrower_size", total_ghg, total_usd),
        "by_year": group_table(df, "year", total_ghg, total_usd),
        "industrial": {
            "n": int(len(industrial)),
            "n_share": share(len(industrial), n),
            "ghg": fmt(industrial_only, 1),
            "ghg_share": share(industrial_only, total_ghg),
            "usd_share": share(float(industrial["loan_usd"].sum()), total_usd),
            "median_ghg": fmt(industrial["ghg_tco2_yr"].median(), 1),
            "intensity": fmt(industrial["intensity"].median(), 1),
        },
        "solar": {
            "n": int(len(solar)),
            "n_share": share(len(solar), n),
            "ghg": fmt(float(solar["ghg_tco2_yr"].sum()), 1),
            "ghg_share": share(float(solar["ghg_tco2_yr"].sum()), total_ghg),
            "usd_share": share(float(solar["loan_usd"].sum()), total_usd),
        },
        "counterfactuals": {
            "without_industrial_ghg": fmt(rest_ghg, 1),
            "without_industrial_multiple": fmt(rest_ghg / TARGET_TCO2, 2),
            "without_top10_ghg": fmt(no_top10_ghg, 1),
            "without_top10_multiple": fmt(no_top10_ghg / TARGET_TCO2, 2),
            "industrial_plus_solar_share": share(solar_plus_ind, total_ghg),
            "bottom_half_ghg_share": share(
                float(ranked.tail(n // 2)["ghg_tco2_yr"].sum()), total_ghg
            ),
        },
        "spec": {
            "formula": formula,
            "cov": "HC3",
            "n": int(model.nobs),
            "r2": fmt(model.rsquared, 3),
            "r2_adj": fmt(model.rsquared_adj, 3),
            "f_p": fmt(model.f_pvalue, 4),
            "elasticity": fmt(model.params["log_loan"], 3),
            "elasticity_se": fmt(model.bse["log_loan"], 3),
            "elasticity_p": fmt(model.pvalues["log_loan"], 4),
            "elasticity_ci": [
                fmt(model.conf_int().loc["log_loan"].iloc[0], 3),
                fmt(model.conf_int().loc["log_loan"].iloc[1], 3),
            ],
        },
        "nested": nested_fit,
        "anova": anova_rows,
        "vif_max": max(v["vif"] for v in vif_rows),
        "vif_high": [v for v in vif_rows if v["vif"] >= 5],
        "asset_multipliers": asset_mult,
        "predicted_at_median_loan": grid,
        "influence": influence_rows,
        "diagnostics": {
            "resid_skew": fmt(float(pd.Series(resid).skew()), 3),
            "jarque_bera_p": fmt(jb[1], 4),
            "breusch_pagan_p": fmt(bp[1], 4),
            "corr_fitted_resid": fmt(float(np.corrcoef(fitted, resid)[0, 1]), 3),
        },
        "intensity_model": {
            "r2": fmt(intensity_model.rsquared, 3),
            "asset_p_industrial": fmt(
                intensity_model.pvalues["C(asset_type)[T.Industrial process]"], 4
            ),
            "industrial_mult": fmt(
                np.exp(intensity_model.params["C(asset_type)[T.Industrial process]"]), 2
            ),
            "solar_mult": fmt(
                np.exp(intensity_model.params["C(asset_type)[T.Solar PV]"]), 2
            ),
        },
        "other_coefs": coef_table(
            model,
            [
                "C(region)[T.Rural]",
                "C(borrower_size)[T.Micro]",
                "C(borrower_size)[T.Medium]",
                "C(sector)[T.Agribusiness]",
                "C(sector)[T.Real estate]",
                "C(sector)[T.Retail & services]",
                "C(sector)[T.Transport]",
                "C(year)[T.2022]",
                "C(year)[T.2023]",
                "C(year)[T.2024]",
            ],
        ),
        "full_summary": model.summary().as_text(),
    }

    OUT.write_text(json.dumps(payload, indent=2))
    print(model.summary())
    print("\n--- Nested R2 ---")
    for k, v in nested_fit.items():
        print(k, v)
    print("\n--- ANOVA ---")
    print(anova)
    print("\n--- Key concentration ---")
    print("total_ghg", total_ghg, "multiple", total_ghg / TARGET_TCO2)
    print("deals for 50/80/90", deals_for(0.5), deals_for(0.8), deals_for(0.9))
    print("gini", gini)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
