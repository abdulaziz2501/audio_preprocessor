from faster_whisper import WhisperModel

class STT:
    def __init__(self):
        self.model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8"
        )

    def transcribe(self, audio_path):
        segments, _ = self.model.transcribe(
            audio_path,
            language="uz",
            beam_size=5
        )
        text = " ".join(seg.text for seg in segments)
        return text.strip()
