"""
Unit tests for metrics module.
Tests each metric against hand-calculated values.
"""

import sys
import os
import numpy as np

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metrics import (
    confusion_matrix_counts, accuracy, precision, recall,
    false_alarm_ratio, false_positive_rate, f1_score,
    critical_success_index, true_skill_statistic, heidke_skill_score,
    brier_score, auc_score, compute_all_metrics, threshold_predictions
)


def test_confusion_matrix():
    """Test basic confusion matrix computation."""
    y_true = [1, 1, 0, 0, 1, 0, 1, 0]
    y_pred = [1, 0, 0, 1, 1, 0, 0, 1]
    TP, FP, TN, FN = confusion_matrix_counts(y_true, y_pred)
    assert TP == 2, f"TP: expected 2, got {TP}"
    assert FP == 2, f"FP: expected 2, got {FP}"
    assert TN == 2, f"TN: expected 2, got {TN}"
    assert FN == 2, f"FN: expected 2, got {FN}"
    print("  confusion_matrix: PASS")


def test_accuracy():
    """Accuracy = (TP+TN) / total = (2+2)/8 = 0.5"""
    y_true = [1, 1, 0, 0, 1, 0, 1, 0]
    y_pred = [1, 0, 0, 1, 1, 0, 0, 1]
    assert abs(accuracy(y_true, y_pred) - 0.5) < 1e-10
    print("  accuracy: PASS")


def test_precision():
    """Precision = TP/(TP+FP) = 2/(2+2) = 0.5"""
    y_true = [1, 1, 0, 0, 1, 0, 1, 0]
    y_pred = [1, 0, 0, 1, 1, 0, 0, 1]
    assert abs(precision(y_true, y_pred) - 0.5) < 1e-10
    print("  precision: PASS")


def test_recall():
    """Recall = TP/(TP+FN) = 2/(2+2) = 0.5"""
    y_true = [1, 1, 0, 0, 1, 0, 1, 0]
    y_pred = [1, 0, 0, 1, 1, 0, 0, 1]
    assert abs(recall(y_true, y_pred) - 0.5) < 1e-10
    print("  recall: PASS")


def test_far():
    """FAR = FP/(TP+FP) = 2/(2+2) = 0.5"""
    y_true = [1, 1, 0, 0, 1, 0, 1, 0]
    y_pred = [1, 0, 0, 1, 1, 0, 0, 1]
    assert abs(false_alarm_ratio(y_true, y_pred) - 0.5) < 1e-10
    print("  FAR: PASS")


def test_fpr():
    """FPR = FP/(FP+TN) = 2/(2+2) = 0.5"""
    y_true = [1, 1, 0, 0, 1, 0, 1, 0]
    y_pred = [1, 0, 0, 1, 1, 0, 0, 1]
    assert abs(false_positive_rate(y_true, y_pred) - 0.5) < 1e-10
    print("  FPR: PASS")


def test_f1():
    """F1 = 2*TP/(2*TP+FP+FN) = 4/(4+2+2) = 0.5"""
    y_true = [1, 1, 0, 0, 1, 0, 1, 0]
    y_pred = [1, 0, 0, 1, 1, 0, 0, 1]
    assert abs(f1_score(y_true, y_pred) - 0.5) < 1e-10
    print("  F1: PASS")


def test_csi():
    """CSI = TP/(TP+FP+FN) = 2/(2+2+2) = 1/3"""
    y_true = [1, 1, 0, 0, 1, 0, 1, 0]
    y_pred = [1, 0, 0, 1, 1, 0, 0, 1]
    assert abs(critical_success_index(y_true, y_pred) - 1/3) < 1e-10
    print("  CSI: PASS")


def test_tss():
    """TSS = TPR - FPR = 0.5 - 0.5 = 0.0"""
    y_true = [1, 1, 0, 0, 1, 0, 1, 0]
    y_pred = [1, 0, 0, 1, 1, 0, 0, 1]
    assert abs(true_skill_statistic(y_true, y_pred) - 0.0) < 1e-10
    print("  TSS: PASS")


def test_hss():
    """HSS = 2(TP*TN-FN*FP)/((TP+FN)(FN+TN)+(TP+FP)(FP+TN))
    = 2*(4-4)/((4)(4)+(4)(4)) = 0/32 = 0.0"""
    y_true = [1, 1, 0, 0, 1, 0, 1, 0]
    y_pred = [1, 0, 0, 1, 1, 0, 0, 1]
    assert abs(heidke_skill_score(y_true, y_pred) - 0.0) < 1e-10
    print("  HSS: PASS")


def test_brier():
    """Brier = mean((p-y)^2)"""
    y_true = [1, 0, 1, 0]
    y_prob = [0.9, 0.1, 0.8, 0.2]
    # (0.01 + 0.01 + 0.04 + 0.04) / 4 = 0.1 / 4 = 0.025
    expected = (0.01 + 0.01 + 0.04 + 0.04) / 4
    assert abs(brier_score(y_true, y_prob) - expected) < 1e-10
    print("  Brier: PASS")


def test_brier_binary():
    """Brier with binary predictions (persistence model)."""
    y_true = [1, 0, 1, 0]
    y_prob = [1, 0, 0, 1]
    # (0 + 0 + 1 + 1) / 4 = 0.5
    assert abs(brier_score(y_true, y_prob) - 0.5) < 1e-10
    print("  Brier (binary): PASS")


