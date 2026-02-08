"""
Naive Bayes baseline model.

P(y=1|x1,x2) = P(y=1)P(x1|y=1)P(x2|y=1) / [P(y=1)P(x1|y=1)P(x2|y=1) + P(y=0)P(x1|y=0)P(x2|y=0)]

Uses GaussianNB (continuous features) since the paper doesn't specify discretization
for NB and the paper's results (high recall, high Brier ~0.36) are consistent with
continuous Gaussian NB rather than discrete binned NB.

Features:
  x1 = consecutive flare-free days
  x2 = sunspot number

Monthly retraining with expanding window.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.naive_bayes import GaussianNB

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metrics import compute_all_metrics, threshold_predictions


def run_naive_bayes(eval_df, merged_df):
    """Run Gaussian Naive Bayes with monthly expanding-window retraining."""
    merged_df = merged_df.sort_values("date").reset_index(drop=True)
    merged_df["date"] = pd.to_datetime(merged_df["date"])
    eval_df = eval_df.copy()
    eval_df["date"] = pd.to_datetime(eval_df["date"])

    results = {}

    for flare_class in ["m", "x"]:
        label_col = f"{flare_class}_label"
        consec_col = f"{flare_class}_consec_free"

        for lead_days, lead_name in [(1, "24h"), (2, "48h"), (3, "72h")]:
            y_true_list = []
            y_prob_list = []

            eval_months = sorted(eval_df["date"].dt.to_period("M").unique())

            for month in eval_months:
                month_start = month.start_time
                month_end = month.end_time

                train_mask = merged_df["date"] < month_start
                train_data = merged_df[train_mask].dropna(subset=[consec_col, "sunspot_number"])

                if len(train_data) == 0 or train_data[label_col].nunique() < 2:
                    continue

                X_train = train_data[[consec_col, "sunspot_number"]].values
                y_train = train_data[label_col].values.astype(int)

                gnb = GaussianNB()
                gnb.fit(X_train, y_train)

                month_eval = eval_df[
                    (eval_df["date"] >= month_start) &
                    (eval_df["date"] <= month_end)
                ]

                for _, row in month_eval.iterrows():
                    target_date = pd.Timestamp(row["date"])
                    feature_date = target_date - pd.Timedelta(days=lead_days)
                    fr = merged_df[merged_df["date"] == feature_date]
                    if len(fr) == 0:
                        continue
                    feature_row = fr.iloc[0]

                    X = np.array([[feature_row[consec_col], feature_row["sunspot_number"]]])
                    prob = gnb.predict_proba(X)[0, 1]

                    y_true_list.append(int(row[label_col]))
                    y_prob_list.append(prob)

            y_true = np.array(y_true_list)
            y_prob = np.array(y_prob_list)
            y_pred = threshold_predictions(y_prob, theta=0.5)

            metrics = compute_all_metrics(y_true, y_pred, y_prob)
            key = f"{flare_class.upper()}_{lead_name}"
            results[key] = metrics
            print(f"  NB {key}: Acc={metrics['Accuracy']}, F1={metrics['F1']}, "
                  f"Prec={metrics['Precision']}, Rec={metrics['Recall']}, "
                  f"Brier={metrics['Brier']}, AUC={metrics['AUC']}")

    return results


if __name__ == "__main__":
    PROC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "processed")

    eval_df = pd.read_csv(os.path.join(PROC, "evaluation_dataset.csv"))
    eval_df["date"] = pd.to_datetime(eval_df["date"])

    merged_df = pd.read_csv(os.path.join(PROC, "merged_dataset.csv"))
    merged_df["date"] = pd.to_datetime(merged_df["date"])

    print("Running Naive Bayes model...")
    results = run_naive_bayes(eval_df, merged_df)

    targets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "understand", "targets.json")
    with open(targets_path) as f:
        targets = json.load(f)

    print("\n" + "=" * 80)
    print("NAIVE BAYES: Paper vs Ours comparison")
    print("=" * 80)

    table_map = {
        "M_24h": "table_2", "M_48h": "table_3", "M_72h": "table_4",
        "X_24h": "table_5", "X_48h": "table_6", "X_72h": "table_7",
    }

    for key, table_name in table_map.items():
        paper = targets["tables"][table_name]["data"]["Naive_Bayes"]
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
