"""
Baseline Average ensemble model.

Simple average of component model probabilities:
  M-class: avg(Climatology, Persistence, Naive Bayes, Logistic Regression) [Assumption A2]
  X-class: avg(Climatology, Persistence, Naive Bayes) — LR excluded [paper p.9-10]

This model depends on the other models' probability outputs.
"""

import os
import sys
import json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metrics import compute_all_metrics, threshold_predictions


def run_baseline_average(eval_df, merged_df, clim_probs, persist_probs, nb_probs, lr_probs):
    """
    Compute Baseline Average from component model probabilities.

    Parameters:
    -----------
    eval_df : DataFrame
    merged_df : DataFrame
    clim_probs : dict of {key: array} — probabilities from climatology
    persist_probs : dict of {key: array} — probabilities from persistence
    nb_probs : dict of {key: array} — probabilities from naive bayes
    lr_probs : dict of {key: array} — probabilities from logistic regression
    """
    results = {}

    for flare_class in ["m", "x"]:
        label_col = f"{flare_class}_label"

        for lead_name in ["24h", "48h", "72h"]:
            key = f"{flare_class.upper()}_{lead_name}"

            # Get component probabilities (matching indices)
            c = clim_probs[key]
            p = persist_probs[key]
            n = nb_probs[key]

            if flare_class == "m":
                # M-class: include LR (Assumption A2)
                l = lr_probs[key]
                avg_prob = (c + p + n + l) / 4.0
            else:
                # X-class: exclude LR
                avg_prob = (c + p + n) / 3.0

            y_true = eval_df[label_col].values[:len(avg_prob)].astype(int)
            y_pred = threshold_predictions(avg_prob, theta=0.5)

            metrics = compute_all_metrics(y_true, y_pred, avg_prob)
            results[key] = metrics
            print(f"  BA {key}: Acc={metrics['Accuracy']}, F1={metrics['F1']}, "
                  f"Prec={metrics['Precision']}, Rec={metrics['Recall']}, "
                  f"Brier={metrics['Brier']}, AUC={metrics['AUC']}")

    return results
