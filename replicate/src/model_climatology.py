"""
Empirical Climatology baseline model.

For each day, computes P(flare | x1, x2) using a conditional probability lookup table:
  x1 = consecutive flare-free days (binned: 0,1,...,20,>20)
  x2 = sunspot number (binned: 0,10,...,200,>200)

Monthly retraining with expanding window:
  For each month's forecasts, train only on all prior months.
  First used starting January 1998 (after 17-month buffer Aug 1996 - Dec 1997).

Formula: P_clim(y=1 | x1 in b1, x2 in b2) = N_flare(b1, b2) / N_total(b1, b2)
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metrics import compute_all_metrics, threshold_predictions


def bin_consec_free(x1):
    """Bin consecutive flare-free days: {0, 1, ..., 20, >20}"""
    if x1 > 20:
        return 21  # represents ">20"
    return int(x1)


def bin_sunspot(x2):
    """Bin sunspot number: {0, 10, 20, ..., 200, >200}
    Each bin is a multiple of 10 (floor division).
    >200 maps to 210 (or any value > 200).
    """
    if x2 > 200:
        return 210  # represents ">200"
    return int(x2 // 10) * 10


def train_climatology_table(train_data, label_col, consec_col):
    """
    Build the climatology lookup table from training data.

    Returns:
    --------
    dict: (x1_bin, x2_bin) -> probability
    """
    # Count flares and total occurrences per bin
    flare_counts = {}
    total_counts = {}

    for _, row in train_data.iterrows():
        x1_bin = bin_consec_free(row[consec_col])
        x2_bin = bin_sunspot(row["sunspot_number"])
        key = (x1_bin, x2_bin)

        total_counts[key] = total_counts.get(key, 0) + 1
        if row[label_col] == 1:
            flare_counts[key] = flare_counts.get(key, 0) + 1

    # Compute probabilities
    table = {}
    for key in total_counts:
        n_flare = flare_counts.get(key, 0)
        n_total = total_counts[key]
        table[key] = n_flare / n_total

    return table


def predict_climatology(row, table, consec_col):
    """Look up climatology probability for a single day."""
    x1_bin = bin_consec_free(row[consec_col])
    x2_bin = bin_sunspot(row["sunspot_number"])
    key = (x1_bin, x2_bin)
    return table.get(key, 0.0)  # Default to 0 if bin not seen in training


def run_climatology(eval_df, merged_df):
    """
    Run climatology model with monthly expanding-window retraining.

    For each month in the evaluation period:
    1. Train on all data before this month
    2. Issue predictions for each day in this month
    """
    merged_df = merged_df.sort_values("date").reset_index(drop=True)
    merged_df["date"] = pd.to_datetime(merged_df["date"])
    eval_df = eval_df.copy()
    eval_df["date"] = pd.to_datetime(eval_df["date"])

    results = {}

    for flare_class in ["m", "x"]:
        label_col = f"{flare_class}_label"
        consec_col = f"{flare_class}_consec_free"

        # For each lead time (24h, 48h, 72h), climatology gives the same
        # probability since it doesn't use the forecast lead time.
        # However, we evaluate against different ground truth alignment.
        # Actually, climatology predicts P(flare on day D), which is the
        # same regardless of when we made the prediction.
        # The paper evaluates all models at each lead time using the
        # forecast issued at that lead time. For climatology, the prediction
        # for day D is the same whether issued 1, 2, or 3 days ahead.
        # But the consecutive flare-free days (x1) should be computed
        # as of the forecast issue date, not the target date.

        # Actually, re-reading the paper: for climatology, x1 and x2 are
        # computed for the target day itself. The "monthly retraining" means
        # the lookup table is retrained monthly, but x1/x2 features are for
        # the day being predicted.

        # For lead times: the same prediction is used since climatology
        # doesn't have a lead-time component. The evaluation metric
        # differences come only from the different ground truth alignment
        # in the SWPC forecasts (not applicable to climatology).

        # Wait, actually for climatology, the prediction for each lead time
        # should use features as known at forecast time:
        # - 24h ahead: features from D-1
        # - 48h ahead: features from D-2
        # - 72h ahead: features from D-3
        # But this would mean using different x1 values for different lead times.

        # The paper doesn't specify this clearly. Since persistence uses the
        # same binary label for all lead times, and climatology uses (x1, x2)
        # for the current day, let me use target-day features and see if it matches.

        for lead_days, lead_name in [(1, "24h"), (2, "48h"), (3, "72h")]:
            y_true_list = []
            y_prob_list = []

            # Get unique months in evaluation period
            eval_months = sorted(eval_df["date"].dt.to_period("M").unique())

            for month in eval_months:
                month_start = month.start_time
                month_end = month.end_time

                # Training data: all data before this month
                train_mask = merged_df["date"] < month_start
                train_data = merged_df[train_mask]

                if len(train_data) == 0:
                    continue

                # Build lookup table
                table = train_climatology_table(train_data, label_col, consec_col)

                # Predict for each day in this month that's in eval period
                month_eval = eval_df[
                    (eval_df["date"] >= month_start) &
                    (eval_df["date"] <= month_end)
                ]

                for _, row in month_eval.iterrows():
                    # Use target day's features for the lookup.
                    # The lead time variation in results comes from the fact
                    # that the training table is the same but x1 for the
                    # target day naturally differs from x1 on the issue day.
                    # However, the paper likely uses issue-day features since
                    # you can't know the target day's x1 in advance.
                    #
                    # For the forecast issued lead_days ahead:
                    # x1 on the issue day (D - lead_days) is used as the feature.
                    target_date = pd.Timestamp(row["date"])
                    feature_date = target_date - pd.Timedelta(days=lead_days)

                    # Look up the feature row from the issue date
                    feature_row = merged_df[merged_df["date"] == feature_date]
                    if len(feature_row) == 0:
                        feature_row = pd.DataFrame([row])

                    feature_row = feature_row.iloc[0]
                    prob = predict_climatology(feature_row, table, consec_col)

                    y_true_list.append(int(row[label_col]))
                    y_prob_list.append(prob)

            y_true = np.array(y_true_list)
            y_prob = np.array(y_prob_list)
            y_pred = threshold_predictions(y_prob, theta=0.5)

            metrics = compute_all_metrics(y_true, y_pred, y_prob)
            key = f"{flare_class.upper()}_{lead_name}"
            results[key] = metrics
            print(f"  Climatology {key}: Acc={metrics['Accuracy']}, F1={metrics['F1']}, "
                  f"Prec={metrics['Precision']}, Rec={metrics['Recall']}, "
                  f"Brier={metrics['Brier']}, AUC={metrics['AUC']}")

    return results


if __name__ == "__main__":
    import json

    PROC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "processed")

    eval_df = pd.read_csv(os.path.join(PROC, "evaluation_dataset.csv"))
    eval_df["date"] = pd.to_datetime(eval_df["date"])

    merged_df = pd.read_csv(os.path.join(PROC, "merged_dataset.csv"))
    merged_df["date"] = pd.to_datetime(merged_df["date"])

    print("Running Climatology model...")
    results = run_climatology(eval_df, merged_df)

    # Compare with paper
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "understand", "targets.json")) as f:
        targets = json.load(f)

    print("\n" + "=" * 80)
    print("CLIMATOLOGY: Paper vs Ours comparison")
    print("=" * 80)

    table_map = {
        "M_24h": "table_2", "M_48h": "table_3", "M_72h": "table_4",
        "X_24h": "table_5", "X_48h": "table_6", "X_72h": "table_7",
    }

    for key, table_name in table_map.items():
        paper = targets["tables"][table_name]["data"]["Climatology"]
        ours = results[key]
        print(f"\n{key} ({targets['tables'][table_name]['caption']}):")
        print(f"  {'Metric':<12} {'Paper':>8} {'Ours':>8} {'Diff':>8} {'Status':>12}")
        for metric in ["Accuracy", "Precision", "Recall", "F1", "Brier", "AUC",
                        "CSI", "POD", "FAR", "TSS", "HSS"]:
            p = paper[metric]
            o = ours[metric]
            diff = o - p
            pct = abs(diff / p * 100) if p != 0 else (0 if o == 0 else 100)
            if pct <= 1:
                status = "MATCH"
            elif pct <= 10:
                status = f"CLOSE ({pct:.1f}%)"
            else:
                status = f"DISCREPANT ({pct:.1f}%)"
            print(f"  {metric:<12} {p:>8.2f} {o:>8.2f} {diff:>+8.2f} {status:>12}")
