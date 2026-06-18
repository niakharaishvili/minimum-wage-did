"""
visualize.py : plots for the real-data minimum wage DiD study
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

REPORTS = Path(__file__).resolve().parents[1] / "reports"
REPORTS.mkdir(exist_ok=True)

TREAT_COLOR = "#c0392b"
CTRL_COLOR  = "#2980b9"
FT = 14


def _save(fig, name, save):
    if save:
        p = REPORTS / f"{name}.png"
        fig.savefig(p, dpi=150, bbox_inches="tight")
        print(f"Saved -> {p}")


def plot_bite_distribution(df, save=False):
    bite = df[df["year"] == 2014]["bite_proxy"]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(bite, bins=30, color="#34495e", edgecolor="white")
    ax.axvline(bite.median(), color=TREAT_COLOR, linestyle="--",
               label=f"Median = {bite.median():.2f}")
    ax.set_title("Distribution of Minimum-Wage Bite Proxy Across Counties (2014)",
                 fontsize=FT)
    ax.set_xlabel("Bite proxy (2014 unemployment relative to mean)")
    ax.set_ylabel("Number of counties")
    ax.legend()
    sns.despine(ax=ax)
    plt.tight_layout()
    _save(fig, "01_bite_distribution", save)
    plt.show()


def plot_parallel_trends(df, save=False):
    """Mean log unemployment over time for treated vs control counties."""
    g = df.groupby(["year", "treated"])["log_unemployed"].mean().unstack()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(g.index, g[1], "o-", color=TREAT_COLOR, linewidth=2,
            label="High bite (treated)")
    ax.plot(g.index, g[0], "s-", color=CTRL_COLOR, linewidth=2,
            label="Low bite (control)")
    ax.axvline(2014.5, color="grey", linestyle="--", alpha=0.7)
    ax.text(2014.6, ax.get_ylim()[1] * 0.99, "Min. wage\nintroduced",
            fontsize=9, color="grey", va="top")
    ax.set_title("Trends: Log County Unemployment, High vs Low Bite", fontsize=FT)
    ax.set_xlabel("Year")
    ax.set_ylabel("Mean log unemployment")
    ax.legend()
    sns.despine(ax=ax)
    plt.tight_layout()
    _save(fig, "02_parallel_trends", save)
    plt.show()


def plot_east_west(df, save=False):
    """Real descriptive: unemployment trajectory East vs West."""
    g = df.groupby(["year", "east"])["unemployed"].mean().unstack()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(g.index, g[1], "o-", color="#8e44ad", linewidth=2, label="East Germany")
    ax.plot(g.index, g[0], "s-", color="#16a085", linewidth=2, label="West Germany")
    ax.axvline(2014.5, color="grey", linestyle="--", alpha=0.7)
    ax.text(2014.6, ax.get_ylim()[1] * 0.97, "Min. wage\nintroduced",
            fontsize=9, color="grey", va="top")
    ax.set_title("Mean County Unemployment: East vs West Germany", fontsize=FT)
    ax.set_xlabel("Year")
    ax.set_ylabel("Mean unemployed persons per county")
    ax.legend()
    sns.despine(ax=ax)
    plt.tight_layout()
    _save(fig, "03_east_west", save)
    plt.show()


def plot_event_study(event_df, save=False):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.errorbar(event_df["year"], event_df["coef"],
                yerr=[event_df["coef"] - event_df["ci_low"],
                      event_df["ci_high"] - event_df["coef"]],
                fmt="o", color=TREAT_COLOR, capsize=4, linewidth=1.5, markersize=7)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(2014.5, color="grey", linestyle="--", alpha=0.7)
    ax.text(2014.6, ax.get_ylim()[1] * 0.9, "Treatment\n(2015)",
            fontsize=9, color="grey", va="top")
    ax.set_title("Event Study: dynamic effect of bite on log unemployment",
                 fontsize=FT)
    ax.set_xlabel("Year")
    ax.set_ylabel("Coefficient on (bite x year)")
    sns.despine(ax=ax)
    plt.tight_layout()
    _save(fig, "04_event_study", save)
    plt.show()
