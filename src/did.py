"""
did.py : Difference-in-Differences estimators for the minimum wage study
========================================================================
Three specifications, in increasing rigour:

1. Canonical 2x2 DiD (binary treated x post) via OLS
2. Two-way fixed effects (county + year FE) with continuous bite x post
3. Event study (year-by-year treatment effects, to check parallel trends)

Uses linearmodels.PanelOLS for fixed effects and statsmodels for OLS.
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from linearmodels.panel import PanelOLS


# ── 1. Canonical 2x2 DiD ────────────────────────────────────────────────────
def canonical_did(df: pd.DataFrame, outcome: str = "log_unemployed"):
    """
    OLS:  Y = b0 + b1*treated + b2*post + b3*(treated x post) + e
    b3 is the DiD estimate (effect of treatment on the treated).
    """
    model = smf.ols(
        f"{outcome} ~ treated + post + treated_x_post",
        data=df
    ).fit(cov_type="cluster", cov_kwds={"groups": df["kreis_id"]})
    return model


# ── 2. Two-way fixed effects with continuous bite ──────────────────────────
def twfe_did(df: pd.DataFrame, outcome: str = "log_unemployed"):
    """
    Two-way fixed effects:
        Y_it = a_i + d_t + b*(bite_i x post_t) + e_it
    County FE (a_i) absorb time-invariant regional differences.
    Year FE (d_t) absorb common shocks.
    b on bite_x_post is the continuous-treatment DiD estimate.
    """
    panel = df.set_index(["kreis_id", "year"])
    mod = PanelOLS(
        panel[outcome],
        panel[["bite_x_post"]],
        entity_effects=True,
        time_effects=True,
    )
    return mod.fit(cov_type="clustered", cluster_entity=True)


# ── 3. Event study (dynamic treatment effects) ─────────────────────────────
def event_study(df: pd.DataFrame, outcome: str = "log_unemployed",
                base_year: int = 2014):
    """
    Interact bite with each year dummy (omitting base_year, 2014, as reference).
    The coefficients trace out the treatment effect year by year:
      - pre-2015 coefficients near zero  -> parallel trends hold
      - post-2015 coefficients diverge   -> treatment effect emerges
    Returns a tidy DataFrame of year, coefficient, and 95% CI.
    """
    d = df.copy()
    years = sorted(d["year"].unique())
    for y in years:
        if y == base_year:
            continue
        d[f"bite_x_{y}"] = d["bite_proxy"] * (d["year"] == y).astype(int)

    interaction_terms = [f"bite_x_{y}" for y in years if y != base_year]
    panel = d.set_index(["kreis_id", "year"])
    mod = PanelOLS(
        panel[outcome],
        panel[interaction_terms],
        entity_effects=True,
        time_effects=True,
    )
    res = mod.fit(cov_type="clustered", cluster_entity=True)

    rows = []
    for y in years:
        if y == base_year:
            rows.append({"year": y, "coef": 0.0, "ci_low": 0.0, "ci_high": 0.0})
        else:
            term = f"bite_x_{y}"
            coef = res.params[term]
            se   = res.std_errors[term]
            rows.append({
                "year": y,
                "coef": coef,
                "ci_low": coef - 1.96 * se,
                "ci_high": coef + 1.96 * se,
            })
    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True), res


# ── helper: run all three outcomes through TWFE ────────────────────────────
def summary_table(df: pd.DataFrame,
                  outcomes=("log_unemployed",)):
    """Compact table of the continuous bite_x_post effect for each outcome."""
    rows = []
    labels = {
        "log_unemployed": "Log unemployment",
        "unemployed": "Unemployment (count)",
    }
    for out in outcomes:
        res = twfe_did(df, outcome=out)
        coef = res.params["bite_x_post"]
        se   = res.std_errors["bite_x_post"]
        pval = res.pvalues["bite_x_post"]
        stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""
        rows.append({
            "Outcome": labels.get(out, out),
            "Bite x Post coef": f"{coef:.3f}{stars}",
            "Std error": f"({se:.3f})",
            "p-value": f"{pval:.3f}",
        })
    return pd.DataFrame(rows)
