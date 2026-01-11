"""
AudioAI - Advanced Silence Trimming Module
Butun audio bo'ylab silence aniqlash va olib tashlash

Bu modul audio fayllarning:
1. Boshi va oxiridagi silence
2. O'rtadagi uzun silence (gaps)
3. Ortiqcha pauzalarni qisqartirish
uchun ishlatiladi.
"""

import numpy as np
import librosa
from typing import Tuple, List, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SilenceSegment:
    """
    Silence segmenti ma'lumotlari.
    
    Attributes:
        start_sample: Boshlang'ich sample
        end_sample: Tugash sample
        start_time: Boshlang'ich vaqt (sekund)
        end_time: Tugash vaqti (sekund)
        duration: Davomiylik (sekund)
    """
    start_sample: int
    end_sample: int
    start_time: float
    end_time: float
    duration: float


@dataclass 
class AudioSegment:
    """
    Audio segmenti (speech yoki silence).
    
    Attributes:
        start_sample: Boshlang'ich sample
        end_sample: Tugash sample
        is_speech: True - nutq, False - silence
        duration: Davomiylik (sekund)
    """
    start_sample: int
    end_sample: int
    is_speech: bool
    duration: float


class SilenceTrimmer:
    """
    Kengaytirilgan Silence Trimmer.
    
    Butun audio bo'ylab silence aniqlash va olib tashlash:
    - Boshi va oxiridagi silence kesish
    - O'rtadagi uzun pauzalarni qisqartirish
    - Minimal speech davomiyligini saqlash
    
    Attributes:
        sample_rate (int): Audio sample rate
        silence_threshold_db (float): Silence aniqlash chegarasi (dB)
        min_silence_duration (float): Minimal silence davomiyligi (olib tashlanadigan)
        max_silence_duration (float): Maksimal ruxsat berilgan silence
        frame_length (int): Tahlil frame uzunligi
        hop_length (int): Frame oraliq uzunligi
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        silence_threshold_db: float = -40,
        min_silence_duration: float = 0.3,
        max_silence_duration: float = 0.4,
        frame_length: int = 2048,
        hop_length: int = 512
    ):
        """
        SilenceTrimmer ni ishga tushirish.
        
        Args:
            sample_rate: Audio sample rate
            silence_threshold_db: Silence chegarasi dB da (past = sezgirroq)
            min_silence_duration: Bu vaqtdan uzun silencelar olib tashlanadi
            max_silence_duration: Qoldirilgan silencelarning max uzunligi
            frame_length: Analysis frame length
            hop_length: Hop length for analysis
        """
        self.sample_rate = sample_rate
        self.silence_threshold_db = silence_threshold_db
        self.min_silence_duration = min_silence_duration
        self.max_silence_duration = max_silence_duration
        self.frame_length = frame_length
        self.hop_length = hop_length
        
        logger.info(
            f"SilenceTrimmer initialized: threshold={silence_threshold_db}dB, "
            f"min_silence={min_silence_duration}s, max_silence={max_silence_duration}s"
        )
    
    def get_audio_energy(self, audio: np.ndarray) -> np.ndarray:
        """
        Audio energiyasini frame bo'yicha hisoblash.
        
        Args:
            audio: Input audio
            
        Returns:
            np.ndarray: Har bir frame uchun energiya (dB)
        """
        # RMS energiya
        rms = librosa.feature.rms(
            y=audio,
            frame_length=self.frame_length,
            hop_length=self.hop_length
        )[0]
        
        # dB ga o'tkazish
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)
        
        return rms_db
    
    def detect_silence_segments(
        self, 
        audio: np.ndarray
    ) -> List[SilenceSegment]:
        """
        Butun audio bo'ylab silence segmentlarini aniqlash.
        
        Args:
            audio: Input audio
            
        Returns:
            List[SilenceSegment]: Barcha silence segmentlari
        """
        # Energiya olish
        energy_db = self.get_audio_energy(audio)
        
        # Silence mask yaratish
        is_silence = energy_db < self.silence_threshold_db
        
        # Segmentlarni topish
        segments = []
        in_silence = False
        silence_start = 0
        
        for i, silent in enumerate(is_silence):
            if silent and not in_silence:
                # Silence boshlanishi
                in_silence = True
                silence_start = i
            elif not silent and in_silence:
                # Silence tugashi
                in_silence = False
                
                # Sample indekslariga o'tkazish
                start_sample = silence_start * self.hop_length
                end_sample = i * self.hop_length
                
                # Vaqtga o'tkazish
                start_time = start_sample / self.sample_rate
                end_time = end_sample / self.sample_rate
                duration = end_time - start_time
                
                segments.append(SilenceSegment(
                    start_sample=start_sample,
                    end_sample=end_sample,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration
                ))
        
        # Oxirida silence qolgan bo'lsa
        if in_silence:
            start_sample = silence_start * self.hop_length
            end_sample = len(audio)
            start_time = start_sample / self.sample_rate
            end_time = end_sample / self.sample_rate
            duration = end_time - start_time
            
            segments.append(SilenceSegment(
                start_sample=start_sample,
                end_sample=end_sample,
                start_time=start_time,
                end_time=end_time,
                duration=duration
            ))
        
        logger.info(f"Found {len(segments)} silence segments")
        return segments
    
    def detect_all_segments(
        self, 
        audio: np.ndarray
    ) -> List[AudioSegment]:
        """
        Butun audio ni speech va silence segmentlariga bo'lish.
        
        Args:
            audio: Input audio
            
        Returns:
            List[AudioSegment]: Barcha segmentlar (speech + silence)
        """
        # Energiya olish
        energy_db = self.get_audio_energy(audio)
        
        # Silence mask
        is_silence = energy_db < self.silence_threshold_db
        
        segments = []
        current_type = is_silence[0]  # True = silence, False = speech
        segment_start = 0
        
        for i in range(1, len(is_silence)):
            if is_silence[i] != current_type:
                # Segment tugadi
                start_sample = segment_start * self.hop_length
                end_sample = i * self.hop_length
                duration = (end_sample - start_sample) / self.sample_rate
                
                segments.append(AudioSegment(
                    start_sample=start_sample,
                    end_sample=min(end_sample, len(audio)),
                    is_speech=not current_type,
                    duration=duration
                ))
                
                # Yangi segment boshlanishi
                segment_start = i
                current_type = is_silence[i]
        
        # Oxirgi segment
        start_sample = segment_start * self.hop_length
        end_sample = len(audio)
        duration = (end_sample - start_sample) / self.sample_rate
        
        segments.append(AudioSegment(
            start_sample=start_sample,
            end_sample=end_sample,
            is_speech=not current_type,
            duration=duration
        ))
        
        return segments
    
    def trim_leading_trailing(
        self, 
        audio: np.ndarray,
        padding: float = 0.05
    ) -> Tuple[np.ndarray, dict]:
        """
        Faqat boshi va oxiridagi silencelarni kesish.
        
        Args:
            audio: Input audio
            padding: Qoldirilgan padding (sekund)
            
        Returns:
            Tuple: Trimmed audio va statistika
        """
        original_duration = len(audio) / self.sample_rate
        
        # Librosa trim
        trimmed, index = librosa.effects.trim(
            audio,
            top_db=abs(self.silence_threshold_db),
            frame_length=self.frame_length,
            hop_length=self.hop_length
        )
        
        # Padding qo'shish
        pad_samples = int(padding * self.sample_rate)
        start_idx = max(0, index[0] - pad_samples)
        end_idx = min(len(audio), index[1] + pad_samples)
        
        trimmed = audio[start_idx:end_idx]
        trimmed_duration = len(trimmed) / self.sample_rate
        
        stats = {
            'original_duration': original_duration,
            'trimmed_duration': trimmed_duration,
            'leading_removed': index[0] / self.sample_rate,
            'trailing_removed': (len(audio) - index[1]) / self.sample_rate
        }
        
        logger.info(f"Leading/trailing trim: {original_duration:.2f}s -> {trimmed_duration:.2f}s")
        
        return trimmed, stats
    
    def remove_long_silences(
        self, 
        audio: np.ndarray,
        keep_short_pause: float = 0.15
    ) -> Tuple[np.ndarray, dict]:
        """
        Audio ichidagi uzun silencelarni qisqartirish.
        
        min_silence_duration dan uzun silencelar max_silence_duration ga qisqartiriladi.
        
        Args:
            audio: Input audio
            keep_short_pause: Silencelar orasida qoldirilgan qisqa pauza
            
        Returns:
            Tuple: Processed audio va statistika
        """
        segments = self.detect_all_segments(audio)
        
        # Yangi audio qurish
        output_parts = []
        total_silence_removed = 0
        silences_shortened = 0
        
        for segment in segments:
            segment_audio = audio[segment.start_sample:segment.end_sample]
            
            if segment.is_speech:
                # Nutq qismini to'liq qo'shish
                output_parts.append(segment_audio)
            else:
                # Silence segment
                if segment.duration > self.min_silence_duration:
                    # Uzun silence - qisqartirish
                    keep_duration = min(self.max_silence_duration, segment.duration)
                    keep_samples = int(keep_duration * self.sample_rate)
                    
                    # Silencening boshidan qisqartirilgan qismni olish
                    shortened_silence = segment_audio[:keep_samples]
                    output_parts.append(shortened_silence)
                    
                    removed = segment.duration - keep_duration
                    total_silence_removed += removed
                    silences_shortened += 1
                    
                    logger.debug(f"Shortened silence: {segment.duration:.2f}s -> {keep_duration:.2f}s")
                else:
                    # Qisqa silence - saqlab qolish
                    output_parts.append(segment_audio)
        
        # Birlashtirilgan audio
        if len(output_parts) > 0:
            output_audio = np.concatenate(output_parts)
        else:
            output_audio = audio
        
        original_duration = len(audio) / self.sample_rate
        processed_duration = len(output_audio) / self.sample_rate
        
        stats = {
            'original_duration': original_duration,
            'processed_duration': processed_duration,
            'total_silence_removed': total_silence_removed,
            'silences_shortened': silences_shortened,
            'segments_found': len(segments)
        }
        
        logger.info(
            f"Long silences removed: {original_duration:.2f}s -> {processed_duration:.2f}s "
            f"({silences_shortened} silences shortened, {total_silence_removed:.2f}s removed)"
        )
        
        return output_audio, stats
    
    def adaptive_threshold(self, audio: np.ndarray) -> float:
        """
        Audio xususiyatlariga qarab adaptiv threshold aniqlash.
        
        Args:
            audio: Input audio
            
        Returns:
            float: Optimal threshold (dB)
        """
        # Energiya hisoblash
        energy_db = self.get_audio_energy(audio)
        
        # Statistikalar
        mean_energy = np.mean(energy_db)
        std_energy = np.std(energy_db)
        min_energy = np.min(energy_db)
        
        # Adaptiv threshold: mean dan 1.5 std past
        adaptive_threshold = mean_energy - 1.5 * std_energy
        
        # Minimal va maksimal chegaralar
        adaptive_threshold = max(adaptive_threshold, min_energy + 5)
        adaptive_threshold = min(adaptive_threshold, -25)  # -25 dB dan yuqori bo'lmasin
        
        logger.info(f"Adaptive threshold: {adaptive_threshold:.1f}dB (mean={mean_energy:.1f}, std={std_energy:.1f})")
        
        return adaptive_threshold
    
    def full_trim(
        self, 
        audio: np.ndarray,
        use_adaptive: bool = True,
        remove_internal: bool = True
    ) -> Tuple[np.ndarray, dict]:
        """
        To'liq silence trimming pipeline.
        
        1. Adaptiv threshold (agar kerak)
        2. Boshi va oxirini kesish
        3. O'rtadagi uzun silencelarni qisqartirish
        
        Args:
            audio: Input audio
            use_adaptive: Adaptiv threshold ishlatish
            remove_internal: O'rtadagi silencelarni ham qisqartirish
            
        Returns:
            Tuple: Fully processed audio va statistika
        """
        original_duration = len(audio) / self.sample_rate
        
        # 1. Adaptiv threshold
        if use_adaptive:
            original_threshold = self.silence_threshold_db
            self.silence_threshold_db = self.adaptive_threshold(audio)
        
        # 2. Boshi va oxirini kesish
        audio, trim_stats = self.trim_leading_trailing(audio)
        
        # 3. O'rtadagi silencelarni qisqartirish
        if remove_internal:
            audio, internal_stats = self.remove_long_silences(audio)
        else:
            internal_stats = {'total_silence_removed': 0, 'silences_shortened': 0}
        
        # Threshold qaytarish
        if use_adaptive:
            self.silence_threshold_db = original_threshold
        
        final_duration = len(audio) / self.sample_rate
        
        # Umumiy statistika
        stats = {
            'original_duration': original_duration,
            'final_duration': final_duration,
            'total_removed': original_duration - final_duration,
            'reduction_percent': ((original_duration - final_duration) / original_duration) * 100 if original_duration > 0 else 0,
            'leading_removed': trim_stats.get('leading_removed', 0),
            'trailing_removed': trim_stats.get('trailing_removed', 0),
            'internal_silence_removed': internal_stats.get('total_silence_removed', 0),
            'silences_shortened': internal_stats.get('silences_shortened', 0)
        }
        
        logger.info(
            f"Full trim completed: {original_duration:.2f}s -> {final_duration:.2f}s "
            f"({stats['reduction_percent']:.1f}% reduction)"
        )
        
        return audio, stats
    
    def trim(
        self, 
        audio: np.ndarray,
        leading_pad: float = 0.05,
        trailing_pad: float = 0.05
    ) -> Tuple[np.ndarray, dict]:
        """
        Backward compatible trim method.
        Endi full_trim ni chaqiradi.
        
        Args:
            audio: Input audio
            leading_pad: Boshida padding
            trailing_pad: Oxirida padding
            
        Returns:
            Tuple: Trimmed audio va statistika
        """
        return self.full_trim(audio, use_adaptive=True, remove_internal=True)
    
    def aggressive_trim(
        self, 
        audio: np.ndarray,
        target_silence_ratio: float = 0.1
    ) -> Tuple[np.ndarray, dict]:
        """
        Aggressive silence trimming - maksimal nutq ajratib olish.
        
        Iterativ ravishda threshold oshirib, maqsad silence ratio ga yetguncha
        silencelarni olib tashlaydi.
        
        Args:
            audio: Input audio
            target_silence_ratio: Maqsad silence nisbati (0-1)
            
        Returns:
            Tuple: Aggressively trimmed audio va stats
        """
        original_duration = len(audio) / self.sample_rate
        best_audio = audio
        best_duration = original_duration
        
        # Turli thresholdlar bilan sinash
        thresholds = [-45, -40, -35, -30, -25]
        
        for threshold in thresholds:
            self.silence_threshold_db = threshold
            
            processed, _ = self.full_trim(audio.copy(), use_adaptive=False, remove_internal=True)
            processed_duration = len(processed) / self.sample_rate
            
            # Silence ratio hisoblash
            segments = self.detect_all_segments(processed)
            total_silence = sum(s.duration for s in segments if not s.is_speech)
            silence_ratio = total_silence / processed_duration if processed_duration > 0 else 0
            
            if silence_ratio <= target_silence_ratio:
                best_audio = processed
                best_duration = processed_duration
                logger.info(f"Target reached at threshold {threshold}dB, silence ratio: {silence_ratio:.2%}")
                break
            
            # Yaxshiroq natija bo'lsa saqlash
            if processed_duration < best_duration:
                best_audio = processed
                best_duration = processed_duration
        
        stats = {
            'original_duration': original_duration,
            'trimmed_duration': best_duration,
            'reduction_ratio': 1 - (best_duration / original_duration) if original_duration > 0 else 0
        }
        
        return best_audio, stats


# Test
if __name__ == "__main__":
    trimmer = SilenceTrimmer()
    print("Advanced SilenceTrimmer module initialized successfully!")
    
    # Test signal yaratish
    sr = 16000
    duration = 5
    t = np.linspace(0, duration, sr * duration)
    
    # Nutq simulyatsiyasi (sinus) + silence
    audio = np.zeros(sr * duration)
    audio[sr*0:sr*1] = 0  # 1s silence (boshi)
    audio[sr*1:sr*2] = np.sin(2 * np.pi * 440 * t[sr*1:sr*2]) * 0.5  # Nutq
    audio[sr*2:sr*3] = 0  # 1s silence (o'rtada)
    audio[sr*3:sr*4] = np.sin(2 * np.pi * 440 * t[sr*3:sr*4]) * 0.5  # Nutq
    audio[sr*4:sr*5] = 0  # 1s silence (oxiri)
    
    trimmed, stats = trimmer.full_trim(audio)
    print(f"\nTest results:")
    print(f"Original: {stats['original_duration']:.2f}s")
    print(f"Trimmed: {stats['final_duration']:.2f}s")
    print(f"Reduction: {stats['reduction_percent']:.1f}%")
