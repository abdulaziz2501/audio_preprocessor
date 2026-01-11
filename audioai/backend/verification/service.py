"""
AudioAI - Verification Service
Main verification orchestration service

Bu modul barcha verification komponentlarini
birlashtiradi va asosiy API service sifatida ishlaydi.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from .models import (
    VerificationResult,
    WordTimestamp,
    VerificationStatus,
    get_verification_status
)
from .transcriber import WhisperTranscriber, get_transcriber
from .comparator import TextComparator
from .aligner import ForcedAligner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VerificationService:
    """
    Audio-Text Verification Service.
    
    Audio fayllarni reference text bilan solishtirish
    va STT dataset validation uchun asosiy service.
    
    Pipeline:
    1. Audio preprocessing (mavjud pipeline ishlatiladi)
    2. Whisper transcription
    3. Text comparison
    4. Forced alignment
    5. Similarity scoring
    6. Status determination
    
    Attributes:
        transcriber: Whisper transcriber
        comparator: Text comparator
        aligner: Forced aligner
        preprocess: Preprocessing ishlatish
    """
    
    def __init__(
        self,
        whisper_model: str = "base",
        language: str = "auto",
        use_preprocessing: bool = True
    ):
        """
        VerificationService ni ishga tushirish.
        
        Args:
            whisper_model: Whisper model nomi
            language: Til kodi
            use_preprocessing: Mavjud preprocessing pipeline ishlatish
        """
        self.transcriber = WhisperTranscriber(
            model_name=whisper_model,
            language=language
        )
        self.comparator = TextComparator()
        self.aligner = ForcedAligner(language=language)
        self.use_preprocessing = use_preprocessing
        self.language = language
        
        logger.info(
            f"VerificationService initialized: model={whisper_model}, "
            f"language={language}, preprocessing={use_preprocessing}"
        )
    
    def verify_audio(
        self,
        audio_path: str,
        reference_text: str,
        options: Optional[Dict[str, Any]] = None
    ) -> VerificationResult:
        """
        Bitta audio faylni verify qilish.
        
        Args:
            audio_path: Audio fayl yo'li
            reference_text: Reference matn
            options: Qo'shimcha options
            
        Returns:
            VerificationResult: Verification natijasi
        """
        options = options or {}
        start_time = time.time()
        
        audio_name = Path(audio_path).name
        
        logger.info(f"Verifying audio: {audio_name}")
        
        try:
            # 1. Preprocessing (agar kerak bo'lsa)
            processed_audio_path = audio_path
            if self.use_preprocessing and options.get('preprocess', True):
                processed_audio_path = self._preprocess_audio(audio_path, options)
            
            # 2. Transcription
            transcription, word_timestamps = self._transcribe(
                processed_audio_path, 
                options
            )
            
            # 3. Text comparison
            comparison = self.comparator.compare(transcription, reference_text)
            
            # 4. Similarity va status
            similarity = comparison['similarity']
            status = get_verification_status(similarity)
            
            # 5. Word timestamps
            timestamps = [
                WordTimestamp(
                    word=w['word'],
                    start=w['start'],
                    end=w['end'],
                    confidence=w.get('confidence')
                )
                for w in word_timestamps
            ]
            
            processing_time = time.time() - start_time
            
            result = VerificationResult(
                audio_name=audio_name,
                transcription=transcription,
                reference_text=reference_text,
                similarity=similarity,
                status=status,
                missing_words=comparison['missing_words'],
                extra_words=comparison['extra_words'],
                word_timestamps=timestamps,
                processing_time=processing_time
            )
            
            logger.info(
                f"Verification completed for {audio_name}: "
                f"similarity={similarity:.2%}, status={status.value}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Verification error for {audio_name}: {e}")
            
            return VerificationResult(
                audio_name=audio_name,
                reference_text=reference_text,
                similarity=0.0,
                status=VerificationStatus.REJECT,
                error=str(e),
                processing_time=time.time() - start_time
            )
    
    def _preprocess_audio(
        self,
        audio_path: str,
        options: Dict[str, Any]
    ) -> str:
        """
        Mavjud preprocessing pipeline ni ishlatish.
        
        Args:
            audio_path: Audio fayl yo'li
            options: Processing options
            
        Returns:
            str: Processed audio path
        """
        try:
            # Import existing audio processing modules
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            
            from audio_processing import AudioDenoiser, SilenceTrimmer
            
            import librosa
            import soundfile as sf
            import numpy as np
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)
            
            # Denoise (agar kerak bo'lsa)
            if options.get('denoise', True):
                denoiser = AudioDenoiser(sample_rate=sr)
                audio = denoiser.apply_highpass_filter(audio)
                audio = denoiser.spectral_gate(audio)
            
            # Trim silence (agar kerak bo'lsa)
            if options.get('trim_silence', True):
                trimmer = SilenceTrimmer(sample_rate=sr)
                audio, _ = trimmer.full_trim(audio)
            
            # Normalize
            if options.get('normalize', True):
                denoiser = AudioDenoiser(sample_rate=sr)
                audio = denoiser.normalize_audio(audio)
            
            # Save to temp file
            temp_dir = Path(audio_path).parent
            temp_path = temp_dir / f"_processed_{Path(audio_path).name}"
            sf.write(str(temp_path), audio, sr)
            
            return str(temp_path)
            
        except ImportError as e:
            logger.warning(f"Preprocessing modules not available: {e}")
            return audio_path
        except Exception as e:
            logger.warning(f"Preprocessing failed, using original: {e}")
            return audio_path
    
    def _transcribe(
        self,
        audio_path: str,
        options: Dict[str, Any]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Audio ni transcribe qilish.
        
        Args:
            audio_path: Audio fayl yo'li
            options: Transcription options
            
        Returns:
            Tuple[str, List]: (transcription text, word timestamps)
        """
        language = options.get('language', self.language)
        
        result = self.transcriber.transcribe(
            audio_path,
            language=language if language != "auto" else None,
            word_timestamps=True
        )
        
        text = result.get('text', '')
        
        # Word timestamps
        word_timestamps = []
        for segment in result.get('segments', []):
            for word in segment.get('words', []):
                word_timestamps.append({
                    'word': word['word'].strip(),
                    'start': word['start'],
                    'end': word['end'],
                    'confidence': word.get('probability', 1.0)
                })
        
        return text, word_timestamps
    
    def verify_batch(
        self,
        audio_files: List[Dict[str, str]],
        reference_text: str,
        options: Optional[Dict[str, Any]] = None
    ) -> List[VerificationResult]:
        """
        Bir nechta audio fayllarni verify qilish (sync).
        
        Args:
            audio_files: Audio fayllar [{'path': ..., 'name': ...}, ...]
            reference_text: Reference matn
            options: Processing options
            
        Returns:
            List[VerificationResult]: Barcha natijalar
        """
        results = []
        
        for audio_info in audio_files:
            result = self.verify_audio(
                audio_info['path'],
                reference_text,
                options
            )
            results.append(result)
        
        return results
    
    def get_summary(
        self,
        results: List[VerificationResult]
    ) -> Dict[str, Any]:
        """
        Natijalar summary statistikasi.
        
        Args:
            results: Verification natijalari
            
        Returns:
            dict: Summary statistika
        """
        if not results:
            return {
                'total': 0,
                'valid': 0,
                'warning': 0,
                'reject': 0,
                'failed': 0,
                'average_similarity': 0
            }
        
        valid = sum(1 for r in results if r.status == VerificationStatus.VALID)
        warning = sum(1 for r in results if r.status == VerificationStatus.WARNING)
        reject = sum(1 for r in results if r.status == VerificationStatus.REJECT)
        failed = sum(1 for r in results if r.error is not None)
        
        similarities = [r.similarity for r in results if r.error is None]
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0
        
        return {
            'total': len(results),
            'valid': valid,
            'warning': warning,
            'reject': reject,
            'failed': failed,
            'average_similarity': avg_similarity,
            'valid_percentage': valid / len(results) * 100 if results else 0
        }


