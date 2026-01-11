"""
AudioAI - Verification Module
Audio-Text Verification & Batch Processing for STT Dataset Validation

Bu modul quyidagi funksiyalarni bajaradi:
1. Whisper bilan audio transcription
2. Reference text bilan solishtirish
3. Forced alignment (word-level timestamps)
4. Similarity score hisoblash
5. Batch processing (background workers)
"""

from .transcriber import WhisperTranscriber
from .aligner import ForcedAligner
from .comparator import TextComparator
from .batch_processor import BatchProcessor, VerificationTask
from .service import VerificationService, process_single_audio
from .models import (
    VerificationResult, 
    WordTimestamp, 
    VerificationStatus,
    BatchJobStatus
)

__all__ = [
    'WhisperTranscriber',
    'ForcedAligner', 
    'TextComparator',
    'BatchProcessor',
    'VerificationTask',
    'VerificationService',
    'process_single_audio',
    'VerificationResult',
    'WordTimestamp',
    'VerificationStatus',
    'BatchJobStatus'
]
