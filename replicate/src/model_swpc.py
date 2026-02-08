"""
SWPC forecast evaluation.

The SWPC model is not trained - it's the system under test.
We simply evaluate the SWPC forecast probabilities against ground truth.
Forecasts are already in the evaluation dataset as integer percentages.
"""

import os
import sys
import json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metrics import compute_all_metrics, threshold_predictions


def run_swpc(eval_df):
    """
    Evaluate SWPC forecasts at theta=0.5.

    The evaluation dataset has columns:
      m_24h, m_48h, m_72h, x_24h, x_48h, x_72h (integer percentages)
      m_label, x_label (binary ground truth)
    """
    results = {}

    for flare_class in ["m", "x"]:
        label_col = f"{flare_class}_label"

        for lead_name in ["24h", "48h", "72h"]:
            prob_col = f"{flare_class}_{lead_name}"

            # Filter to days with valid forecasts
            valid = eval_df[eval_df[prob_col].notna()].copy()

            y_true = valid[label_col].values.astype(int)
            y_prob = valid[prob_col].values / 100.0  # Convert percentage to [0,1]
            y_pred = threshold_predictions(y_prob, theta=0.5)

            metrics = compute_all_metrics(y_true, y_pred, y_prob)
            key = f"{flare_class.upper()}_{lead_name}"
            results[key] = metrics
            print(f"  SWPC {key}: Acc={metrics['Accuracy']}, F1={metrics['F1']}, "
                  f"Prec={metrics['Precision']}, Rec={metrics['Recall']}, "
                  f"Brier={metrics['Brier']}, AUC={metrics['AUC']}")

    return results


if __name__ == "__main__":
    PROC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "processed")

    eval_df = pd.read_csv(os.path.join(PROC, "evaluation_dataset.csv"))
    eval_df["date"] = pd.to_datetime(eval_df["date"])

    print("Evaluating SWPC forecasts...")
    results = run_swpc(eval_df)

    # Compare with paper
    targets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "understand", "targets.json")
    with open(targets_path) as f:
        targets = json.load(f)

    print("\n" + "=" * 80)
    print("SWPC: Paper vs Ours comparison")
    print("=" * 80)

    table_map = {
        "M_24h": "table_2", "M_48h": "table_3", "M_72h": "table_4",
        "X_24h": "table_5", "X_48h": "table_6", "X_72h": "table_7",
    }

    for key, table_name in table_map.items():
        paper = targets["tables"][table_name]["data"]["SWPC"]
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
