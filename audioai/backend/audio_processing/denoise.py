"""
AudioAI - Noise Reduction Module
Background noise olib tashlash uchun spectral gating algorithm

Bu modul audio fayllardan background noise (shovqin) ni 
olib tashlash uchun ishlatiladi.
"""

import numpy as np
import librosa
import soundfile as sf
from scipy.signal import butter, filtfilt
from typing import Tuple, Optional
import logging

# Logger sozlash
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioDenoiser:
    """
    Audio fayllardan noise olib tashlash uchun class.
    
    Spectral gating va butterworth filter kombinatsiyasidan foydalanadi.
    STT dataset tayyorlash uchun optimallashtirilgan.
    
    Attributes:
        sample_rate (int): Audio sample rate (default: 16000 Hz)
        noise_reduce_strength (float): Noise reduction kuchi (0.0 - 1.0)
        highpass_freq (int): High-pass filter chastotasi
    """
    
    def __init__(
        self, 
        sample_rate: int = 16000,
        noise_reduce_strength: float = 0.7,
        highpass_freq: int = 80
    ):
        """
        AudioDenoiser ni ishga tushirish.
        
        Args:
            sample_rate: Audio sample rate Hz da
            noise_reduce_strength: Noise reduction intensivligi (0-1)
            highpass_freq: Past chastotalarni kesish chegarasi
        """
        self.sample_rate = sample_rate
        self.noise_reduce_strength = noise_reduce_strength
        self.highpass_freq = highpass_freq
        
        logger.info(f"AudioDenoiser initialized: SR={sample_rate}, strength={noise_reduce_strength}")
    
    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        Audio faylni yuklash va mono formatga o'tkazish.
        
        Args:
            file_path: Audio fayl yo'li
            
        Returns:
            Tuple[np.ndarray, int]: Audio data va sample rate
        """
        try:
            # Audio yuklash va sample rate ga moslashtirish
            audio, sr = librosa.load(file_path, sr=self.sample_rate, mono=True)
            logger.info(f"Loaded audio: {file_path}, duration: {len(audio)/sr:.2f}s")
            return audio, sr
        except Exception as e:
            logger.error(f"Audio yuklashda xato: {e}")
            raise
    
    def save_audio(self, audio: np.ndarray, file_path: str) -> None:
        """
        Audio faylni saqlash.
        
        Args:
            audio: Audio data numpy array
            file_path: Saqlash yo'li
        """
        try:
            sf.write(file_path, audio, self.sample_rate)
            logger.info(f"Saved audio: {file_path}")
        except Exception as e:
            logger.error(f"Audio saqlashda xato: {e}")
            raise
    
    def apply_highpass_filter(self, audio: np.ndarray) -> np.ndarray:
        """
        High-pass filter qo'llash - past chastota shovqinlarini olib tashlash.
        
        Args:
            audio: Input audio signal
            
        Returns:
            np.ndarray: Filterlangan audio
        """
        # Butterworth high-pass filter yaratish
        nyquist = self.sample_rate / 2
        normalized_cutoff = self.highpass_freq / nyquist
        
        # Filter koeffitsientlarini hisoblash
        b, a = butter(4, normalized_cutoff, btype='high')
        
        # Filterni qo'llash
        filtered_audio = filtfilt(b, a, audio)
        
        return filtered_audio
    
    def spectral_gate(
        self, 
        audio: np.ndarray,
        noise_sample_duration: float = 0.5
    ) -> np.ndarray:
        """
        Spectral gating orqali noise reduction.
        
        Audioning boshidagi qismidan noise profilini oladi
        va uni butun signaldan olib tashlaydi.
        
        Args:
            audio: Input audio signal
            noise_sample_duration: Noise sample olish davomiyligi (sekundda)
            
        Returns:
            np.ndarray: Denoised audio
        """
        # STFT parametrlari
        n_fft = 2048
        hop_length = 512
        
        # STFT qo'llash
        stft = librosa.stft(audio, n_fft=n_fft, hop_length=hop_length)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Noise sample olish (birinchi N sekunddan)
        noise_frames = int(noise_sample_duration * self.sample_rate / hop_length)
        noise_frames = max(1, min(noise_frames, magnitude.shape[1] // 4))
        
        # Noise profili - noise samplening o'rtacha spektri
        noise_profile = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
        
        # Noise threshold hisoblash
        threshold = noise_profile * (1 + self.noise_reduce_strength * 2)
        
        # Spectral gating qo'llash
        # Signal noise threshold dan past bo'lsa, kamaytirish
        gain = np.maximum(0, 1 - (threshold / (magnitude + 1e-10)))
        gain = np.power(gain, self.noise_reduce_strength)
        
        # Yangi magnitude hisoblash
        denoised_magnitude = magnitude * gain
        
        # Fazani qaytarish va ISTFT
        denoised_stft = denoised_magnitude * np.exp(1j * phase)
        denoised_audio = librosa.istft(denoised_stft, hop_length=hop_length)
        
        return denoised_audio
    
    def normalize_audio(
        self, 
        audio: np.ndarray, 
        target_db: float = -3.0
    ) -> np.ndarray:
        """
        Audio normalizatsiya - optimal balandlikka keltirish.
        
        Args:
            audio: Input audio
            target_db: Maqsad balandlik dB da
            
        Returns:
            np.ndarray: Normallashtirilgan audio
        """
        # RMS hisoblash
        rms = np.sqrt(np.mean(audio ** 2))
        
        if rms < 1e-10:
            return audio
        
        # Maqsad RMS
        target_rms = 10 ** (target_db / 20)
        
        # Scaling faktor
        scale = target_rms / rms
        
        # Clipping oldini olish
        normalized = audio * scale
        normalized = np.clip(normalized, -1.0, 1.0)
        
        return normalized
    
    def process(
        self, 
        input_path: str, 
        output_path: Optional[str] = None
    ) -> Tuple[np.ndarray, dict]:
        """
        To'liq noise reduction pipeline.
        
        Args:
            input_path: Input audio fayl yo'li
            output_path: Output fayl yo'li (optional)
            
        Returns:
            Tuple: Processed audio va statistika
        """
        logger.info(f"Processing started: {input_path}")
        
        # 1. Audio yuklash
        audio, sr = self.load_audio(input_path)
        original_duration = len(audio) / sr
        
        # 2. High-pass filter
        audio = self.apply_highpass_filter(audio)
        
        # 3. Spectral gating
        audio = self.spectral_gate(audio)
        
        # 4. Normalizatsiya
        audio = self.normalize_audio(audio)
        
        # Statistika
        stats = {
            'original_duration': original_duration,
            'processed_duration': len(audio) / sr,
            'sample_rate': sr,
            'noise_reduction_applied': True
        }
        
        # Saqlash (agar path berilgan bo'lsa)
        if output_path:
            self.save_audio(audio, output_path)
        
        logger.info(f"Processing completed: duration={stats['processed_duration']:.2f}s")
        
        return audio, stats


# Standalone test uchun
if __name__ == "__main__":
    denoiser = AudioDenoiser()
    print("AudioDenoiser module initialized successfully!")
