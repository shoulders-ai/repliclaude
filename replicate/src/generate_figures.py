"""
Generate all 6 paper figures as PNGs.

Figure 1: Long-term solar activity (27-day rolling M/X flare days + sunspot number)
Figure 2: Seasonal distribution (flares by day of year)
Figure 3: Empirical conditional probability P(flare | n consecutive flare-free days)
Figure 4: Reliability diagrams (SWPC forecast probability vs observed frequency)
Figure 5: Storm-after-calm confusion matrix
Figure 6: All-clear confusion matrix

Usage: bash tools/run.sh replicate/src/generate_figures.py
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, "data", "processed")
FIGS = os.path.join(BASE, "results", "figures")
os.makedirs(FIGS, exist_ok=True)

# Load data
eval_df = pd.read_csv(os.path.join(PROC, "evaluation_dataset.csv"))
eval_df["date"] = pd.to_datetime(eval_df["date"])

merged_df = pd.read_csv(os.path.join(PROC, "merged_dataset.csv"))
merged_df["date"] = pd.to_datetime(merged_df["date"])
merged_df = merged_df.sort_values("date").reset_index(drop=True)

# Shared style
plt.rcParams.update({
    "figure.dpi": 150,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
})


def figure_1():
    """Long-term solar activity: 27-day rolling M/X flare days + sunspot number."""
    print("Generating Figure 1: Long-term solar activity...")
    df = merged_df.copy()

    # 27-day rolling sum of flare days
    df = df.set_index("date").sort_index()
    m_rolling = df["m_label"].rolling(27, min_periods=1).sum()
    x_rolling = df["x_label"].rolling(27, min_periods=1).sum()
    ssn = df["sunspot_number"]

    fig, ax1 = plt.subplots(figsize=(12, 5))

    ax1.fill_between(m_rolling.index, m_rolling.values, alpha=0.4, color="tab:orange", label="M-class (27-day rolling)")
    ax1.fill_between(x_rolling.index, x_rolling.values, alpha=0.6, color="tab:red", label="X-class (27-day rolling)")
    ax1.set_ylabel("Flare days (27-day rolling sum)")
    ax1.set_xlabel("Year")
    ax1.set_ylim(0, None)

    ax2 = ax1.twinx()
    ax2.plot(ssn.index, ssn.values, color="gray", alpha=0.5, linewidth=0.5, label="Sunspot number")
    ax2.set_ylabel("Daily sunspot number", color="gray")
    ax2.tick_params(axis="y", labelcolor="gray")

    # Combine legends
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=9)

    ax1.set_title("Figure 1: Long-term Solar Activity (1996-2024)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "figure_1_solar_activity.png"))
    plt.close(fig)
    print("  Saved figure_1_solar_activity.png")


def figure_2():
    """Seasonal distribution: flares by day of year."""
    print("Generating Figure 2: Seasonal distribution...")
    df = eval_df.copy()
    df["doy"] = df["date"].dt.dayofyear

    # Bin by month for cleaner display
    df["month"] = df["date"].dt.month
    m_by_month = df.groupby("month")["m_label"].sum()
    x_by_month = df.groupby("month")["x_label"].sum()

    months = np.arange(1, 13)
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    fig, ax = plt.subplots(figsize=(10, 5))
    width = 0.4
    ax.bar(months - width/2, m_by_month.values, width, label="M-class", color="tab:orange", alpha=0.8)
    ax.bar(months + width/2, x_by_month.values, width, label="X-class", color="tab:red", alpha=0.8)
    ax.set_xticks(months)
    ax.set_xticklabels(month_labels)
    ax.set_xlabel("Month")
    ax.set_ylabel("Total flare days (1998-2024)")
    ax.legend()
    ax.set_title("Figure 2: Seasonal Distribution of Solar Flare Days")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "figure_2_seasonal_distribution.png"))
    plt.close(fig)
    print("  Saved figure_2_seasonal_distribution.png")


def figure_3():
    """Empirical conditional probability P(flare | n consecutive flare-free days)."""
    print("Generating Figure 3: Conditional probability...")
    df = eval_df.copy()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    for ax, flare_class, label, color in [
        (ax1, "m", "M-class", "tab:orange"),
        (ax2, "x", "X-class", "tab:red"),
    ]:
        consec_col = f"{flare_class}_consec_free"
        label_col = f"{flare_class}_label"

        max_n = 50
        ns = range(0, max_n + 1)
        probs = []
        counts = []
        for n in ns:
            subset = df[df[consec_col] == n]
            if len(subset) > 0:
                probs.append(subset[label_col].mean())
                counts.append(len(subset))
            else:
                probs.append(np.nan)
                counts.append(0)

        ax.plot(list(ns), probs, color=color, linewidth=1.5, marker="o", markersize=3)
        ax.set_xlabel("Consecutive flare-free days (n)")
        ax.set_ylabel(f"P({label} flare | n free days)")
        ax.set_title(f"{label}")
        ax.set_ylim(-0.02, max(0.6, max(p for p in probs if p is not None and not np.isnan(p)) * 1.1))
        ax.axhline(y=df[label_col].mean(), color="gray", linestyle="--", alpha=0.5, label="Climatological rate")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    fig.suptitle("Figure 3: Empirical Conditional Probability of Flare Given n Flare-Free Days", fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "figure_3_conditional_probability.png"))
    plt.close(fig)
    print("  Saved figure_3_conditional_probability.png")


def figure_4():
    """Reliability diagrams: SWPC forecast probability vs observed frequency."""
    print("Generating Figure 4: Reliability diagrams...")
    df = eval_df.copy()

    fig, axes = plt.subplots(2, 3, figsize=(14, 9))

    for row, flare_class in enumerate(["m", "x"]):
        label_col = f"{flare_class}_label"
        for col, lead in enumerate(["24h", "48h", "72h"]):
            ax = axes[row, col]
            prob_col = f"{flare_class}_{lead}"
            valid = df[df[prob_col].notna()].copy()
            y_true = valid[label_col].values.astype(int)
            y_prob = valid[prob_col].values / 100.0

            # Bin forecasts into probability bins
            bins = np.arange(0, 1.05, 0.05)
            bin_centers = []
            observed_freq = []
            bin_counts = []

            for i in range(len(bins) - 1):
                mask = (y_prob >= bins[i]) & (y_prob < bins[i + 1])
                if mask.sum() > 0:
                    bin_centers.append((bins[i] + bins[i + 1]) / 2)
                    observed_freq.append(y_true[mask].mean())
                    bin_counts.append(mask.sum())

            ax.plot([0, 1], [0, 1], "k--", alpha=0.5, linewidth=1, label="Perfect calibration")
            ax.scatter(bin_centers, observed_freq, s=[min(c/5, 100) for c in bin_counts],
                      color="tab:blue", alpha=0.7, zorder=3)
            ax.plot(bin_centers, observed_freq, color="tab:blue", alpha=0.5, linewidth=1)
            ax.set_xlim(-0.02, 1.02)
            ax.set_ylim(-0.02, 1.02)
            ax.set_xlabel("Forecast probability")
            ax.set_ylabel("Observed frequency")
            ax.set_title(f"{flare_class.upper()}-class, {lead}")
            ax.grid(True, alpha=0.3)
            if row == 0 and col == 0:
                ax.legend(fontsize=8)

    fig.suptitle("Figure 4: SWPC Reliability Diagrams", fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "figure_4_reliability_diagrams.png"))
    plt.close(fig)
    print("  Saved figure_4_reliability_diagrams.png")


def figure_5():
    """Storm-after-calm confusion matrix (X-class, >30 quiet days, SWPC 24h, theta=0.05)."""
    print("Generating Figure 5: Storm-after-calm confusion matrix...")
    valid = eval_df[eval_df["x_24h"].notna()].copy()
    calm_mask = valid["x_consec_free"] > 30
    calm_data = valid[calm_mask]

    y_true = calm_data["x_label"].values.astype(int)
    y_prob = calm_data["x_24h"].values / 100.0
    y_pred = (y_prob >= 0.05).astype(int)

    TP = ((y_pred == 1) & (y_true == 1)).sum()
    FP = ((y_pred == 1) & (y_true == 0)).sum()
    FN = ((y_pred == 0) & (y_true == 1)).sum()
    TN = ((y_pred == 0) & (y_true == 0)).sum()

    cm = np.array([[TP, FP], [FN, TN]])

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues", aspect="auto")

    for i in range(2):
        for j in range(2):
            color = "white" if cm[i, j] > cm.max() / 2 else "black"
            ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center",
                   fontsize=16, fontweight="bold", color=color)

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Flare (Observed)", "No Flare (Observed)"])
    ax.set_yticklabels(["Flare (Predicted)", "No Flare (Predicted)"])
    ax.set_title(f"Figure 5: Storm After the Calm\n"
                 f"X-class, >30 quiet days, SWPC 24h, θ=0.05\n"
                 f"Miss rate: {FN/(TP+FN):.2f}, FAR: {FP/(TP+FP):.2f}",
                 fontsize=11)
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "figure_5_storm_after_calm.png"))
    plt.close(fig)
    print(f"  TP={TP}, FN={FN}, FP={FP}, TN={TN}")
    print("  Saved figure_5_storm_after_calm.png")


def figure_6():
    """All-clear confusion matrix (X-class +1/+2/+3 days, SWPC 24h, theta=0.05)."""
    print("Generating Figure 6: All-clear confusion matrix...")
    x_flare_dates = set(merged_df[merged_df["x_label"] == 1]["date"])

    all_clear_dates = set()
    for d in x_flare_dates:
        for offset in [1, 2, 3]:
            all_clear_dates.add(d + pd.Timedelta(days=offset))

    ac_mask = eval_df["date"].isin(all_clear_dates) & eval_df["x_24h"].notna()
    ac_data = eval_df[ac_mask]

    y_true = ac_data["x_label"].values.astype(int)
    y_prob = ac_data["x_24h"].values / 100.0
    y_pred = (y_prob >= 0.05).astype(int)

    TP = ((y_pred == 1) & (y_true == 1)).sum()
    FP = ((y_pred == 1) & (y_true == 0)).sum()
    FN = ((y_pred == 0) & (y_true == 1)).sum()
    TN = ((y_pred == 0) & (y_true == 0)).sum()

    cm = np.array([[TP, FP], [FN, TN]])

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Oranges", aspect="auto")

    for i in range(2):
        for j in range(2):
            color = "white" if cm[i, j] > cm.max() / 2 else "black"
            ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center",
                   fontsize=16, fontweight="bold", color=color)

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Flare (Observed)", "No Flare (Observed)"])
    ax.set_yticklabels(["Flare (Predicted)", "No Flare (Predicted)"])

    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    far = FP / (TP + FP) if (TP + FP) > 0 else 0
    ax.set_title(f"Figure 6: All-Clear Analysis\n"
                 f"X-class +1/+2/+3 days, SWPC 24h, θ=0.05\n"
                 f"Recall: {recall:.2f}, FAR: {far:.2f}",
                 fontsize=11)
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "figure_6_all_clear.png"))
    plt.close(fig)
    print(f"  TP={TP}, FN={FN}, FP={FP}, TN={TN}")
    print("  Saved figure_6_all_clear.png")


if __name__ == "__main__":
    figure_1()
    figure_2()
    figure_3()
    figure_4()
    figure_5()
    figure_6()
    print(f"\nAll 6 figures saved to {FIGS}/")
