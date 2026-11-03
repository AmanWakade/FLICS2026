import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CAT_COLS = ["GENDER", "ON_DIALYSIS", "DON_TY"]
NUM_COLS = [
    "AGE", "ETHNICITY", "BMI_TCR", "DIAB",
    "CURRENT_PRA", "DAYSWAIT_CHRON",
    "AGE_DON", "KDPI", "CREAT_DON", "COLD_ISCH_KI", "DISTANCE",
]
# Note: DIAB is numeric but fine to keep numeric; ETHNICITY is coded numeric.

LABEL_COL = "label_fail_1y"
CENTER_COL = "client_center"


def set_seed(seed: int):
    import random
    import os
    import torch

    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def load_df(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def split_by_center(df: pd.DataFrame, seed: int, test_size: float, val_size: float):
    # Split within each center to preserve distribution
    splits = {}
    centers = sorted(df[CENTER_COL].unique().tolist())
    for c in centers:
        cdf = df[df[CENTER_COL] == c].copy()
        trainval, test = train_test_split(
            cdf, test_size=test_size, random_state=seed, stratify=cdf[LABEL_COL]
        )
        train, val = train_test_split(
            trainval, test_size=val_size, random_state=seed, stratify=trainval[LABEL_COL]
        )
        splits[c] = {"train": train, "val": val, "test": test}
    return splits


def clean_numeric(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[NUM_COLS] = df[NUM_COLS].replace("%", "", regex=True)
    for col in NUM_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def fit_ohe(reference_df: pd.DataFrame) -> OneHotEncoder:
    ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    ohe.fit(reference_df[CAT_COLS].astype(str))
    return ohe


def fit_client_transformers(client_train: pd.DataFrame, ohe: OneHotEncoder):
    client_train = clean_numeric(client_train)
    scaler = StandardScaler()
    medians = client_train[NUM_COLS].median(numeric_only=True)
    scaler.fit(client_train[NUM_COLS].fillna(medians))
    return ohe, scaler, medians


def transform(df: pd.DataFrame, ohe: OneHotEncoder, scaler: StandardScaler, medians: pd.Series):
    df = clean_numeric(df)
    X_cat = ohe.transform(df[CAT_COLS].astype(str))
    X_num = scaler.transform(df[NUM_COLS].fillna(medians))
    X = np.concatenate([X_num, X_cat], axis=1).astype(np.float32)
    y = df[LABEL_COL].astype(int).to_numpy()
    return X, y


def save_run_meta(outdir: Path, cfg):
    outdir.mkdir(parents=True, exist_ok=True)
    with open(outdir / "config.json", "w") as f:
        json.dump(asdict(cfg), f, indent=2, default=str)
