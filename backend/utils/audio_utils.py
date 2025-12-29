"""
Audio Utilities
Audio fayllar bilan ishlash uchun yordamchi funksiyalar
"""

import os
import uuid
from pathlib import Path
import logging
from typing import Optional
from fastapi import UploadFile
import shutil

logger = logging.getLogger(__name__)


def create_directories():
    """Kerakli papkalarni yaratish"""
    directories = [
        "uploads",
        "outputs",
        "outputs/segments",
        "temp"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"📁 Papka yaratildi yoki mavjud: {directory}")


def generate_unique_filename(original_filename: str) -> str:
    """
    Unikal fayl nomi yaratish
    
    Args:
        original_filename: Original fayl nomi
    
    Returns:
        Unikal fayl nomi (UUID + extension)
    """
    file_ext = Path(original_filename).suffix
    unique_id = uuid.uuid4().hex[:12]
    return f"{unique_id}{file_ext}"


def save_upload_file(upload_file: UploadFile, file_id: str) -> str:
    """
    Yuklangan faylni saqlash
    
    Args:
        upload_file: FastAPI UploadFile object
        file_id: Fayl ID'si
    
    Returns:
        Saqlangan fayl yo'li
    """
    try:
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file_id)
        
        # Faylni saqlash
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        logger.info(f"💾 Fayl saqlandi: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"❌ Fayl saqlashda xato: {e}")
        raise


def get_file_size_mb(file_path: str) -> float:
    """
    Fayl hajmini MB da olish
    
    Args:
        file_path: Fayl yo'li
    
    Returns:
        Fayl hajmi (MB)
    """
    try:
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    except Exception as e:
        logger.error(f"❌ Fayl hajmini olishda xato: {e}")
        return 0.0


def validate_audio_file(file_path: str) -> bool:
    """
    Audio faylni tekshirish
    
    Args:
        file_path: Fayl yo'li
    
    Returns:
        True agar fayl to'g'ri bo'lsa
    """
    try:
        import librosa
        
        # Faylni yuklashga urinish
        audio, sr = librosa.load(file_path, sr=None, duration=1)
        
        if len(audio) == 0:
            logger.error("❌ Audio fayl bo'sh")
            return False
        
        logger.info(f"✅ Audio fayl to'g'ri: sample_rate={sr}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Audio faylni tekshirishda xato: {e}")
        return False


def get_audio_info(file_path: str) -> dict:
    """
    Audio fayl haqida ma'lumot olish
    
    Args:
        file_path: Fayl yo'li
    
    Returns:
        Audio ma'lumotlari dictionary
    """
    try:
        import librosa
        
        # Audio yuklash
        audio, sr = librosa.load(file_path, sr=None)
        
        duration = len(audio) / sr
        channels = 1  # librosa mono formatda yuklaydi
        
        info = {
            "duration": round(duration, 2),
            "sample_rate": sr,
            "channels": channels,
            "samples": len(audio),
            "file_size_mb": get_file_size_mb(file_path),
            "format": Path(file_path).suffix[1:].upper()
        }
        
        logger.info(f"ℹ️ Audio info: {duration:.2f}s, {sr}Hz")
        return info
        
    except Exception as e:
        logger.error(f"❌ Audio ma'lumotlarini olishda xato: {e}")
        return {}


def cleanup_old_files(directory: str, max_age_hours: int = 24):
    """
    Eski fayllarni o'chirish (disk bo'shatish uchun)
    
    Args:
        directory: Tozalanadigan papka
        max_age_hours: Maksimal fayl yoshi (soatlarda)
    """
    try:
        import time
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        deleted_count = 0
        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    deleted_count += 1
                    logger.info(f"🗑️ Eski fayl o'chirildi: {filename}")
        
        if deleted_count > 0:
            logger.info(f"✅ {deleted_count} ta eski fayl o'chirildi")
        
    except Exception as e:
        logger.error(f"❌ Eski fayllarni o'chirishda xato: {e}")


def convert_audio_format(
    input_path: str,
    output_format: str = "wav",
    output_dir: str = "outputs"
) -> str:
    """
    Audio formatni o'zgartirish
    
    Args:
        input_path: Kirish fayl yo'li
        output_format: Yangi format (wav, mp3, flac, ogg)
        output_dir: Output papka
    
    Returns:
        Yangi fayl yo'li
    """
    try:
        from pydub import AudioSegment
        
        logger.info(f"🔄 Format o'zgartirish: {output_format}")
        
        # Audio yuklash
        audio = AudioSegment.from_file(input_path)
        
        # Yangi fayl nomi
        filename = Path(input_path).stem
        output_filename = f"{filename}.{output_format}"
        output_path = os.path.join(output_dir, output_filename)
        
        # Export
        audio.export(output_path, format=output_format)
        
        logger.info(f"✅ Format o'zgartirildi: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"❌ Format o'zgartirishda xato: {e}")
        raise


def normalize_audio(input_path: str, target_dbfs: float = -20.0) -> str:
    """
    Audio ovozini normallashtirish (ovoz balandligini standartlashtirish)
    
    Args:
        input_path: Kirish fayl yo'li
        target_dbfs: Maqsadli ovoz balandligi (dBFS)
    
    Returns:
        Normallashtirilgan fayl yo'li
    """
    try:
        from pydub import AudioSegment
        
        logger.info(f"🔊 Audio normallashtirish boshlandi")
        
        audio = AudioSegment.from_file(input_path)
        
        # Hozirgi loudness
        current_dbfs = audio.dBFS
        
        # O'zgarish hisoblash
        change_in_dbfs = target_dbfs - current_dbfs
        
        # Normalizatsiya
        normalized_audio = audio.apply_gain(change_in_dbfs)
        
        # Saqlash
        filename = Path(input_path).stem
        output_path = os.path.join("outputs", f"{filename}_normalized.wav")
        
        normalized_audio.export(output_path, format="wav")
        
        logger.info(f"✅ Normallashtirildi: {current_dbfs:.1f} dBFS → {target_dbfs:.1f} dBFS")
        
        return output_path
        
    except Exception as e:
        logger.error(f"❌ Normallashtirish xato: {e}")
        raise


def merge_audio_files(file_paths: list, output_path: str = None) -> str:
    """
    Bir nechta audio fayllarni birlashtirish
    
    Args:
        file_paths: Audio fayllar ro'yxati
        output_path: Output fayl yo'li (optional)
    
    Returns:
        Birlashtirilgan fayl yo'li
    """
    try:
        from pydub import AudioSegment
        
        logger.info(f"🔗 {len(file_paths)} ta faylni birlashtirish")
        
        combined = AudioSegment.empty()
        
        for file_path in file_paths:
            audio = AudioSegment.from_file(file_path)
            combined += audio
        
        # Output path
        if output_path is None:
            output_path = os.path.join("outputs", "merged_audio.wav")
        
        combined.export(output_path, format="wav")
        
        logger.info(f"✅ Fayllar birlashtirildi: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"❌ Birlashtirish xato: {e}")
        raise


# Test uchun
if __name__ == "__main__":
    print("Audio Utilities test mode")
    create_directories()
    print("Barcha papkalar yaratildi!")
