import numpy as np
from sklearn.metrics import (
    roc_auc_score, average_precision_score,
    f1_score, balanced_accuracy_score,
    confusion_matrix, log_loss
)

def eval_binary(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5):
    from sklearn.metrics import accuracy_score
    y_pred = (y_prob >= threshold).astype(int)
    out = {}
    out["roc_auc"] = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else float("nan")
    out["pr_auc"] = float(average_precision_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else float("nan")
    out["macro_f1"] = float(f1_score(y_true, y_pred, average="macro"))
    out["weighted_f1"] = float(f1_score(y_true, y_pred, average="weighted"))
    out["balanced_acc"] = float(balanced_accuracy_score(y_true, y_pred))
    out["logloss"] = float(log_loss(y_true, np.clip(y_prob, 1e-6, 1-1e-6)))
    out["confusion_matrix"] = confusion_matrix(y_true, y_pred).tolist()
    out["accuracy"] = float(accuracy_score(y_true, y_pred))
    return out

def best_threshold_by_f1(y_true, y_prob):
    thresholds = np.linspace(0.05, 0.95, 19)
    best_t, best_f1 = 0.5, -1
    for t in thresholds:
        f1 = f1_score(y_true, (y_prob >= t).astype(int), average="macro")
        if f1 > best_f1:
            best_f1 = f1
            best_t = float(t)
    return best_t, float(best_f1)