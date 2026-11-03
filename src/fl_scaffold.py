import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import precision_recall_curve, roc_curve
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from torch.utils.data import DataLoader, TensorDataset

from model import MLP
from metrics import eval_binary, best_threshold_by_f1

# ----------------
# Paths
# ----------------
CLIENT_DIR = Path("prepared/clients")
OUT_DIR = Path("results/scaffold")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------
# Settings
# ----------------
CLIENTS = 5
ROUNDS = 20
LOCAL_EPOCHS = 5
BATCH = 1024
LR = 1e-3
LABEL = "label_fail_1y"

CAT_COLS = ["GENDER", "ON_DIALYSIS", "DON_TY"]
NUM_COLS = [
    "AGE", "ETHNICITY", "BMI_TCR", "DIAB",
    "CURRENT_PRA", "DAYSWAIT_CHRON",
    "AGE_DON", "KDPI", "CREAT_DON", "COLD_ISCH_KI", "DISTANCE"
]


def clean_numeric(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[NUM_COLS] = df[NUM_COLS].replace("%", "", regex=True)
    for col in NUM_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


train_parts = [pd.read_csv(CLIENT_DIR / f"client_{i}_train.csv") for i in range(CLIENTS)]
combined_train = pd.concat(train_parts, ignore_index=True)
ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
ohe.fit(combined_train[CAT_COLS].astype(str))

client_loaders = []
client_sizes = []
val_sets = []
test_sets = []

for i in range(CLIENTS):
    train_df = clean_numeric(pd.read_csv(CLIENT_DIR / f"client_{i}_train.csv"))
    val_df = clean_numeric(pd.read_csv(CLIENT_DIR / f"client_{i}_val.csv"))
    test_df = clean_numeric(pd.read_csv(CLIENT_DIR / f"client_{i}_test.csv"))

    medians = train_df[NUM_COLS].median(numeric_only=True)
    scaler = StandardScaler()
    scaler.fit(train_df[NUM_COLS].fillna(medians))

    def preprocess(df: pd.DataFrame):
        X_cat = ohe.transform(df[CAT_COLS].astype(str))
        X_num = scaler.transform(df[NUM_COLS].fillna(medians))
        X = np.concatenate([X_num, X_cat], axis=1).astype(np.float32)
        y = df[LABEL].values.astype(np.float32)
        return X, y

    X_train, y_train = preprocess(train_df)
    X_val, y_val = preprocess(val_df)
    X_test, y_test = preprocess(test_df)

    loader = DataLoader(
        TensorDataset(torch.tensor(X_train), torch.tensor(y_train)),
        batch_size=BATCH,
        shuffle=True,
    )
    client_loaders.append(loader)
    client_sizes.append(len(train_df))
    val_sets.append((torch.tensor(X_val, dtype=torch.float32), y_val))
    test_sets.append((torch.tensor(X_test, dtype=torch.float32), y_test))

total_samples = sum(client_sizes)
input_dim = val_sets[0][0].shape[1]
global_model = MLP(input_dim)
criterion = nn.BCEWithLogitsLoss()

c_global = [torch.zeros_like(p) for p in global_model.parameters()]
c_clients = [[torch.zeros_like(p) for p in global_model.parameters()] for _ in range(CLIENTS)]

logs = []

for r in range(ROUNDS):
    client_states = []
    client_weights = []

    for cid, (loader, n) in enumerate(zip(client_loaders, client_sizes)):
        local_model = copy.deepcopy(global_model)
        opt = torch.optim.Adam(local_model.parameters(), lr=LR)
        local_model.train()

        for _ in range(LOCAL_EPOCHS):
            for xb, yb in loader:
                logits = local_model(xb)
                loss = criterion(logits, yb)
                opt.zero_grad()
                loss.backward()

                for param, cg, ci in zip(local_model.parameters(), c_global, c_clients[cid]):
                    param.grad += cg - ci

                opt.step()

        new_ci = []
        for p_local, p_global, ci, cg in zip(
            local_model.parameters(),
            global_model.parameters(),
            c_clients[cid],
            c_global,
        ):
            delta = p_global.data - p_local.data
            new_ci.append(ci - cg + delta / (LOCAL_EPOCHS * LR))
        c_clients[cid] = new_ci

        client_states.append(local_model.state_dict())
        client_weights.append(n / total_samples)

    new_state = {}
    for key in global_model.state_dict().keys():
        new_state[key] = sum(client_weights[i] * client_states[i][key] for i in range(CLIENTS))
    global_model.load_state_dict(new_state)

    global_model.eval()
    val_probs_all, val_y_all = [], []
    with torch.no_grad():
        for val_tensor, y_val in val_sets:
            val_prob = torch.sigmoid(global_model(val_tensor)).numpy()
            val_probs_all.append(val_prob)
            val_y_all.append(y_val)
    val_prob_all = np.concatenate(val_probs_all)
    val_y_all = np.concatenate(val_y_all)
    best_t, _ = best_threshold_by_f1(val_y_all, val_prob_all)

    test_probs_all, test_y_all = [], []
    with torch.no_grad():
        for test_tensor, y_test in test_sets:
            test_prob = torch.sigmoid(global_model(test_tensor)).numpy()
            test_probs_all.append(test_prob)
            test_y_all.append(y_test)
    test_prob_all = np.concatenate(test_probs_all)
    test_y_all = np.concatenate(test_y_all)

    metrics = eval_binary(test_y_all, test_prob_all, threshold=best_t)
    metrics["round"] = r + 1
    logs.append(metrics)

    print(f"Round {r+1} | AUC={metrics['roc_auc']:.4f} F1={metrics['macro_f1']:.4f}")

with open(OUT_DIR / "round_metrics.json", "w") as f:
    json.dump(logs, f, indent=2)
with open(OUT_DIR / "global_eval_final.json", "w") as f:
    json.dump(logs[-1], f, indent=2)

fpr, tpr, _ = roc_curve(test_y_all, test_prob_all)
roc_df = pd.DataFrame({"fpr": fpr, "tpr": tpr})
roc_df.to_csv(OUT_DIR / "roc_points.csv", index=False)

precision, recall, _ = precision_recall_curve(test_y_all, test_prob_all)
pr_df = pd.DataFrame({"recall": recall, "precision": precision})
pr_df.to_csv(OUT_DIR / "pr_points.csv", index=False)

roc_coords = "\n".join([f"({x:.6f},{y:.6f})" for x, y in zip(fpr, tpr)])
pr_coords = "\n".join([f"({x:.6f},{y:.6f})" for x, y in zip(recall, precision)])

with open(OUT_DIR / "roc_coords.tex", "w") as f:
    f.write(roc_coords)
with open(OUT_DIR / "pr_coords.tex", "w") as f:
    f.write(pr_coords)

print("Saved results + ROC/PR coordinates to:", OUT_DIR)
