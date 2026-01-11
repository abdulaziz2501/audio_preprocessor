"""
AudioAI - Verification API Router
FastAPI endpoints for Audio-Text Verification

API Endpoints:
- POST /verify-audios: Upload multiple audios + one text
- GET /verify-status/{job_id}: Return progress & completion state
- GET /verify-result/{job_id}: Return final per-audio results
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
import logging

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from .models import (
    BatchJobResponse,
    BatchStatusResponse,
    BatchResultResponse,
    BatchJobStatus,
    VerificationResult
)
from .batch_processor import get_batch_processor, BatchProcessor
from .service import process_single_audio, get_verification_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Router yaratish
router = APIRouter(prefix="/api", tags=["verification"])

# Upload directory
VERIFY_UPLOAD_DIR = Path(__file__).parent.parent / "uploads" / "verify"
VERIFY_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed extensions
ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.ogg', '.flac', '.m4a'}

# Max file size (100 MB)
MAX_FILE_SIZE = 100 * 1024 * 1024


def get_processor() -> BatchProcessor:
    """
    BatchProcessor instance olish va configure qilish.
    """
    processor = get_batch_processor(max_workers=4)
    processor.set_processor(process_single_audio)
    return processor


@router.post("/verify-audios", response_model=BatchJobResponse)
async def verify_audios(
    background_tasks: BackgroundTasks,
    reference_text: str = Form(..., description="Reference matn"),
    audio_files: List[UploadFile] = File(..., description="Audio fayllar"),
    language: str = Form("auto", description="Til kodi (auto, uz, ru, en, ...)"),
    whisper_model: str = Form("base", description="Whisper model (tiny, base, small, medium, large-v2)"),
    preprocess: bool = Form(True, description="Preprocessing qilish"),
    denoise: bool = Form(True, description="Noise removal"),
    trim_silence: bool = Form(True, description="Silence trimming")
):
    """
    Bir nechta audio fayllarni reference text bilan verify qilish.
    
    Bu endpoint darhol job_id qaytaradi va processing background da davom etadi.
    
    **Parameters:**
    - **reference_text**: Reference matn (barcha audio fayllar uchun bir xil)
    - **audio_files**: Audio fayllar (WAV, MP3, OGG, FLAC, M4A)
    - **language**: Til kodi (auto = avtomatik aniqlash)
    - **whisper_model**: Whisper model nomi
    - **preprocess**: Preprocessing qilish (denoise, trim)
    - **denoise**: Noise removal
    - **trim_silence**: Silence trimming
    
    **Returns:**
    - **job_id**: Unique job ID
    - **total_files**: Umumiy fayllar soni
    - **status**: Job holati
    """
    
    # Validate audio files
    if not audio_files or len(audio_files) == 0:
        raise HTTPException(status_code=400, detail="Kamida bitta audio fayl yuklang")
    
    if not reference_text or not reference_text.strip():
        raise HTTPException(status_code=400, detail="Reference matn bo'sh bo'lmasligi kerak")
    
    # Job ID yaratish
    job_id = str(uuid.uuid4())
    job_dir = VERIFY_UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    
    # Fayllarni saqlash va validate qilish
    audio_info_list = []
    
    for audio_file in audio_files:
        # Extension tekshirish
        if not audio_file.filename:
            continue
            
        ext = Path(audio_file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            # Skip invalid files but continue
            logger.warning(f"Skipping invalid file: {audio_file.filename}")
            continue
        
        # Faylni saqlash (original nom bilan)
        file_path = job_dir / audio_file.filename
        
        try:
            content = await audio_file.read()
            
            # Size tekshirish
            if len(content) > MAX_FILE_SIZE:
                logger.warning(f"File too large: {audio_file.filename}")
                continue
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            audio_info_list.append({
                'path': str(file_path),
                'name': audio_file.filename  # Original nom saqlanadi!
            })
            
        except Exception as e:
            logger.error(f"Error saving file {audio_file.filename}: {e}")
            continue
    
    if not audio_info_list:
        # Cleanup
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(
            status_code=400, 
            detail="Hech qanday valid audio fayl topilmadi"
        )
    
    # Processing options
    options = {
        'language': language,
        'whisper_model': whisper_model,
        'preprocess': preprocess,
        'denoise': denoise,
        'trim_silence': trim_silence,
        'normalize': True
    }
    
    # Batch job yaratish
    processor = get_processor()
    job = processor.create_job(
        audio_files=audio_info_list,
        reference_text=reference_text.strip(),
        options=options
    )
    
    # Background task boshlash
    background_tasks.add_task(start_job_background, processor, job.job_id)
    
    logger.info(f"Created verification job {job.job_id} with {len(audio_info_list)} files")
    
    return BatchJobResponse(
        job_id=job.job_id,
        total_files=len(audio_info_list),
        reference_text=reference_text[:100] + "..." if len(reference_text) > 100 else reference_text,
        status=BatchJobStatus.QUEUED,
        message=f"Job yaratildi. {len(audio_info_list)} ta fayl processing uchun navbatda."
    )


async def start_job_background(processor: BatchProcessor, job_id: str):
    """
    Background task: Job ni boshlash.
    """
    try:
        await processor.start_job(job_id)
    except Exception as e:
        logger.error(f"Error starting job {job_id}: {e}")


@router.get("/verify-status/{job_id}", response_model=BatchStatusResponse)
async def get_verify_status(job_id: str):
    """
    Verification job statusini olish.
    
    **Parameters:**
    - **job_id**: Job ID
    
    **Returns:**
    - **status**: Job holati (queued, running, completed, partial, failed)
    - **progress**: Umumiy progress (0-100%)
    - **total_tasks**: Umumiy tasklar soni
    - **completed_tasks**: Tugallangan tasklar
    - **failed_tasks**: Xato bo'lgan tasklar
    - **tasks**: Har bir task holati
    """
    
    processor = get_processor()
    status = processor.get_job_status(job_id)
    
    if status is None:
        raise HTTPException(status_code=404, detail="Job topilmadi")
    
    return BatchStatusResponse(
        job_id=status['job_id'],
        status=BatchJobStatus(status['status']),
        total_tasks=status['total_tasks'],
        completed_tasks=status['completed_tasks'],
        failed_tasks=status['failed_tasks'],
        progress=status['progress'],
        tasks=status['tasks'],
        estimated_time_remaining=status.get('estimated_time_remaining')
    )


@router.get("/verify-result/{job_id}", response_model=BatchResultResponse)
async def get_verify_result(job_id: str):
    """
    Verification job natijalarini olish.
    
    Job tugallangandan keyin to'liq natijalarni qaytaradi.
    
    **Parameters:**
    - **job_id**: Job ID
    
    **Returns:**
    - **status**: Final status
    - **summary**: Umumiy statistika
        - total_processed
        - valid_count
        - warning_count
        - reject_count
        - average_similarity
    - **results**: Har bir audio uchun natija
        - audio_name (original nom)
        - transcription
        - similarity
        - status (valid/warning/reject)
        - missing_words
        - extra_words
        - word_timestamps
    """
    
    processor = get_processor()
    result = processor.get_job_results(job_id)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Job topilmadi")
    
    # Job holati tekshirish
    job = processor.get_job(job_id)
    if job and job.status == "running":
        raise HTTPException(
            status_code=202, 
            detail="Job hali davom etmoqda. Status endpoint dan foydalaning."
        )
    
    return BatchResultResponse(
        job_id=result['job_id'],
        status=BatchJobStatus(result['status']),
        summary=result['summary'],
        results=result['results']
    )


@router.delete("/verify-job/{job_id}")
async def cancel_verify_job(job_id: str):
    """
    Verification job ni bekor qilish.
    
    Faqat running yoki queued holatdagi job larni bekor qilish mumkin.
    
    **Parameters:**
    - **job_id**: Job ID
    
    **Returns:**
    - **message**: Natija xabari
    """
    
    processor = get_processor()
    success = processor.cancel_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="Job bekor qilib bo'lmaydi (tugallangan yoki topilmadi)"
        )
    
    # Job fayllarini tozalash
    job_dir = VERIFY_UPLOAD_DIR / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir, ignore_errors=True)
    
    return {"message": "Job bekor qilindi", "job_id": job_id}


@router.post("/verify-single")
async def verify_single_audio(
    reference_text: str = Form(...),
    audio_file: UploadFile = File(...),
    language: str = Form("auto"),
    whisper_model: str = Form("base"),
    preprocess: bool = Form(True)
):
    """
    Bitta audio faylni verify qilish (sync endpoint).
    
    Kichik fayllar uchun - natija darhol qaytariladi.
    
    **Parameters:**
    - **reference_text**: Reference matn
    - **audio_file**: Audio fayl
    - **language**: Til kodi
    - **whisper_model**: Whisper model
    - **preprocess**: Preprocessing qilish
    
    **Returns:**
    - Verification natijasi
    """
    
    # Validate
    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="Audio fayl nomi yo'q")
    
    ext = Path(audio_file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Ruxsat berilmagan fayl formati")
    
    # Temp fayl saqlash
    temp_id = str(uuid.uuid4())
    temp_dir = VERIFY_UPLOAD_DIR / temp_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = temp_dir / audio_file.filename
    
    try:
        content = await audio_file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Verify
        options = {
            'language': language,
            'whisper_model': whisper_model,
            'preprocess': preprocess,
            'denoise': True,
            'trim_silence': True,
            'normalize': True
        }
        
        result = process_single_audio(
            str(file_path),
            reference_text.strip(),
            options
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Single verification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.get("/verify-models")
async def get_available_models():
    """
    Mavjud Whisper modellar ro'yxati.
    
    **Returns:**
    - **models**: Model nomlari va ma'lumotlari
    """
    
    models = {
        'tiny': {'vram_gb': 1, 'speed': 'fastest', 'accuracy': 'low'},
        'base': {'vram_gb': 1, 'speed': 'fast', 'accuracy': 'medium'},
        'small': {'vram_gb': 2, 'speed': 'medium', 'accuracy': 'good'},
        'medium': {'vram_gb': 5, 'speed': 'slow', 'accuracy': 'high'},
        'large-v2': {'vram_gb': 10, 'speed': 'slowest', 'accuracy': 'best'},
        'large-v3': {'vram_gb': 10, 'speed': 'slowest', 'accuracy': 'best'}
    }
    
    return {
        'models': models,
        'recommended': 'base',
        'default': 'base'
    }


# Cleanup task (periodic cleanup uchun)
@router.post("/verify-cleanup")
async def cleanup_old_jobs(max_age_hours: int = 24):
    """
    Eski job larni tozalash.
    
    **Parameters:**
    - **max_age_hours**: Maksimal yosh (soatda)
    
    **Returns:**
    - **cleaned_jobs**: Tozalangan job lar soni
    """
    
    processor = get_processor()
    cleaned = processor.cleanup_old_jobs(max_age_hours)
    
    # Fayl papkalarini ham tozalash
    cleaned_dirs = 0
    if VERIFY_UPLOAD_DIR.exists():
        for job_dir in VERIFY_UPLOAD_DIR.iterdir():
            if job_dir.is_dir():
                job_id = job_dir.name
                job = processor.get_job(job_id)
                if job is None:
                    # Job mavjud emas, papkani o'chirish
                    shutil.rmtree(job_dir, ignore_errors=True)
                    cleaned_dirs += 1
    
    return {
        "message": "Cleanup completed",
        "cleaned_jobs": cleaned,
        "cleaned_directories": cleaned_dirs
    }


# Health check
@router.get("/verify-health")
async def verification_health():
    """
    Verification service health check.
    """
    import torch
    
    return {
        "status": "healthy",
        "service": "verification",
        "gpu_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    }
