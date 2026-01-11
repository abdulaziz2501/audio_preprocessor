import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write

SAMPLE_RATE = 16000

def record_audio(seconds=5, filename="speaker.wav"):
    print("🎤 Gapiring...")
    audio = sd.rec(
        int(seconds * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )
    sd.wait()
    write(filename, SAMPLE_RATE, audio)
    print("✅ Yozildi")
    return filename

def play_audio(filename):
    from scipy.io.wavfile import read
    sr, audio = read(filename)
    sd.play(audio, sr)
    sd.wait()
