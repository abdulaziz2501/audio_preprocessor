"""
Noise Reduction Service
Audio'dan shovqinni professional darajada tozalash
"""

import numpy as np
import librosa
import soundfile as sf
import noisereduce as nr
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class NoiseReducer:
    """Audio shovqinlarini tozalash uchun klass"""
    
    def __init__(self, output_dir: str = "outputs"):
        """
        Initialize NoiseReducer
        
        Args:
            output_dir: Output fayllar saqlanadigan papka
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        logger.info("NoiseReducer initialized")
    
    def reduce_noise(
        self,
        input_path: str,
        strength: float = 0.8,
        stationary: bool = True
    ) -> str:
        """
        Audio fayldan shovqinni tozalash
        
        Args:
            input_path: Kirish audio fayl yo'li
            strength: Shovqin tozalash kuchi (0.0 - 1.0)
                     0.0 - minimal tozalash
                     1.0 - maksimal tozalash
            stationary: Doimiy shovqin uchun True, o'zgaruvchan uchun False
        
        Returns:
            Tozalangan audio fayl yo'li
        """
        try:
            logger.info(f"🔊 Shovqin tozalash boshlandi: {input_path}")
            
            # Audio faylni yuklash
            audio, sample_rate = librosa.load(input_path, sr=None)
            
            # Original uzunlikni saqlash
            original_length = len(audio)
            
            # Shovqinni aniqlash va tozalash
            # noisereduce kutubxonasidan foydalanish
            reduced_noise = nr.reduce_noise(
                y=audio,
                sr=sample_rate,
                stationary=stationary,
                prop_decrease=strength
            )
            
            # Natijani normalizatsiya qilish (clipping'dan saqlash)
            max_value = np.abs(reduced_noise).max()
            if max_value > 1.0:
                reduced_noise = reduced_noise / max_value * 0.95
            
            # Output fayl nomini yaratish
            filename = Path(input_path).stem
            output_filename = f"{filename}_noise_reduced.wav"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Tozalangan audio'ni saqlash
            sf.write(output_path, reduced_noise, sample_rate)
            
            # Statistika
            noise_reduction_db = 20 * np.log10(
                np.mean(np.abs(audio)) / np.mean(np.abs(reduced_noise))
            )
            
            logger.info(f"✅ Shovqin tozalandi:")
            logger.info(f"   - Original uzunlik: {original_length / sample_rate:.2f} soniya")
            logger.info(f"   - Shovqin kamayishi: ~{noise_reduction_db:.1f} dB")
            logger.info(f"   - Saqlandi: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Shovqin tozalashda xato: {e}")
            raise
    
    def adaptive_noise_reduction(
        self,
        input_path: str,
        noise_sample_duration: float = 1.0
    ) -> str:
        """
        Adaptiv shovqin tozalash (audio boshidan namuna olib)
        
        Args:
            input_path: Kirish audio fayl yo'li
            noise_sample_duration: Shovqin namunasi davomiyligi (sekundlarda)
        
        Returns:
            Tozalangan audio fayl yo'li
        """
        try:
            logger.info(f"🔊 Adaptiv shovqin tozalash boshlandi")
            
            # Audio faylni yuklash
            audio, sample_rate = librosa.load(input_path, sr=None)
            
            # Shovqin namunasini olish (audio boshidan)
            noise_sample_length = int(noise_sample_duration * sample_rate)
            noise_sample = audio[:noise_sample_length]
            
            # Adaptiv shovqin tozalash
            reduced_noise = nr.reduce_noise(
                y=audio,
                sr=sample_rate,
                y_noise=noise_sample,
                stationary=False
            )
            
            # Normalizatsiya
            max_value = np.abs(reduced_noise).max()
            if max_value > 1.0:
                reduced_noise = reduced_noise / max_value * 0.95
            
            # Output faylni saqlash
            filename = Path(input_path).stem
            output_filename = f"{filename}_adaptive_reduced.wav"
            output_path = os.path.join(self.output_dir, output_filename)
            
            sf.write(output_path, reduced_noise, sample_rate)
            
            logger.info(f"✅ Adaptiv shovqin tozalandi: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Adaptiv shovqin tozalashda xato: {e}")
            raise
    
    def multi_pass_reduction(
        self,
        input_path: str,
        passes: int = 2,
        strength: float = 0.6
    ) -> str:
        """
        Ko'p bosqichli shovqin tozalash (yuqori sifat uchun)
        
        Args:
            input_path: Kirish audio fayl yo'li
            passes: Tozalash bosqichlari soni
            strength: Har bir bosqichda tozalash kuchi
        
        Returns:
            Tozalangan audio fayl yo'li
        """
        try:
            logger.info(f"🔊 {passes} bosqichli shovqin tozalash boshlandi")
            
            audio, sample_rate = librosa.load(input_path, sr=None)
            
            # Ko'p marta tozalash
            for i in range(passes):
                logger.info(f"   Pass {i+1}/{passes}...")
                audio = nr.reduce_noise(
                    y=audio,
                    sr=sample_rate,
                    stationary=True,
                    prop_decrease=strength
                )
            
            # Normalizatsiya
            max_value = np.abs(audio).max()
            if max_value > 1.0:
                audio = audio / max_value * 0.95
            
            # Saqlash
            filename = Path(input_path).stem
            output_filename = f"{filename}_multipass_reduced.wav"
            output_path = os.path.join(self.output_dir, output_filename)
            
            sf.write(output_path, audio, sample_rate)
            
            logger.info(f"✅ {passes} bosqichli tozalash tugadi: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Ko'p bosqichli tozalashda xato: {e}")
            raise


# Test uchun
if __name__ == "__main__":
    # Test qilish
    reducer = NoiseReducer()
    print("NoiseReducer test mode")
    print("Foydalanish: python noise_reducer.py <audio_file>")
