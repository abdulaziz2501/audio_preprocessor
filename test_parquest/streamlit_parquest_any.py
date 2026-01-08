import streamlit as st
import os
import io
import json
import pandas as pd
import soundfile as sf
import librosa
import numpy as np
import re
from multiprocessing import Pool, cpu_count

# =========================
# CONFIG
# =========================
OUTPUT_DIR = "output"
STATE_FILE = os.path.join(OUTPUT_DIR, "processed_parquets.json")
METADATA_FILE = os.path.join(OUTPUT_DIR, "metadata.csv")

TARGET_SR = 16000
THRESHOLD_SEC = 15
MAX_FILE_MB = 600  # endi 600 MB

# =========================
# UI
# =========================
st.set_page_config(page_title="Parquet Audio Processor with Segments", layout="wide")
st.title("🎧 Parquet Audio Processor with Segments")
st.write("""
Upload one or multiple parquet files.
- Each file must be < 600 MB
- Audio will be resampled to 16kHz
- Short (<15s) and long (>=15s) audio will be separated
- Metadata will be updated automatically with `segment` column
""")

uploaded_files = st.file_uploader("Upload parquet files", type=["parquet"], accept_multiple_files=True)
if not uploaded_files:
    st.stop()

# =========================
# INIT STATE
# =========================
os.makedirs(OUTPUT_DIR, exist_ok=True)

if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {"processed_files": {}, "last_global_id": -1}

if os.path.exists(METADATA_FILE):
    metadata_df = pd.read_csv(METADATA_FILE)
else:
    metadata_df = pd.DataFrame(columns=["id","audio_path","text_path","duration","split","sampling_rate","segment"])

# =========================
# CREATE FOLDERS
for split in ["short_audio", "long_audio"]:
    os.makedirs(os.path.join(OUTPUT_DIR, split, "audio"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, split, "text"), exist_ok=True)

# =========================
# TEXT SEGMENT FUNCTION
# =========================
def split_text_segments(text):
    # Split on . ! ? followed by space, remove empty segments
    segments = re.split(r'(?<=[.!?])\s+', text)
    segments = [s.strip() for s in segments if s.strip()]
    return segments if segments else [text.strip()]

# =========================
# PROCESSING FUNCTION
# =========================
def process_row(args):
    idx, row, start_id = args
    audio_bytes = row["audio"]["bytes"]
    text = row["transcription"].strip()
    audio, sr = sf.read(io.BytesIO(audio_bytes))

    if audio.ndim == 2:
        audio = audio.mean(axis=1)

    if sr != TARGET_SR:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=TARGET_SR)
        sr = TARGET_SR

    duration = librosa.get_duration(y=audio, sr=sr)
    split = "short_audio" if duration < THRESHOLD_SEC else "long_audio"
    file_id = f"sample_{start_id + idx:06d}"

    audio_path = os.path.join(OUTPUT_DIR, split, "audio", f"{file_id}.wav")
    text_path = os.path.join(OUTPUT_DIR, split, "text", f"{file_id}.txt")

    sf.write(audio_path, audio, sr)
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text)

    # Split text into segments
    segments = split_text_segments(text)

    return [{
        "id": file_id,
        "audio_path": audio_path,
        "text_path": text_path,
        "duration": round(duration,2),
        "split": split,
        "sampling_rate": sr,
        "segment": seg
    } for seg in segments]

# =========================
# PROCESS FILES
# =========================
total_added = 0
start_id = state["last_global_id"] + 1
all_records = []

for uploaded_file in uploaded_files:
    fname = uploaded_file.name
    size_mb = uploaded_file.size / (1024*1024)

    if size_mb > MAX_FILE_MB:
        st.warning(f"⚠️ File `{fname}` is too large ({size_mb:.2f} MB). Skipping.")
        continue

    if fname in state["processed_files"]:
        st.info(f"⚠️ File `{fname}` already processed. Skipping.")
        continue

    df = pd.read_parquet(uploaded_file)
    st.info(f"Processing `{fname}` with {len(df)} samples...")

    # Multiprocessing
    num_processes = max(1, cpu_count() - 1)
    pool = Pool(processes=num_processes)
    args = [(idx, row, start_id) for idx, row in df.iterrows()]
    results_nested = pool.map(process_row, args)
    pool.close()
    pool.join()

    # Flatten results (each audio can return multiple segments)
    results = [item for sublist in results_nested for item in sublist]

    # Update metadata
    metadata_df = pd.concat([metadata_df, pd.DataFrame(results)], ignore_index=True)
    metadata_df.to_csv(METADATA_FILE, index=False)

    # Update state
    state["processed_files"][fname] = start_id + len(df) - 1
    state["last_global_id"] = start_id + len(df) - 1
    start_id = state["last_global_id"] + 1

    total_added += len(df)
    st.success(f"✅ Finished `{fname}`: {len(df)} audio files added with segments.")

# Save state
with open(STATE_FILE, "w") as f:
    json.dump(state, f, indent=2)

st.info(f"📦 Total new audio added from all files: {total_added}")
st.info(f"🔢 Last global audio ID: {state['last_global_id']}")
st.info("📄 Metadata updated in `metadata.csv` with `segment` column")
