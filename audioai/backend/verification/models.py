"""
AudioAI - Verification Models
Pydantic models for verification module

Bu fayl verification moduli uchun barcha
data modellarini o'z ichiga oladi.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class VerificationStatus(str, Enum):
    """
    Audio verification natijasi holati.
    
    Similarity score asosida:
    - valid: >= 0.90
    - warning: 0.75 - 0.89
    - reject: < 0.75
    """
    VALID = "valid"
    WARNING = "warning"
    REJECT = "reject"


class TaskStatus(str, Enum):
    """
    Task processing holati.
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BatchJobStatus(str, Enum):
    """
    Batch job umumiy holati.
    """
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"  # Ba'zilari muvaffaqiyatli, ba'zilari xato
    FAILED = "failed"


class WordTimestamp(BaseModel):
    """
    So'z va uning vaqt belgilari.
    
    Attributes:
        word: So'z matni
        start: Boshlanish vaqti (sekund)
        end: Tugash vaqti (sekund)
        confidence: Ishonchlilik darajasi (0-1)
    """
    word: str
    start: float
    end: float
    confidence: Optional[float] = None


class VerificationResult(BaseModel):
    """
    Bitta audio fayl uchun verification natijasi.
    
    Attributes:
        audio_name: Original fayl nomi (o'zgartirilmagan)
        transcription: Whisper tomonidan aniqlangan matn
        reference_text: Reference matn
        similarity: Similarity score (0-1)
        status: valid/warning/reject
        missing_words: Reference da bor, lekin audioda yo'q so'zlar
        extra_words: Audioda bor, lekin reference da yo'q so'zlar
        word_timestamps: Har bir so'z uchun vaqt belgilari
        processing_time: Processing vaqti (sekund)
        error: Xato xabari (agar bo'lsa)
    """
    audio_name: str
    transcription: Optional[str] = None
    reference_text: Optional[str] = None
    similarity: float = 0.0
    status: VerificationStatus = VerificationStatus.REJECT
    missing_words: List[str] = Field(default_factory=list)
    extra_words: List[str] = Field(default_factory=list)
    word_timestamps: List[WordTimestamp] = Field(default_factory=list)
    processing_time: Optional[float] = None
    error: Optional[str] = None
    
    class Config:
        use_enum_values = True


class AudioTaskResult(BaseModel):
    """
    Bitta audio task natijasi (batch ichida).
    
    Attributes:
        task_id: Unique task ID
        audio_name: Audio fayl nomi
        status: Task holati
        progress: Progress (0-100)
        result: Verification natijasi
        error: Xato xabari
        created_at: Yaratilgan vaqt
        completed_at: Tugallangan vaqt
    """
    task_id: str
    audio_name: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    result: Optional[VerificationResult] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class BatchJobResponse(BaseModel):
    """
    Batch job yaratish response.
    
    Attributes:
        job_id: Unique job ID
        total_files: Umumiy fayllar soni
        reference_text: Reference matn (qisqartirilgan)
        status: Job holati
        message: Xabar
    """
    job_id: str
    total_files: int
    reference_text: str
    status: BatchJobStatus = BatchJobStatus.QUEUED
    message: str = "Job created successfully"
    
    class Config:
        use_enum_values = True


class BatchStatusResponse(BaseModel):
    """
    Batch job status response.
    
    Attributes:
        job_id: Job ID
        status: Umumiy holat
        total_tasks: Umumiy tasklar soni
        completed_tasks: Tugallangan tasklar
        failed_tasks: Xato bo'lgan tasklar
        progress: Umumiy progress (0-100)
        tasks: Individual task statuslari
    """
    job_id: str
    status: BatchJobStatus
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    progress: float
    tasks: List[AudioTaskResult] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    estimated_time_remaining: Optional[float] = None
    
    class Config:
        use_enum_values = True


class BatchResultResponse(BaseModel):
    """
    Batch job final results.
    
    Attributes:
        job_id: Job ID
        status: Final status
        summary: Umumiy statistika
        results: Barcha natijalar
    """
    job_id: str
    status: BatchJobStatus
    summary: Dict[str, Any]
    results: List[VerificationResult] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class VerifyAudiosRequest(BaseModel):
    """
    Verify audios API request body (agar JSON ishlatilsa).
    """
    reference_text: str
    options: Optional[Dict[str, Any]] = None


# Threshold constants
SIMILARITY_THRESHOLDS = {
    'valid': 0.90,      # >= 0.90 = valid
    'warning': 0.75,    # 0.75 - 0.89 = warning
    # < 0.75 = reject
}


def get_verification_status(similarity: float) -> VerificationStatus:
    """
    Similarity score asosida status aniqlash.
    
    Args:
        similarity: Similarity score (0-1)
        
    Returns:
        VerificationStatus: valid, warning, yoki reject
    """
    if similarity >= SIMILARITY_THRESHOLDS['valid']:
        return VerificationStatus.VALID
    elif similarity >= SIMILARITY_THRESHOLDS['warning']:
        return VerificationStatus.WARNING
    else:
        return VerificationStatus.REJECT
