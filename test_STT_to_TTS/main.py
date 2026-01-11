from audio_io import record_audio, play_audio
from stt import STT
from tts import TextToSpeech

def simple_logic(text: str) -> str:
    text = text.lower()

    if "salom" in text:
        return "Salom! Qanday yordam bera olaman?"
    if "isming nima" in text:
        return "Men sening shaxsiy ovozli assistentingman"
    if "rahmat" in text:
        return "Arzimaydi"
    if "to'xta" in text or "stop" in text:
        return "Yaxshi, to‘xtayman"

    return "Kechirasan, tushunmadim"

def main():
    stt = STT()
    tts = TextToSpeech()

    while True:
        audio_path = record_audio(seconds=5)
        text = stt.transcribe(audio_path)

        print(f"📝 STT: {text}")

        response = simple_logic(text)
        print(f"🤖 Javob: {response}")

        out_audio = tts.speak(response)
        play_audio(out_audio)

        if "to‘xtayman" in response:
            break

if __name__ == "__main__":
    main()
