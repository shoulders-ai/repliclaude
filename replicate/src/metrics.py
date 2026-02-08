"""
Evaluation metrics for solar flare forecast verification.
Implements all 11 metrics from Camporeale & Berger (2025), Section 3.1.

All metrics operate on binary predictions/observations or probabilistic forecasts.
Confusion matrix convention:
  TP = True Positive (predicted 1, observed 1)
  FP = False Positive (predicted 1, observed 0)
  TN = True Negative (predicted 0, observed 0)
  FN = False Negative (predicted 0, observed 1)
"""

import numpy as np
from sklearn.metrics import roc_auc_score


def confusion_matrix_counts(y_true, y_pred):
    """Compute TP, FP, TN, FN from binary arrays."""
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    TP = int(np.sum((y_true == 1) & (y_pred == 1)))
    FP = int(np.sum((y_true == 0) & (y_pred == 1)))
    TN = int(np.sum((y_true == 0) & (y_pred == 0)))
    FN = int(np.sum((y_true == 1) & (y_pred == 0)))
    return TP, FP, TN, FN


def accuracy(y_true, y_pred):
    """Accuracy = (TP + TN) / (TP + FP + TN + FN)"""
    TP, FP, TN, FN = confusion_matrix_counts(y_true, y_pred)
    total = TP + FP + TN + FN
    return (TP + TN) / total if total > 0 else 0.0


def precision(y_true, y_pred):
    """Precision = TP / (TP + FP)"""
    TP, FP, TN, FN = confusion_matrix_counts(y_true, y_pred)
    denom = TP + FP
    return TP / denom if denom > 0 else 0.0


def recall(y_true, y_pred):
    """Recall (POD) = TP / (TP + FN)"""
    TP, FP, TN, FN = confusion_matrix_counts(y_true, y_pred)
    denom = TP + FN
    return TP / denom if denom > 0 else 0.0


def false_alarm_ratio(y_true, y_pred):
    """FAR = FP / (TP + FP) = 1 - Precision"""
    TP, FP, TN, FN = confusion_matrix_counts(y_true, y_pred)
    denom = TP + FP
    return FP / denom if denom > 0 else 0.0


def false_positive_rate(y_true, y_pred):
    """FPR = FP / (FP + TN)"""
    TP, FP, TN, FN = confusion_matrix_counts(y_true, y_pred)
    denom = FP + TN
    return FP / denom if denom > 0 else 0.0


def f1_score(y_true, y_pred):
    """F1 = 2*TP / (2*TP + FP + FN)"""
    TP, FP, TN, FN = confusion_matrix_counts(y_true, y_pred)
    denom = 2 * TP + FP + FN
    return (2 * TP) / denom if denom > 0 else 0.0


def critical_success_index(y_true, y_pred):
    """CSI = TP / (TP + FP + FN)"""
    TP, FP, TN, FN = confusion_matrix_counts(y_true, y_pred)
    denom = TP + FP + FN
    return TP / denom if denom > 0 else 0.0


def true_skill_statistic(y_true, y_pred):
    """TSS = TP/(TP+FN) - FP/(FP+TN)"""
    TP, FP, TN, FN = confusion_matrix_counts(y_true, y_pred)
    tpr = TP / (TP + FN) if (TP + FN) > 0 else 0.0
    fpr = FP / (FP + TN) if (FP + TN) > 0 else 0.0
    return tpr - fpr


def heidke_skill_score(y_true, y_pred):
    """HSS = 2(TP*TN - FN*FP) / ((TP+FN)(FN+TN) + (TP+FP)(FP+TN))"""
    TP, FP, TN, FN = confusion_matrix_counts(y_true, y_pred)
    numer = 2 * (TP * TN - FN * FP)
    denom = (TP + FN) * (FN + TN) + (TP + FP) * (FP + TN)
    return numer / denom if denom > 0 else 0.0


def brier_score(y_true, y_prob):
    """Brier Score = (1/N) * sum((p_i - y_i)^2). Lower is better."""
    y_true = np.asarray(y_true, dtype=float)
    y_prob = np.asarray(y_prob, dtype=float)
    return float(np.mean((y_prob - y_true) ** 2))


def auc_score(y_true, y_prob):
    """Area Under the ROC Curve. Uses sklearn implementation."""
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    # Handle edge cases: if all same class, AUC is undefined
    if len(np.unique(y_true)) < 2:
        return 0.5  # Undefined, return 0.5 by convention
    return float(roc_auc_score(y_true, y_prob))


def compute_all_metrics(y_true, y_pred, y_prob=None):
    """
    Compute all 11 metrics at once.

    Parameters:
    -----------
    y_true : array-like
        Binary ground truth labels (0 or 1)
    y_pred : array-like
        Binary predictions (0 or 1), obtained by thresholding y_prob
    y_prob : array-like, optional
        Probabilistic predictions [0, 1]. Required for Brier and AUC.
        If None, y_pred is used as the probability (for deterministic models).

    Returns:
    --------
    dict with keys: Accuracy, Precision, Recall, F1, Brier, AUC, CSI, POD, FAR, TSS, HSS
    """
    if y_prob is None:
        y_prob = np.asarray(y_pred, dtype=float)

    return {
        "Accuracy": round(accuracy(y_true, y_pred), 2),
        "Precision": round(precision(y_true, y_pred), 2),
        "Recall": round(recall(y_true, y_pred), 2),
        "F1": round(f1_score(y_true, y_pred), 2),
        "Brier": round(brier_score(y_true, y_prob), 2),
        "AUC": round(auc_score(y_true, y_prob), 2),
        "CSI": round(critical_success_index(y_true, y_pred), 2),
        "POD": round(recall(y_true, y_pred), 2),  # Same as Recall
        "FAR": round(false_alarm_ratio(y_true, y_pred), 2),
        "TSS": round(true_skill_statistic(y_true, y_pred), 2),
        "HSS": round(heidke_skill_score(y_true, y_pred), 2),
    }


def threshold_predictions(y_prob, theta=0.5):
    """Convert probabilistic predictions to binary using threshold theta.
    Prediction is 1 if y_prob >= theta, else 0.
    Note: uses >= (greater than or equal) following standard convention.
    """
    return (np.asarray(y_prob) >= theta).astype(int)
