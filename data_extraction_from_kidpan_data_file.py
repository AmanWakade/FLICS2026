import pandas as pd
import numpy as np
from pathlib import Path

KIDPAN_PATH = Path("KIDPAN_DATA_converted.csv")

usecols = [
    "TRR_ID_CODE", "CTR_CODE",
    "TX_DATE", "FAILDATE_KI", "RETXDATE_KI", "RESUM_MAINT_DIAL_DT", "PX_STAT", "PX_STAT_DATE",
    "TXKID", "MULTIORG",
    "AGE", "GENDER", "ETHNICITY", "BMI_TCR", "DIAB", "ON_DIALYSIS",
    "CURRENT_PRA", "DAYSWAIT_CHRON",
    "AGE_DON", "DON_TY", "KDPI", "CREAT_DON", "COLD_ISCH_KI", "DISTANCE",
]

chunks = []
print("Reading in chunks...")

for chunk in pd.read_csv(
    KIDPAN_PATH,
    usecols=usecols,
    dtype="string",
    na_values=[".", " .", "NA", "N/A", "NULL", ""],
    chunksize=100_000,   # 100k rows per chunk
    low_memory=True
):
    chunks.append(chunk)

df = pd.concat(chunks, ignore_index=True)

print("Finished loading. Rows:", len(df))

print("Unique TRR_ID_CODE:", df["TRR_ID_CODE"].nunique())
print("Missing TX_DATE:", df["TX_DATE"].isna().mean())
print("Missing CTR_CODE:", df["CTR_CODE"].isna().mean())

# Keep only transplant records
df = df[df["TX_DATE"].notna()]

# Remove multi-organ cases
df["MULTIORG"] = pd.to_numeric(df["MULTIORG"], errors="coerce")
df = df[(df["MULTIORG"].isna()) | (df["MULTIORG"] == 0)]

# Adults only
df["AGE"] = pd.to_numeric(df["AGE"], errors="coerce")
df = df[df["AGE"].isna() | (df["AGE"] >= 18)]

print("After transplant-only filters:", len(df))
print("Unique TRR after filter:", df["TRR_ID_CODE"].nunique())


# Convert date columns properly (if not already)
for c in ["TX_DATE", "FAILDATE_KI", "RETXDATE_KI", "RESUM_MAINT_DIAL_DT", "PX_STAT_DATE"]:
    df[c] = pd.to_datetime(df[c], errors="coerce")

# Build event date (Option 1 – death counts as failure)
event_dates = pd.concat(
    [
        df["FAILDATE_KI"],
        df["RETXDATE_KI"],
        df["RESUM_MAINT_DIAL_DT"],
        df["PX_STAT_DATE"],
    ],
    axis=1,
)

df["EVENT_DATE"] = event_dates.min(axis=1)
df["TX_PLUS_1Y"] = df["TX_DATE"] + pd.to_timedelta(365, unit="D")

df["label_fail_1y"] = (
    (df["EVENT_DATE"].notna()) &
    (df["EVENT_DATE"] <= df["TX_PLUS_1Y"])
).astype("int8")

print("Positive rate:", df["label_fail_1y"].mean())
print("Total failures:", df["label_fail_1y"].sum())

# Clean CTR_CODE
df["CTR_CODE"] = df["CTR_CODE"].astype("string").str.strip().str.upper()

# Remove unknowns
unknown_tokens = {"", " ", "UNKNOWN", "UNK", "NA", "N/A", "NONE", "."}
df = df[~df["CTR_CODE"].isin(unknown_tokens)]

# Count top 5 centers
top_centers = df["CTR_CODE"].value_counts().head(5)
print(top_centers)

# Filter to those centers
df = df[df["CTR_CODE"].isin(top_centers.index)].copy()
df.rename(columns={"CTR_CODE": "client_center"}, inplace=True)

print("Rows after selecting top 5 centers:", len(df))

features = [
    "AGE", "GENDER", "ETHNICITY", "BMI_TCR", "DIAB",
    "ON_DIALYSIS", "CURRENT_PRA", "DAYSWAIT_CHRON",
    "AGE_DON", "DON_TY", "KDPI", "CREAT_DON",
    "COLD_ISCH_KI", "DISTANCE"
]

df_model = df[features + ["label_fail_1y", "client_center"]].copy()

print("Model dataset shape:", df_model.shape)

OUTPUT_PATH = Path("kidney_fl_5centers_dataset.csv")

df_model.to_csv(OUTPUT_PATH, index=False)

print("Saved dataset to:", OUTPUT_PATH)