"""
Audio Segmentation Service
Audio fayllarni belgilangan davomiylikdagi bo'laklarga bo'lish
"""

import librosa
import soundfile as sf
import os
from pathlib import Path
import logging
from typing import List, Dict
import numpy as np

logger = logging.getLogger(__name__)


class AudioSegmenter:
    """Audio fayllarni segmentlarga bo'lish uchun klass"""
    
    def __init__(self, output_dir: str = "outputs/segments"):
        """
        Initialize AudioSegmenter
        
        Args:
            output_dir: Segmentlar saqlanadigan papka
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        logger.info("AudioSegmenter initialized")
    
    def segment_audio(
        self,
        input_path: str,
        segment_duration: int = 30,
        overlap: int = 0
    ) -> List[Dict[str, any]]:
        """
        Audio'ni belgilangan davomiylikdagi segmentlarga bo'lish
        
        Args:
            input_path: Kirish audio fayl yo'li
            segment_duration: Har bir segment davomiyligi (sekundlarda)
            overlap: Segmentlar orasidagi overlap (sekundlarda)
        
        Returns:
            Segment ma'lumotlari (fayl yo'li, boshlanish vaqti, tugash vaqti)
        """
        try:
            logger.info(f"✂️ Segmentatsiya boshlandi: {input_path}")
            logger.info(f"   - Segment davomiyligi: {segment_duration}s")
            logger.info(f"   - Overlap: {overlap}s")
            
            # Audio faylni yuklash
            audio, sample_rate = librosa.load(input_path, sr=None)
            total_duration = len(audio) / sample_rate
            
            # Sample sonlarini hisoblash
            segment_samples = segment_duration * sample_rate
            overlap_samples = overlap * sample_rate
            step_samples = segment_samples - overlap_samples
            
            segments = []
            segment_count = 0
            start_sample = 0
            
            # Base filename
            base_filename = Path(input_path).stem
            
            # Audio'ni bo'laklarga bo'lish
            while start_sample < len(audio):
                end_sample = min(start_sample + segment_samples, len(audio))
                
                # Segment'ni kesib olish
                segment_audio = audio[start_sample:end_sample]
                
                # Juda qisqa segmentlarni o'tkazib yuborish
                if len(segment_audio) < sample_rate * 0.5:  # 0.5 sekunddan qisqa
                    break
                
                # Segment haqida ma'lumot
                start_time = start_sample / sample_rate
                end_time = end_sample / sample_rate
                duration = len(segment_audio) / sample_rate
                
                # Fayl nomini yaratish
                segment_filename = f"{base_filename}_segment_{segment_count:03d}.wav"
                segment_path = os.path.join(self.output_dir, segment_filename)
                
                # Segment'ni saqlash
                sf.write(segment_path, segment_audio, sample_rate)
                
                # Ma'lumotni saqlash
                segments.append({
                    "segment_number": segment_count,
                    "filename": segment_filename,
                    "file_path": segment_path,
                    "start_time": round(start_time, 2),
                    "end_time": round(end_time, 2),
                    "duration": round(duration, 2),
                    "sample_rate": sample_rate
                })
                
                logger.info(f"   ✅ Segment {segment_count}: {start_time:.2f}s - {end_time:.2f}s")
                
                segment_count += 1
                start_sample += step_samples
            
            logger.info(f"✅ Segmentatsiya tugadi: {segment_count} ta segment yaratildi")
            logger.info(f"   - Umumiy davomiylik: {total_duration:.2f}s")
            
            return segments
            
        except Exception as e:
            logger.error(f"❌ Segmentatsiyada xato: {e}")
            raise
    
    def segment_by_silence(
        self,
        input_path: str,
        min_silence_duration: int = 1000,
        silence_threshold: int = -40
    ) -> List[Dict[str, any]]:
        """
        Jimlik joylariga qarab segmentlarga bo'lish
        
        Args:
            input_path: Kirish audio fayl yo'li
            min_silence_duration: Minimal jimlik davomiyligi (ms)
            silence_threshold: Jimlik chegarasi (dB)
        
        Returns:
            Segment ma'lumotlari
        """
        try:
            from pydub import AudioSegment
            from pydub.silence import split_on_silence
            
            logger.info(f"✂️ Jimlik bo'yicha segmentatsiya boshlandi")
            
            # Audio faylni yuklash
            audio = AudioSegment.from_file(input_path)
            
            # Jimlik joylarida bo'lish
            chunks = split_on_silence(
                audio,
                min_silence_len=min_silence_duration,
                silence_thresh=silence_threshold,
                keep_silence=500  # Har bir segment oldiga/ketiga 500ms jimlik qoldirish
            )
            
            segments = []
            base_filename = Path(input_path).stem
            
            # Har bir chunk'ni saqlash
            for i, chunk in enumerate(chunks):
                segment_filename = f"{base_filename}_silence_segment_{i:03d}.wav"
                segment_path = os.path.join(self.output_dir, segment_filename)
                
                chunk.export(segment_path, format="wav")
                
                segments.append({
                    "segment_number": i,
                    "filename": segment_filename,
                    "file_path": segment_path,
                    "duration": len(chunk) / 1000.0  # ms to seconds
                })
                
                logger.info(f"   ✅ Segment {i}: {len(chunk)/1000.0:.2f}s")
            
            logger.info(f"✅ Jimlik bo'yicha segmentatsiya tugadi: {len(chunks)} ta segment")
            
            return segments
            
        except Exception as e:
            logger.error(f"❌ Jimlik bo'yicha segmentatsiyada xato: {e}")
            raise
    
    def smart_segment(
        self,
        input_path: str,
        target_duration: int = 30,
        max_segments: int = None
    ) -> List[Dict[str, any]]:
        """
        Aqlli segmentatsiya - audio'ni eng yaxshi nuqtalarda bo'lish
        
        Args:
            input_path: Kirish audio fayl yo'li
            target_duration: Maqsadli segment davomiyligi (sekundlarda)
            max_segments: Maksimal segment soni (agar kerak bo'lsa)
        
        Returns:
            Segment ma'lumotlari
        """
        try:
            logger.info(f"🧠 Aqlli segmentatsiya boshlandi")
            
            # Audio faylni yuklash
            audio, sample_rate = librosa.load(input_path, sr=None)
            total_duration = len(audio) / sample_rate
            
            # Onset detection (audio boshlangan nuqtalarni topish)
            onset_frames = librosa.onset.onset_detect(
                y=audio,
                sr=sample_rate,
                units='samples'
            )
            
            # Target segment samples
            target_samples = target_duration * sample_rate
            
            segments = []
            segment_count = 0
            start_sample = 0
            
            base_filename = Path(input_path).stem
            
            while start_sample < len(audio):
                # Ideal tugash nuqtasi
                ideal_end = start_sample + target_samples
                
                # Eng yaqin onset'ni topish
                nearby_onsets = onset_frames[
                    (onset_frames >= ideal_end - sample_rate) &
                    (onset_frames <= ideal_end + sample_rate)
                ]
                
                if len(nearby_onsets) > 0:
                    end_sample = nearby_onsets[0]
                else:
                    end_sample = min(ideal_end, len(audio))
                
                # Segment'ni kesib olish
                segment_audio = audio[start_sample:end_sample]
                
                if len(segment_audio) < sample_rate * 0.5:
                    break
                
                # Fayl nomini yaratish
                segment_filename = f"{base_filename}_smart_segment_{segment_count:03d}.wav"
                segment_path = os.path.join(self.output_dir, segment_filename)
                
                # Saqlash
                sf.write(segment_path, segment_audio, sample_rate)
                
                start_time = start_sample / sample_rate
                end_time = end_sample / sample_rate
                
                segments.append({
                    "segment_number": segment_count,
                    "filename": segment_filename,
                    "file_path": segment_path,
                    "start_time": round(start_time, 2),
                    "end_time": round(end_time, 2),
                    "duration": round((end_sample - start_sample) / sample_rate, 2)
                })
                
                logger.info(f"   ✅ Smart segment {segment_count}: {start_time:.2f}s - {end_time:.2f}s")
                
                segment_count += 1
                start_sample = end_sample
                
                # Maksimal segment sonini tekshirish
                if max_segments and segment_count >= max_segments:
                    break
            
            logger.info(f"✅ Aqlli segmentatsiya tugadi: {segment_count} ta segment")
            
            return segments
            
        except Exception as e:
            logger.error(f"❌ Aqlli segmentatsiyada xato: {e}")
            raise


# Test uchun
if __name__ == "__main__":
    segmenter = AudioSegmenter()
    print("AudioSegmenter test mode")
