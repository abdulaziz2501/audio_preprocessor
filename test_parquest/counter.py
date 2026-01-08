import os
import soundfile as sf

# ========================
# CONFIG
# ========================
AUDIO_DIR = "output/short_audio/audio"  # yoki short_audio/audio
# AUDIO_DIR = "output/short_audio/audio"

# ========================
# GET ALL WAV FILES
# ========================
wav_files = [os.path.join(AUDIO_DIR, f) for f in os.listdir(AUDIO_DIR) if f.endswith(".wav")]

total_seconds = 0.0

for wav_file in wav_files:
    try:
        data, sr = sf.read(wav_file)
        duration = len(data) / sr
        total_seconds += duration
    except Exception as e:
        print(f"⚠️ Could not read {wav_file}: {e}")

# ========================
# FORMAT TIME
# ========================
hours = int(total_seconds // 3600)
minutes = int((total_seconds % 3600) // 60)
seconds = int(total_seconds % 60)

print(f"🎧 Total audio files: {len(wav_files)}")
print(f"⏱ Total duration: {hours}h {minutes}m {seconds}s ({total_seconds/3600:.2f} hours)")
