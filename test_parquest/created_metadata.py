import pandas as pd
import os

# =========================
# CONFIG
# =========================
METADATA_FILE = "output/metadata.csv"  # original metadata
OUTPUT_DIR = "output"

SHORT_CSV = os.path.join(OUTPUT_DIR, "short.csv")
LONG_CSV = os.path.join(OUTPUT_DIR, "long.csv")

# =========================
# LOAD METADATA
df = pd.read_csv(METADATA_FILE)

# =========================
# SPLIT DATA
short_df = df[df["split"] == "short_audio"]
long_df = df[df["split"] == "long_audio"]

# =========================
# SAVE TO CSV
short_df.to_csv(SHORT_CSV, index=False)
long_df.to_csv(LONG_CSV, index=False)

print(f"✅ Short audio CSV saved: {SHORT_CSV} ({len(short_df)} rows)")
print(f"✅ Long audio CSV saved: {LONG_CSV} ({len(long_df)} rows)")