def test_auc():
    """AUC for a simple case."""
    y_true = [1, 1, 0, 0]
    y_prob = [0.9, 0.7, 0.3, 0.1]
    # Perfect separation -> AUC = 1.0
    assert abs(auc_score(y_true, y_prob) - 1.0) < 1e-10
    print("  AUC (perfect): PASS")

    # Random -> AUC ~ 0.5
    y_true2 = [1, 0, 1, 0]
    y_prob2 = [0.5, 0.5, 0.5, 0.5]
    assert abs(auc_score(y_true2, y_prob2) - 0.5) < 1e-10
    print("  AUC (random): PASS")


def test_threshold():
    """Test threshold function."""
    y_prob = [0.1, 0.3, 0.5, 0.7, 0.9]
    y_pred = threshold_predictions(y_prob, theta=0.5)
    expected = [0, 0, 1, 1, 1]
    assert list(y_pred) == expected, f"Expected {expected}, got {list(y_pred)}"
    print("  threshold: PASS")


def test_perfect_predictions():
    """All metrics for perfect predictions."""
    y_true = [1, 1, 0, 0, 1]
    y_pred = [1, 1, 0, 0, 1]
    assert accuracy(y_true, y_pred) == 1.0
    assert precision(y_true, y_pred) == 1.0
    assert recall(y_true, y_pred) == 1.0
    assert f1_score(y_true, y_pred) == 1.0
    assert critical_success_index(y_true, y_pred) == 1.0
    assert true_skill_statistic(y_true, y_pred) == 1.0
    assert heidke_skill_score(y_true, y_pred) == 1.0
    assert false_alarm_ratio(y_true, y_pred) == 0.0
    assert false_positive_rate(y_true, y_pred) == 0.0
    assert brier_score(y_true, y_pred) == 0.0
    print("  perfect predictions: PASS")


def test_all_negative_predictions():
    """All predicted 0 (never-predict-flare model)."""
    y_true = [1, 0, 0, 0, 1]
    y_pred = [0, 0, 0, 0, 0]
    # TP=0, FP=0, TN=3, FN=2
    assert accuracy(y_true, y_pred) == 3/5
    assert precision(y_true, y_pred) == 0.0  # 0/(0+0) -> 0
    assert recall(y_true, y_pred) == 0.0  # 0/(0+2) -> 0
    assert f1_score(y_true, y_pred) == 0.0
    assert critical_success_index(y_true, y_pred) == 0.0
    # TSS = 0 - 0 = 0
    assert true_skill_statistic(y_true, y_pred) == 0.0
    print("  all-negative: PASS")


def test_asymmetric_case():
    """Non-trivial case with known hand-calculated values."""
    # TP=3, FP=1, TN=4, FN=2
    y_true = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    y_pred = [1, 1, 1, 0, 0, 1, 0, 0, 0, 0]

    TP, FP, TN, FN = confusion_matrix_counts(y_true, y_pred)
    assert (TP, FP, TN, FN) == (3, 1, 4, 2)

    assert abs(accuracy(y_true, y_pred) - 7/10) < 1e-10
    assert abs(precision(y_true, y_pred) - 3/4) < 1e-10
    assert abs(recall(y_true, y_pred) - 3/5) < 1e-10
    assert abs(f1_score(y_true, y_pred) - 6/9) < 1e-10  # 2*3/(6+1+2) = 6/9
    assert abs(critical_success_index(y_true, y_pred) - 3/6) < 1e-10  # 3/(3+1+2) = 0.5
    assert abs(false_alarm_ratio(y_true, y_pred) - 1/4) < 1e-10
    assert abs(false_positive_rate(y_true, y_pred) - 1/5) < 1e-10

    # TSS = 3/5 - 1/5 = 2/5 = 0.4
    assert abs(true_skill_statistic(y_true, y_pred) - 0.4) < 1e-10

    # HSS = 2*(3*4-2*1)/((5)(6)+(4)(5)) = 2*(12-2)/(30+20) = 20/50 = 0.4
    assert abs(heidke_skill_score(y_true, y_pred) - 0.4) < 1e-10

    print("  asymmetric case: PASS")


def test_compute_all():
    """Test compute_all_metrics returns all expected keys."""
    y_true = [1, 0, 1, 0]
    y_pred = [1, 0, 0, 1]
    y_prob = [0.8, 0.2, 0.3, 0.7]

    result = compute_all_metrics(y_true, y_pred, y_prob)
    expected_keys = {"Accuracy", "Precision", "Recall", "F1", "Brier", "AUC",
                     "CSI", "POD", "FAR", "TSS", "HSS"}
    assert set(result.keys()) == expected_keys
    assert result["POD"] == result["Recall"]
    print("  compute_all: PASS")


if __name__ == "__main__":
    print("Running metrics unit tests...")
    test_confusion_matrix()
    test_accuracy()
    test_precision()
    test_recall()
    test_far()
    test_fpr()
    test_f1()
    test_csi()
    test_tss()
    test_hss()
    test_brier()
    test_brier_binary()
    test_auc()
    test_threshold()
    test_perfect_predictions()
    test_all_negative_predictions()
    test_asymmetric_case()
    test_compute_all()
    print("\nAll tests passed!")
