"""
AudioAI - Voice Activity Detection (VAD) Module
Nutq segmentlarini aniqlash uchun modul

Bu modul audiodagi nutq qismlarini silence qismlaridan
ajratib olish uchun ishlatiladi.
"""

import numpy as np
import librosa
from typing import List, Tuple, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SpeechSegment:
    """
    Nutq segmenti ma'lumotlari.
    
    Attributes:
        start: Boshlang'ich vaqt (sekund)
        end: Tugash vaqti (sekund)
        duration: Davomiylik (sekund)
        energy: Segment energiyasi
    """
    start: float
    end: float
    duration: float
    energy: float


class VoiceActivityDetector:
    """
    Voice Activity Detection (VAD) - Nutq faoliyatini aniqlash.
    
    Energy-based va zero-crossing rate kombinatsiyasidan foydalanadi.
    STT dataset uchun optimallashtirilgan.
    
    Attributes:
        sample_rate (int): Audio sample rate
        frame_duration_ms (int): Har bir frame davomiyligi (ms)
        energy_threshold (float): Energia chegarasi (0-1)
        min_speech_duration (float): Minimal nutq davomiyligi (sekund)
        min_silence_duration (float): Minimal silence davomiyligi (sekund)
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        frame_duration_ms: int = 30,
        energy_threshold: float = 0.02,
        min_speech_duration: float = 0.1,
        min_silence_duration: float = 0.3
    ):
        """
        VAD ni ishga tushirish.
        
        Args:
            sample_rate: Audio sample rate
            frame_duration_ms: Frame davomiyligi millisekund
            energy_threshold: Nutq/silence chegarasi
            min_speech_duration: Minimal nutq davomiyligi
            min_silence_duration: Minimal silence davomiyligi
        """
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.energy_threshold = energy_threshold
        self.min_speech_duration = min_speech_duration
        self.min_silence_duration = min_silence_duration
        
        # Frame hajmi
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        
        logger.info(f"VAD initialized: frame_size={self.frame_size}, threshold={energy_threshold}")
    
    def calculate_frame_energy(self, frame: np.ndarray) -> float:
        """
        Frame energiyasini hisoblash (RMS).
        
        Args:
            frame: Audio frame
            
        Returns:
            float: Frame RMS energiyasi
        """
        return np.sqrt(np.mean(frame ** 2))
    
    def calculate_zcr(self, frame: np.ndarray) -> float:
        """
        Zero Crossing Rate hisoblash.
        
        Nutqda odatda ZCR yuqori bo'ladi.
        
        Args:
            frame: Audio frame
            
        Returns:
            float: Zero crossing rate
        """
        signs = np.sign(frame)
        signs[signs == 0] = 1
        crossings = np.abs(np.diff(signs))
        return np.sum(crossings) / (2 * len(frame))
    
    def get_adaptive_threshold(self, audio: np.ndarray) -> float:
        """
        Adaptiv threshold hisoblash.
        
        Audioning boshidagi silence qismidan threshold oladi.
        
        Args:
            audio: Input audio
            
        Returns:
            float: Adaptiv threshold qiymati
        """
        # Birinchi 0.5 sekundni olish (silence deb faraz qilamiz)
        silence_samples = int(0.5 * self.sample_rate)
        silence_samples = min(silence_samples, len(audio) // 4)
        
        if silence_samples < self.frame_size:
            return self.energy_threshold
        
        silence_part = audio[:silence_samples]
        
        # Silence energiyasini hisoblash
        n_frames = len(silence_part) // self.frame_size
        energies = []
        
        for i in range(n_frames):
            start = i * self.frame_size
            end = start + self.frame_size
            frame = silence_part[start:end]
            energies.append(self.calculate_frame_energy(frame))
        
        if len(energies) > 0:
            # Threshold = mean + 2 * std (silence energiyasidan yuqori)
            mean_energy = np.mean(energies)
            std_energy = np.std(energies)
            adaptive_threshold = mean_energy + 2 * std_energy
            
            # Minimal threshold
            adaptive_threshold = max(adaptive_threshold, self.energy_threshold)
            
            logger.info(f"Adaptive threshold: {adaptive_threshold:.4f}")
            return adaptive_threshold
        
        return self.energy_threshold
    
    def detect_speech_frames(
        self, 
        audio: np.ndarray,
        use_adaptive: bool = True
    ) -> List[bool]:
        """
        Har bir frame uchun nutq/silence aniqlash.
        
        Args:
            audio: Input audio
            use_adaptive: Adaptiv threshold ishlatish
            
        Returns:
            List[bool]: Har bir frame uchun True (speech) yoki False (silence)
        """
        # Threshold aniqlash
        if use_adaptive:
            threshold = self.get_adaptive_threshold(audio)
        else:
            threshold = self.energy_threshold
        
        # Framelar bo'yicha tahlil
        n_frames = len(audio) // self.frame_size
        speech_flags = []
        
        for i in range(n_frames):
            start = i * self.frame_size
            end = start + self.frame_size
            frame = audio[start:end]
            
            # Energia tekshirish
            energy = self.calculate_frame_energy(frame)
            
            # ZCR tekshirish (qo'shimcha signal)
            zcr = self.calculate_zcr(frame)
            
            # Nutq aniqlash (energia va ZCR kombinatsiyasi)
            is_speech = energy > threshold and zcr > 0.01
            speech_flags.append(is_speech)
        
        return speech_flags
    
    def smooth_speech_flags(
        self, 
        flags: List[bool],
        min_speech_frames: int,
        min_silence_frames: int
    ) -> List[bool]:
        """
        Speech flaglarni tekislash (smoothing).
        
        Juda qisqa nutq/silence segmentlarini olib tashlash.
        
        Args:
            flags: Raw speech flags
            min_speech_frames: Minimal nutq framelar soni
            min_silence_frames: Minimal silence framelar soni
            
        Returns:
            List[bool]: Smoothed flags
        """
        if len(flags) == 0:
            return flags
        
        smoothed = flags.copy()
        
        # Qisqa silence gaplarni to'ldirish
        i = 0
        while i < len(smoothed):
            if not smoothed[i]:
                # Silence boshlanishi
                j = i
                while j < len(smoothed) and not smoothed[j]:
                    j += 1
                
                # Agar silence juda qisqa bo'lsa, speech qilish
                silence_len = j - i
                if silence_len < min_silence_frames:
                    # Oldingi va keyingi speech bo'lsa
                    if i > 0 and j < len(smoothed):
                        for k in range(i, j):
                            smoothed[k] = True
                
                i = j
            else:
                i += 1
        
        # Qisqa speech segmentlarni olib tashlash
        i = 0
        while i < len(smoothed):
            if smoothed[i]:
                j = i
                while j < len(smoothed) and smoothed[j]:
                    j += 1
                
                speech_len = j - i
                if speech_len < min_speech_frames:
                    for k in range(i, j):
                        smoothed[k] = False
                
                i = j
            else:
                i += 1
        
        return smoothed
    
    def get_speech_segments(
        self, 
        audio: np.ndarray
    ) -> List[SpeechSegment]:
        """
        Nutq segmentlarini aniqlash.
        
        Args:
            audio: Input audio
            
        Returns:
            List[SpeechSegment]: Nutq segmentlari ro'yxati
        """
        # Speech flags aniqlash
        speech_flags = self.detect_speech_frames(audio)
        
        # Minimal frame sonlarini hisoblash
        min_speech_frames = int(self.min_speech_duration * 1000 / self.frame_duration_ms)
        min_silence_frames = int(self.min_silence_duration * 1000 / self.frame_duration_ms)
        
        # Smoothing
        smoothed_flags = self.smooth_speech_flags(
            speech_flags, 
            min_speech_frames, 
            min_silence_frames
        )
        
        # Segmentlarni chiqarish
        segments = []
        i = 0
        
        while i < len(smoothed_flags):
            if smoothed_flags[i]:
                # Speech segment boshlanishi
                start_frame = i
                while i < len(smoothed_flags) and smoothed_flags[i]:
                    i += 1
                end_frame = i
                
                # Vaqtga o'tkazish
                start_time = start_frame * self.frame_duration_ms / 1000
                end_time = end_frame * self.frame_duration_ms / 1000
                duration = end_time - start_time
                
                # Segment energiyasi
                start_sample = start_frame * self.frame_size
                end_sample = min(end_frame * self.frame_size, len(audio))
                segment_audio = audio[start_sample:end_sample]
                energy = self.calculate_frame_energy(segment_audio)
                
                segments.append(SpeechSegment(
                    start=start_time,
                    end=end_time,
                    duration=duration,
                    energy=energy
                ))
            else:
                i += 1
        
        logger.info(f"Found {len(segments)} speech segments")
        return segments
    
    def extract_speech(
        self, 
        audio: np.ndarray,
        padding: float = 0.1
    ) -> Tuple[np.ndarray, List[SpeechSegment]]:
        """
        Faqat nutq qismlarini chiqarish.
        
        Args:
            audio: Input audio
            padding: Har bir segment atrofiga qo'shiladigan padding (sekund)
            
        Returns:
            Tuple: Extracted speech audio va segments
        """
        segments = self.get_speech_segments(audio)
        
        if len(segments) == 0:
            logger.warning("No speech segments found!")
            return audio, segments
        
        # Nutq qismlarini birlashtirish
        speech_parts = []
        padding_samples = int(padding * self.sample_rate)
        
        for segment in segments:
            start_sample = max(0, int(segment.start * self.sample_rate) - padding_samples)
            end_sample = min(len(audio), int(segment.end * self.sample_rate) + padding_samples)
            speech_parts.append(audio[start_sample:end_sample])
        
        # Birlashtirishda kichik pause qo'shish
        pause_samples = int(0.1 * self.sample_rate)
        pause = np.zeros(pause_samples)
        
        combined = []
        for i, part in enumerate(speech_parts):
            combined.append(part)
            if i < len(speech_parts) - 1:
                combined.append(pause)
        
        extracted_audio = np.concatenate(combined)
        
        logger.info(f"Extracted speech: {len(extracted_audio)/self.sample_rate:.2f}s from {len(audio)/self.sample_rate:.2f}s")
        
        return extracted_audio, segments


# Test
if __name__ == "__main__":
    vad = VoiceActivityDetector()
    print("VoiceActivityDetector module initialized successfully!")
