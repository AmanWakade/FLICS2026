import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# -----------------------
# Config
# -----------------------
DATA_PATH = Path("data/kidney_fl_5centers_dataset.csv")  # <-- your 48k dataset
OUTDIR = Path("prepared")
CLIENT_DIR = OUTDIR / "clients"
OUTDIR.mkdir(exist_ok=True)
CLIENT_DIR.mkdir(exist_ok=True)

SEED = 42
TEST_SIZE = 0.20          # 20% test
VAL_SIZE_OF_TRAIN = 0.10  # 10% of remaining train (i.e., 8% of total)
LABEL_COL = "label_fail_1y"
CENTER_COL = "client_center"

# -----------------------
# Load
# -----------------------
df = pd.read_csv(DATA_PATH)
assert LABEL_COL in df.columns and CENTER_COL in df.columns, "Missing label or client_center columns."

centers = sorted(df[CENTER_COL].unique().tolist())
print("Centers:", centers)
print("Total rows:", len(df), "Positive rate:", df[LABEL_COL].mean())

# -----------------------
# Per-center stratified splits
# -----------------------
manifest = {
    "data_path": str(DATA_PATH),
    "seed": SEED,
    "test_size": TEST_SIZE,
    "val_size_of_train": VAL_SIZE_OF_TRAIN,
    "centers": [],
}

all_train_parts = []
all_val_parts = []
all_test_parts = []

rng = np.random.default_rng(SEED)

for i, c in enumerate(centers):
    cdf = df[df[CENTER_COL] == c].copy()

    # Optional shuffle before splitting (not required but fine)
    idx = np.arange(len(cdf))
    rng.shuffle(idx)
    cdf = cdf.iloc[idx].reset_index(drop=True)

    # 1) Train+Val vs Test
    trainval, test = train_test_split(
        cdf,
        test_size=TEST_SIZE,
        random_state=SEED,
        stratify=cdf[LABEL_COL],
    )

    # 2) Train vs Val (val is a fraction of trainval)
    train, val = train_test_split(
        trainval,
        test_size=VAL_SIZE_OF_TRAIN,
        random_state=SEED,
        stratify=trainval[LABEL_COL],
    )

    # Save
    train_path = CLIENT_DIR / f"client_{i}_train.csv"
    val_path = CLIENT_DIR / f"client_{i}_val.csv"
    test_path = CLIENT_DIR / f"client_{i}_test.csv"

    train.to_csv(train_path, index=False)
    val.to_csv(val_path, index=False)
    test.to_csv(test_path, index=False)

    # Collect for global splits too
    all_train_parts.append(train)
    all_val_parts.append(val)
    all_test_parts.append(test)

    stats = {
        "client_id": i,
        "center_code": str(c),
        "n_total": int(len(cdf)),
        "n_train": int(len(train)),
        "n_val": int(len(val)),
        "n_test": int(len(test)),
        "pos_rate_total": float(cdf[LABEL_COL].mean()),      #  pos is the % of patients with graft failure in that center (overall)
        "pos_rate_train": float(train[LABEL_COL].mean()),    #  % of failures in the training set
        "pos_rate_val": float(val[LABEL_COL].mean()),        #  % of failures in the validation set
        "pos_rate_test": float(test[LABEL_COL].mean()),      #  % of failures in the test set 
        "files": {
            "train": str(train_path),
            "val": str(val_path),
            "test": str(test_path),
        },
    }
    manifest["centers"].append(stats)

    print(f"[client_{i}] center={c} total={len(cdf)} train={len(train)} val={len(val)} test={len(test)} "
          f"pos={stats['pos_rate_total']:.3f}")

# -----------------------
# Global combined splits (for centralized baseline)
# -----------------------
global_train = pd.concat(all_train_parts, ignore_index=True)
global_val = pd.concat(all_val_parts, ignore_index=True)
global_test = pd.concat(all_test_parts, ignore_index=True)

global_train.to_csv(OUTDIR / "global_train.csv", index=False)
global_val.to_csv(OUTDIR / "global_val.csv", index=False)
global_test.to_csv(OUTDIR / "global_test.csv", index=False)

manifest["global"] = {
    "train": str(OUTDIR / "global_train.csv"),
    "val": str(OUTDIR / "global_val.csv"),
    "test": str(OUTDIR / "global_test.csv"),
    "n_train": int(len(global_train)),
    "n_val": int(len(global_val)),
    "n_test": int(len(global_test)),
    "pos_rate_train": float(global_train[LABEL_COL].mean()),
    "pos_rate_val": float(global_val[LABEL_COL].mean()),
    "pos_rate_test": float(global_test[LABEL_COL].mean()),
}

with open(OUTDIR / "manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

print("\nSaved:")
print("-", OUTDIR / "manifest.json")
print("-", OUTDIR / "global_train.csv")
print("-", OUTDIR / "global_val.csv")
print("-", OUTDIR / "global_test.csv")
print("-", CLIENT_DIR / "client_0_train.csv ... client_4_test.csv")