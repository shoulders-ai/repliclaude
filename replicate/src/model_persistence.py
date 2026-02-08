"""
Persistence baseline model.

For each day D, the observed flare activity (binary: M or X class occurred today)
is used as the prediction for D+1, D+2, D+3.
This is a deterministic (0/1) model -- no training required.

For probabilistic metrics (Brier, AUC), the binary output is used directly
as the "probability" (following Assumption A4).
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metrics import compute_all_metrics, threshold_predictions


def run_persistence(eval_df, merged_df):
    """
    Run persistence model on evaluation dataset.

    Parameters:
    -----------
    eval_df : DataFrame
        Evaluation period dataset (1998-2024)
    merged_df : DataFrame
        Full merged dataset including buffer (1996-2024)

    Returns:
    --------
    dict : results for M and X class at 24h, 48h, 72h
    """
    merged_df = merged_df.sort_values("date").reset_index(drop=True)
    merged_df["date"] = pd.to_datetime(merged_df["date"])

    # Create date-indexed lookup for labels
    date_to_idx = {d: i for i, d in enumerate(merged_df["date"])}

    results = {}

    for flare_class in ["m", "x"]:
        label_col = f"{flare_class}_label"

        for lead_days, lead_name in [(1, "24h"), (2, "48h"), (3, "72h")]:
            # For each evaluation day, the persistence prediction is the
            # observed label from `lead_days` days before
            y_true_list = []
            y_pred_list = []

            for _, row in eval_df.iterrows():
                target_date = pd.Timestamp(row["date"])

                # The prediction for target_date comes from observing
                # the label on (target_date - lead_days) days
                source_date = target_date - pd.Timedelta(days=lead_days)

                if source_date in date_to_idx:
                    source_idx = date_to_idx[source_date]
                    pred = int(merged_df.iloc[source_idx][label_col])
                else:
                    continue  # Skip if source date not available

                y_true_list.append(int(row[label_col]))
                y_pred_list.append(pred)

            y_true = np.array(y_true_list)
            y_pred = np.array(y_pred_list)
            # Persistence is deterministic: probability = binary prediction
            y_prob = y_pred.astype(float)

            metrics = compute_all_metrics(y_true, y_pred, y_prob)
            key = f"{flare_class.upper()}_{lead_name}"
            results[key] = metrics
            print(f"  Persistence {key}: Acc={metrics['Accuracy']}, F1={metrics['F1']}, "
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

    print("Running Persistence model...")
    results = run_persistence(eval_df, merged_df)

    # Compare with paper
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "understand", "targets.json")) as f:
        targets = json.load(f)

    print("\n" + "=" * 80)
    print("PERSISTENCE: Paper vs Ours comparison")
    print("=" * 80)

    table_map = {
        "M_24h": "table_2", "M_48h": "table_3", "M_72h": "table_4",
        "X_24h": "table_5", "X_48h": "table_6", "X_72h": "table_7",
    }

    for key, table_name in table_map.items():
        paper = targets["tables"][table_name]["data"]["Persistence"]
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
