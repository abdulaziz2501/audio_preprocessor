"""
Silence Removal Service
Audio'dan jimlik (silence) joylarni aniqlash va olib tashlash
"""

from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import os
from pathlib import Path
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class SilenceRemover:
    """Audio'dan jimlikni olib tashlash uchun klass"""
    
    def __init__(self, output_dir: str = "outputs"):
        """
        Initialize SilenceRemover
        
        Args:
            output_dir: Output fayllar saqlanadigan papka
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        logger.info("SilenceRemover initialized")
    
    def remove_silence(
        self,
        input_path: str,
        silence_threshold: int = -40,
        min_silence_duration: int = 500,
        keep_silence: int = 100
    ) -> str:
        """
        Audio'dan jimlik joylarni olib tashlash
        
        Args:
            input_path: Kirish audio fayl yo'li
            silence_threshold: Jimlik chegarasi (dB)
                              -40 dB = juda jim
                              -30 dB = o'rtacha jim
                              -20 dB = ozgina tovush
            min_silence_duration: Minimal jimlik davomiyligi (milliseconds)
                                 500ms = 0.5 soniya
            keep_silence: Har bir gap oldida/ketida qoldiriladigan jimlik (ms)
                         100ms = ikkita gap orasida kichik pauza qoldirish
        
        Returns:
            Jimlik olib tashlangan audio fayl yo'li
        """
        try:
            logger.info(f"🔇 Jimlik olib tashlash boshlandi: {input_path}")
            logger.info(f"   - Jimlik chegarasi: {silence_threshold} dB")
            logger.info(f"   - Minimal jimlik: {min_silence_duration} ms")
            
            # Audio faylni yuklash
            audio = AudioSegment.from_file(input_path)
            original_duration = len(audio) / 1000.0  # ms to seconds
            
            # Jimlik bo'lmagan joylarni aniqlash
            nonsilent_ranges = detect_nonsilent(
                audio,
                min_silence_len=min_silence_duration,
                silence_thresh=silence_threshold,
                seek_step=10  # Tezlik va aniqlik o'rtasida muvozanat
            )
            
            if not nonsilent_ranges:
                logger.warning("⚠️ Hech qanday ovoz topilmadi!")
                return input_path
            
            # Jimlik bo'lmagan qismlarni birlashtirish
            output_audio = AudioSegment.empty()
            
            for i, (start, end) in enumerate(nonsilent_ranges):
                # Keep_silence qo'shish
                start_with_silence = max(0, start - keep_silence)
                end_with_silence = min(len(audio), end + keep_silence)
                
                # Qismni qo'shish
                chunk = audio[start_with_silence:end_with_silence]
                output_audio += chunk
                
                logger.debug(f"   Segment {i+1}: {start/1000:.2f}s - {end/1000:.2f}s")
            
            # Statistika
            final_duration = len(output_audio) / 1000.0
            removed_duration = original_duration - final_duration
            percentage_removed = (removed_duration / original_duration) * 100
            
            # Output fayl nomini yaratish
            filename = Path(input_path).stem
            output_filename = f"{filename}_no_silence.wav"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Saqlash
            output_audio.export(output_path, format="wav")
            
            logger.info(f"✅ Jimlik olib tashlandi:")
            logger.info(f"   - Original davomiylik: {original_duration:.2f}s")
            logger.info(f"   - Yangi davomiylik: {final_duration:.2f}s")
            logger.info(f"   - Olib tashlangan: {removed_duration:.2f}s ({percentage_removed:.1f}%)")
            logger.info(f"   - Saqlandi: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Jimlik olib tashlashda xato: {e}")
            raise
    
    def detect_silence_ranges(
        self,
        input_path: str,
        silence_threshold: int = -40,
        min_silence_duration: int = 500
    ) -> List[Tuple[float, float]]:
        """
        Audio'dagi jimlik joylarni aniqlash (olib tashlamasdan)
        
        Args:
            input_path: Kirish audio fayl yo'li
            silence_threshold: Jimlik chegarasi (dB)
            min_silence_duration: Minimal jimlik davomiyligi (ms)
        
        Returns:
            Jimlik oraliqlar ro'yxati [(start_time, end_time), ...]
        """
        try:
            logger.info(f"🔍 Jimlik joylarni aniqlash boshlandi")
            
            audio = AudioSegment.from_file(input_path)
            
            # Jimlik bo'lmagan joylarni topish
            nonsilent_ranges = detect_nonsilent(
                audio,
                min_silence_len=min_silence_duration,
                silence_thresh=silence_threshold
            )
            
            # Jimlik oraliqlarini hisoblash
            silence_ranges = []
            
            # Boshlang'ich jimlik
            if nonsilent_ranges and nonsilent_ranges[0][0] > 0:
                silence_ranges.append((0, nonsilent_ranges[0][0] / 1000.0))
            
            # Oralardagi jimliklar
            for i in range(len(nonsilent_ranges) - 1):
                silence_start = nonsilent_ranges[i][1] / 1000.0
                silence_end = nonsilent_ranges[i + 1][0] / 1000.0
                silence_ranges.append((silence_start, silence_end))
            
            # Oxirgi jimlik
            if nonsilent_ranges and nonsilent_ranges[-1][1] < len(audio):
                silence_ranges.append((nonsilent_ranges[-1][1] / 1000.0, len(audio) / 1000.0))
            
            logger.info(f"✅ {len(silence_ranges)} ta jimlik joyi topildi")
            
            return silence_ranges
            
        except Exception as e:
            logger.error(f"❌ Jimlik aniqlashda xato: {e}")
            raise
    
    def trim_silence_edges(
        self,
        input_path: str,
        silence_threshold: int = -40
    ) -> str:
        """
        Audio boshi va oxiridagi jimlikni kesib tashlash
        
        Args:
            input_path: Kirish audio fayl yo'li
            silence_threshold: Jimlik chegarasi (dB)
        
        Returns:
            Kesilgan audio fayl yo'li
        """
        try:
            logger.info(f"✂️ Bosh va oxir jimlikni kesish boshlandi")
            
            audio = AudioSegment.from_file(input_path)
            original_duration = len(audio) / 1000.0
            
            # Jimlik bo'lmagan birinchi va oxirgi nuqtalarni topish
            nonsilent_ranges = detect_nonsilent(
                audio,
                min_silence_len=100,
                silence_thresh=silence_threshold
            )
            
            if not nonsilent_ranges:
                logger.warning("⚠️ Hech qanday ovoz topilmadi!")
                return input_path
            
            # Birinchi va oxirgi ovozli joylarni olish
            start = nonsilent_ranges[0][0]
            end = nonsilent_ranges[-1][1]
            
            # Kesish
            trimmed_audio = audio[start:end]
            
            # Statistika
            final_duration = len(trimmed_audio) / 1000.0
            removed = original_duration - final_duration
            
            # Saqlash
            filename = Path(input_path).stem
            output_filename = f"{filename}_trimmed.wav"
            output_path = os.path.join(self.output_dir, output_filename)
            
            trimmed_audio.export(output_path, format="wav")
            
            logger.info(f"✅ Bosh va oxir kesildi:")
            logger.info(f"   - Original: {original_duration:.2f}s")
            logger.info(f"   - Yangi: {final_duration:.2f}s")
            logger.info(f"   - Olib tashlangan: {removed:.2f}s")
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Kesishda xato: {e}")
            raise
    
    def adaptive_silence_removal(
        self,
        input_path: str,
        aggressiveness: str = "moderate"
    ) -> str:
        """
        Adaptiv jimlik olib tashlash (audio tabiati bo'yicha moslashadi)
        
        Args:
            input_path: Kirish audio fayl yo'li
            aggressiveness: Agressivlik darajasi
                          "gentle" = kam olib tashlash
                          "moderate" = o'rtacha
                          "aggressive" = ko'p olib tashlash
        
        Returns:
            Qayta ishlangan audio fayl yo'li
        """
        try:
            logger.info(f"🎯 Adaptiv jimlik olib tashlash: {aggressiveness}")
            
            # Parametrlarni tanlash
            params = {
                "gentle": {
                    "threshold": -35,
                    "min_silence": 1000,
                    "keep_silence": 200
                },
                "moderate": {
                    "threshold": -40,
                    "min_silence": 500,
                    "keep_silence": 100
                },
                "aggressive": {
                    "threshold": -45,
                    "min_silence": 300,
                    "keep_silence": 50
                }
            }
            
            p = params.get(aggressiveness, params["moderate"])
            
            # Jimlikni olib tashlash
            output_path = self.remove_silence(
                input_path,
                silence_threshold=p["threshold"],
                min_silence_duration=p["min_silence"],
                keep_silence=p["keep_silence"]
            )
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Adaptiv jimlik olib tashlashda xato: {e}")
            raise


# Test uchun
if __name__ == "__main__":
    remover = SilenceRemover()
    print("SilenceRemover test mode")
