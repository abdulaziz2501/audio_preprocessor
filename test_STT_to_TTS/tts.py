from TTS.api import TTS

class TextToSpeech:
    def __init__(self):
        self.tts = TTS(
            model_name="tts_models/multilingual/multi-dataset/xtts_v2",
            device="cpu"
        )

    def speak(self, text, out_path="response.wav"):
        self.tts.tts_to_file(
            text=text,
            speaker_wav="speaker.wav",
            language="uz",
            file_path=out_path
        )
        return out_path
