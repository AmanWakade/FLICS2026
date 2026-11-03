import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import roc_curve, precision_recall_curve
import shap
import matplotlib.pyplot as plt

from metrics import eval_binary, best_threshold_by_f1
from model import MLP

# --------------------
# Paths
# --------------------

DATA_DIR = Path("prepared")

TRAIN_PATH = DATA_DIR / "global_train.csv"
VAL_PATH = DATA_DIR / "global_val.csv"
TEST_PATH = DATA_DIR / "global_test.csv"

OUT_DIR = Path("results/centralised")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------
# Columns
# --------------------

CAT_COLS = ["GENDER", "ON_DIALYSIS", "DON_TY"]

NUM_COLS = [
    "AGE", "ETHNICITY", "BMI_TCR", "DIAB",
    "CURRENT_PRA", "DAYSWAIT_CHRON",
    "AGE_DON", "KDPI", "CREAT_DON", "COLD_ISCH_KI", "DISTANCE"
]

LABEL_COL = "label_fail_1y"

# --------------------
# Load data
# --------------------

train_df = pd.read_csv(TRAIN_PATH)
val_df = pd.read_csv(VAL_PATH)
test_df = pd.read_csv(TEST_PATH)

# --------------------
# Encoding
# --------------------

ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
scaler = StandardScaler()

# Encode categorical
X_cat_train = ohe.fit_transform(train_df[CAT_COLS].astype(str))
X_cat_val = ohe.transform(val_df[CAT_COLS].astype(str))
X_cat_test = ohe.transform(test_df[CAT_COLS].astype(str))

# Clean numeric %
for d in (train_df, val_df, test_df):
    d[NUM_COLS] = d[NUM_COLS].replace('%', '', regex=True)

# Convert to numeric safely
for col in NUM_COLS:
    train_df[col] = pd.to_numeric(train_df[col], errors="coerce")
    val_df[col] = pd.to_numeric(val_df[col], errors="coerce")
    test_df[col] = pd.to_numeric(test_df[col], errors="coerce")

# Fill missing using TRAIN medians only
train_medians = train_df[NUM_COLS].median(numeric_only=True)
train_df[NUM_COLS] = train_df[NUM_COLS].fillna(train_medians)
val_df[NUM_COLS] = val_df[NUM_COLS].fillna(train_medians)
test_df[NUM_COLS] = test_df[NUM_COLS].fillna(train_medians)

# Scale
X_num_train = scaler.fit_transform(train_df[NUM_COLS])
X_num_val = scaler.transform(val_df[NUM_COLS])
X_num_test = scaler.transform(test_df[NUM_COLS])

# Combine numeric + categorical
X_train = np.concatenate([X_num_train, X_cat_train], axis=1).astype(np.float32)
X_val = np.concatenate([X_num_val, X_cat_val], axis=1).astype(np.float32)
X_test = np.concatenate([X_num_test, X_cat_test], axis=1).astype(np.float32)

# Labels
y_train = train_df[LABEL_COL].values
y_val = val_df[LABEL_COL].values
y_test = test_df[LABEL_COL].values

# Feature names for SHAP
cat_feature_names = ohe.get_feature_names_out(CAT_COLS).tolist()
feature_names = NUM_COLS + cat_feature_names

# --------------------
# Torch datasets
# --------------------

train_loader = DataLoader(
    TensorDataset(
        torch.tensor(X_train, dtype=torch.float32),
        torch.tensor(y_train, dtype=torch.float32)
    ),
    batch_size=1024,
    shuffle=True
)

val_tensor = torch.tensor(X_val, dtype=torch.float32)
test_tensor = torch.tensor(X_test, dtype=torch.float32)

# --------------------
# Model
# --------------------

model = MLP(X_train.shape[1])

optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

# Class imbalance handling
pos = (y_train == 1).sum()
neg = (y_train == 0).sum()
pos_weight = torch.tensor([neg / max(pos, 1)], dtype=torch.float32)

criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
print("pos_weight:", float(pos_weight.item()))

# --------------------
# Training
# --------------------

EPOCHS = 30

for epoch in range(EPOCHS):
    model.train()

    for xb, yb in train_loader:
        logits = model(xb)
        loss = criterion(logits, yb)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        val_logits = model(val_tensor)
        val_prob = torch.sigmoid(val_logits).cpu().numpy()

    metrics = eval_binary(y_val, val_prob)
    print(f"Epoch {epoch+1}  AUC={metrics['roc_auc']:.4f}  F1={metrics['macro_f1']:.4f}")

# --------------------
# Find best threshold
# --------------------

best_t, best_f1 = best_threshold_by_f1(y_val, val_prob)
print("Best threshold:", best_t)

# --------------------
# Final test evaluation
# --------------------

with torch.no_grad():
    test_logits = model(test_tensor)
    test_prob = torch.sigmoid(test_logits).cpu().numpy()

test_metrics = eval_binary(y_test, test_prob, threshold=best_t)

print("\nFinal Test Metrics")
print(test_metrics)

# --------------------
# Save results
# --------------------

with open(OUT_DIR / "global_eval_final.json", "w") as f:
    json.dump(test_metrics, f, indent=2)

# ROC curve points
fpr, tpr, _ = roc_curve(y_test, test_prob)
roc_df = pd.DataFrame({"fpr": fpr, "tpr": tpr})
roc_df.to_csv(OUT_DIR / "roc_points.csv", index=False)

# PR curve points
precision, recall, _ = precision_recall_curve(y_test, test_prob)
pr_df = pd.DataFrame({"recall": recall, "precision": precision})
pr_df.to_csv(OUT_DIR / "pr_points.csv", index=False)

# LaTeX coordinates
roc_coords = "\n".join([f"({x:.6f},{y:.6f})" for x, y in zip(fpr, tpr)])
pr_coords = "\n".join([f"({x:.6f},{y:.6f})" for x, y in zip(recall, precision)])

with open(OUT_DIR / "roc_coords.tex", "w") as f:
    f.write(roc_coords)

with open(OUT_DIR / "pr_coords.tex", "w") as f:
    f.write(pr_coords)

print("Saved results + ROC/PR coordinates to:", OUT_DIR)

# --------------------
# SHAP Explainability
# --------------------

print("\nRunning SHAP...")

model.eval()

def model_predict(x: np.ndarray) -> np.ndarray:
    x_tensor = torch.tensor(x, dtype=torch.float32)
    with torch.no_grad():
        probs = torch.sigmoid(model(x_tensor)).cpu().numpy().reshape(-1)
    return probs

# Use smaller samples for speed
background_size = min(200, len(X_train))
test_sample_size = min(300, len(X_test))

X_background = X_train[:background_size]
X_test_sample = X_test[:test_sample_size]

explainer = shap.Explainer(model_predict, X_background)
shap_values = explainer(X_test_sample)

# Save SHAP summary plot
plt.figure()
shap.summary_plot(
    shap_values,
    X_test_sample,
    feature_names=feature_names,
    show=False
)
plt.tight_layout()
plt.savefig(OUT_DIR / "shap_summary.png", dpi=300, bbox_inches="tight")
plt.close()

# Save mean absolute SHAP importance
shap_importance = pd.DataFrame({
    "feature": feature_names,
    "mean_abs_shap": np.abs(shap_values.values).mean(axis=0)
}).sort_values("mean_abs_shap", ascending=False)

shap_importance.to_csv(OUT_DIR / "shap_importance.csv", index=False)

print("Saved SHAP outputs to:", OUT_DIR)