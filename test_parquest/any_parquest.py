import os
import io
import json
import pandas as pd
import soundfile as sf
import librosa

# ======================
# CONFIG
# ======================
PARQUET_PATH = "data/0002.parquet"
PARQUET_NAME = os.path.basename(PARQUET_PATH)

OUTPUT_DIR = "output"
STATE_FILE = os.path.join(OUTPUT_DIR, "processed_parquets.json")
THRESHOLD_SEC = 15

# ======================
# LOAD / INIT STATE
# ======================
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {
        "processed_files": {},
        "last_global_id": -1
    }

# ======================
# CHECK DUPLICATE PARQUET
# ======================
if PARQUET_NAME in state["processed_files"]:
    print(f"⚠️ Parquet already processed: {PARQUET_NAME}")
    print("No new audio added.")
    exit(0)

# ======================
# LOAD DATA
# ======================
df = pd.read_parquet(PARQUET_PATH)
print("Total samples in parquet:", len(df))

# ======================
# CREATE FOLDERS
# ======================
for split in ["short_audio", "long_audio"]:
    os.makedirs(os.path.join(OUTPUT_DIR, split, "audio"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, split, "text"), exist_ok=True)

# ======================
# PROCESS
# ======================
added_count = 0
current_id = state["last_global_id"] + 1

for _, row in df.iterrows():

    audio_bytes = row["audio"]["bytes"]
    text = row["transcription"].strip()

    audio_array, sr = sf.read(io.BytesIO(audio_bytes))

    # mono qilish (STT uchun tavsiya)
    if audio_array.ndim == 2:
        audio_array = audio_array.mean(axis=1)

    duration = librosa.get_duration(y=audio_array, sr=sr)

    split = "short_audio" if duration < THRESHOLD_SEC else "long_audio"

    file_id = f"sample_{current_id:06d}"

    audio_path = os.path.join(OUTPUT_DIR, split, "audio", f"{file_id}.wav")
    text_path = os.path.join(OUTPUT_DIR, split, "text", f"{file_id}.txt")

    sf.write(audio_path, audio_array, sr)

    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text)

    current_id += 1
    added_count += 1

# ======================
# UPDATE STATE
# ======================
state["processed_files"][PARQUET_NAME] = current_id - 1
state["last_global_id"] = current_id - 1

with open(STATE_FILE, "w") as f:
    json.dump(state, f, indent=2)

# ======================
# INFO
# ======================
print("✅ Processing completed")
print(f"📦 Parquet processed: {PARQUET_NAME}")
print(f"➕ New audio added: {added_count}")
print(f"🔢 Last global audio ID: {state['last_global_id']}")