# Singleton-like instance getter
_verification_service: Optional[VerificationService] = None


def get_verification_service(
    whisper_model: str = "base",
    language: str = "auto"
) -> VerificationService:
    """
    Global VerificationService instance olish.
    
    Args:
        whisper_model: Whisper model
        language: Til
        
    Returns:
        VerificationService instance
    """
    global _verification_service
    
    if _verification_service is None:
        _verification_service = VerificationService(
            whisper_model=whisper_model,
            language=language
        )
    
    return _verification_service


def process_single_audio(
    audio_path: str,
    reference_text: str,
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Bitta audio ni processing qilish (batch processor uchun).
    
    Bu funksiya BatchProcessor._process_func sifatida ishlatiladi.
    
    Args:
        audio_path: Audio fayl yo'li
        reference_text: Reference matn
        options: Processing options
        
    Returns:
        dict: Verification natijasi (dict formatda)
    """
    service = get_verification_service(
        whisper_model=options.get('whisper_model', 'base'),
        language=options.get('language', 'auto')
    )
    
    result = service.verify_audio(audio_path, reference_text, options)
    
    # Dict ga aylantirish (serialization uchun)
    return {
        'audio_name': result.audio_name,
        'transcription': result.transcription,
        'reference_text': result.reference_text,
        'similarity': result.similarity,
        'status': result.status.value if isinstance(result.status, VerificationStatus) else result.status,
        'missing_words': result.missing_words,
        'extra_words': result.extra_words,
        'word_timestamps': [
            {'word': w.word, 'start': w.start, 'end': w.end, 'confidence': w.confidence}
            for w in result.word_timestamps
        ],
        'processing_time': result.processing_time,
        'error': result.error
    }


# Test
if __name__ == "__main__":
    service = VerificationService(whisper_model="base")
    print("VerificationService initialized successfully!")
