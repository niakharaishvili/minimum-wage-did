"""
data_loader.py : German Minimum Wage 2015 : DiD on REAL data
=============================================================
Uses real county-level (Kreis) unemployment data from the German Federal
Employment Agency (Bundesagentur fuer Arbeit), packaged by the RegioHub
"badata" project (Nguyen & Tsolak 2023, MIT licence, DOI 10.5281/zenodo.7664361).

Panel: 400 German counties, 2012-2018, around the 1 January 2015 introduction
of the national minimum wage (8.50 EUR/hour).

Identification: the minimum wage was nationally uniform but bit harder where
more workers earned low wages. We proxy the regional "bite" with pre-treatment
(2014) unemployment intensity, which is strongly correlated with the share of
low-wage workers and with East Germany, where the wage floor bit hardest
(Caliendo et al. 2018; Ahlfeldt, Roth & Seidel 2018).
"""
import numpy as np
import pandas as pd
from pathlib import Path

ROOT      = Path(__file__).resolve().parents[1]
DATA_RAW  = ROOT / "data" / "raw"
DATA_PROC = ROOT / "data" / "processed"

TREATMENT_YEAR = 2015
DATA_FILE = "ba_unemployment_panel.csv"


def load_data() -> pd.DataFrame:
    """Load the real BA county-year panel and construct DiD variables."""
    path = DATA_RAW / DATA_FILE
    if not path.exists():
        raise FileNotFoundError(
            f"Expected real data at {path}. "
            "Download from https://doi.org/10.5281/zenodo.7664361 "
            "and build the county panel (see data-raw/build_panel.py)."
        )
    df = pd.read_csv(path)
    return _prepare(df)


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["year"] = df["year"].astype(int)

    # post-treatment indicator
    df["post"] = (df["year"] >= TREATMENT_YEAR).astype(int)

    # log outcome (unemployment counts are right-skewed)
    df["log_unemployed"] = np.log(df["unemployed"])

    # continuous treatment intensity: pre-treatment bite proxy
    # (already computed in the raw file as bite_proxy = 2014 unemployment / mean)
    # binary treatment: above-median bite
    med = df.loc[df["year"] == 2014, "bite_proxy"].median()
    df["treated"] = (df["bite_proxy"] > med).astype(int)

    # DiD interactions
    df["bite_x_post"]    = df["bite_proxy"] * df["post"]
    df["treated_x_post"] = df["treated"] * df["post"]

    return df.sort_values(["kreis_id", "year"]).reset_index(drop=True)


def save_processed(df: pd.DataFrame, name: str = "ba_panel_processed.csv"):
    p = DATA_PROC / name
    df.to_csv(p, index=False)
    print(f"Saved -> {p}")
