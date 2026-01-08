"""
AudioAI - FastAPI Backend Application
STT Dataset uchun Audio Preprocessing API

Bu API quyidagi funksiyalarni bajaradi:
1. Audio fayllarni qabul qilish (upload)
2. Background noise olib tashlash
3. Silence trimming
4. Voice activity detection va speech extraction
5. Processed audio qaytarish
"""

import os
import uuid
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

import numpy as np
import librosa
import soundfile as sf

# Audio processing modullarimiz
from audio_processing.denoise import AudioDenoiser
from audio_processing.vad import VoiceActivityDetector
from audio_processing.trim import SilenceTrimmer

import logging

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============== App Configuration ==============

# Papka yo'llari
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads" / "original"
PROCESSED_DIR = BASE_DIR / "uploads" / "processed"

# Papkalarni yaratish
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Ruxsat berilgan formatlar
ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.ogg', '.flac', '.m4a'}

# Maksimal fayl hajmi (50 MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# Processing holatini saqlash
processing_status = {}


# ============== FastAPI App ==============

app = FastAPI(
    title="AudioAI - STT Preprocessing API",
    description="Speech-to-Text dataset uchun audio preprocessing servisi",
    version="1.0.0"
)

# CORS sozlash (frontend uchun)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production da aniq domain qo'yish kerak
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Pydantic Models ==============

class ProcessingStatus(BaseModel):
    """Processing holati modeli"""
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    message: Optional[str] = None
    original_filename: Optional[str] = None
    original_duration: Optional[float] = None
    processed_duration: Optional[float] = None
    download_url: Optional[str] = None


class ProcessingOptions(BaseModel):
    """Processing parametrlari"""
    denoise: bool = True
    trim_silence: bool = True
    extract_speech: bool = True
    normalize: bool = True
    noise_strength: float = 0.7  # 0.0 - 1.0


# ============== Audio Processor Class ==============

class AudioProcessor:
    """
    Audio processing pipeline.
    
    Barcha processing bosqichlarini birlashtiradi:
    - Denoising
    - Silence trimming
    - VAD & speech extraction
    - Normalization
    """
    
    def __init__(self, sample_rate: int = 16000):
        """
        Audio processor ni ishga tushirish.
        
        Args:
            sample_rate: Target sample rate
        """
        self.sample_rate = sample_rate
        self.denoiser = AudioDenoiser(sample_rate=sample_rate)
        self.vad = VoiceActivityDetector(sample_rate=sample_rate)
        self.trimmer = SilenceTrimmer(sample_rate=sample_rate)
        
        logger.info("AudioProcessor initialized")
    
    def load_audio(self, file_path: str) -> np.ndarray:
        """Audio faylni yuklash"""
        audio, sr = librosa.load(file_path, sr=self.sample_rate, mono=True)
        return audio
    
    def save_audio(self, audio: np.ndarray, file_path: str) -> None:
        """Audio faylni saqlash"""
        sf.write(file_path, audio, self.sample_rate)
    
    async def process(
        self,
        input_path: str,
        output_path: str,
        options: ProcessingOptions,
        task_id: str
    ) -> dict:
        """
        To'liq audio processing pipeline.
        
        Args:
            input_path: Input audio fayl yo'li
            output_path: Output fayl yo'li
            options: Processing parametrlari
            task_id: Task ID (progress tracking uchun)
            
        Returns:
            dict: Processing statistikasi
        """
        try:
            # Status yangilash
            self._update_status(task_id, "processing", 10, "Audio yuklanmoqda...")
            
            # 1. Audio yuklash
            audio = self.load_audio(input_path)
            original_duration = len(audio) / self.sample_rate
            
            logger.info(f"Loaded audio: {original_duration:.2f}s")
            self._update_status(task_id, "processing", 20, "Noise olib tashlanmoqda...")
            
            # Async uchun kichik pause
            await asyncio.sleep(0.1)
            
            # 2. Denoising
            if options.denoise:
                self.denoiser.noise_reduce_strength = options.noise_strength
                audio = self.denoiser.apply_highpass_filter(audio)
                audio = self.denoiser.spectral_gate(audio)
                logger.info("Denoising completed")
            
            self._update_status(task_id, "processing", 50, "Silence kesib olinmoqda...")
            await asyncio.sleep(0.1)
            
            # 3. Silence trimming (butun audio bo'ylab)
            if options.trim_silence:
                audio, trim_stats = self.trimmer.full_trim(
                    audio, 
                    use_adaptive=True, 
                    remove_internal=True  # O'rtadagi silencelarni ham qisqartirish
                )
                logger.info(
                    f"Trimming completed: {trim_stats['original_duration']:.2f}s -> {trim_stats['final_duration']:.2f}s "
                    f"(internal silences: {trim_stats.get('silences_shortened', 0)} shortened)"
                )
            
            self._update_status(task_id, "processing", 70, "Nutq ajratib olinmoqda...")
            await asyncio.sleep(0.1)
            
            # 4. Speech extraction (VAD)
            if options.extract_speech:
                audio, segments = self.vad.extract_speech(audio)
                logger.info(f"Speech extraction completed: {len(segments)} segments")
            
            self._update_status(task_id, "processing", 85, "Normallashtirilmoqda...")
            await asyncio.sleep(0.1)
            
            # 5. Normalization
            if options.normalize:
                audio = self.denoiser.normalize_audio(audio)
                logger.info("Normalization completed")
            
            # 6. Saqlash
            self._update_status(task_id, "processing", 95, "Saqlanmoqda...")
            self.save_audio(audio, output_path)
            
            processed_duration = len(audio) / self.sample_rate
            
            # Final status
            stats = {
                'original_duration': original_duration,
                'processed_duration': processed_duration,
                'reduction': original_duration - processed_duration,
                'reduction_percent': ((original_duration - processed_duration) / original_duration) * 100
            }
            
            self._update_status(
                task_id, 
                "completed", 
                100, 
                f"Tayyor! {original_duration:.1f}s → {processed_duration:.1f}s",
                stats
            )
            
            logger.info(f"Processing completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            self._update_status(task_id, "failed", 0, str(e))
            raise
    
    def _update_status(
        self, 
        task_id: str, 
        status: str, 
        progress: int, 
        message: str,
        stats: dict = None
    ):
        """Processing statusini yangilash"""
        if task_id in processing_status:
            processing_status[task_id]['status'] = status
            processing_status[task_id]['progress'] = progress
            processing_status[task_id]['message'] = message
            if stats:
                processing_status[task_id]['original_duration'] = stats.get('original_duration')
                processing_status[task_id]['processed_duration'] = stats.get('processed_duration')


# Global processor instance
processor = AudioProcessor()


# ============== API Endpoints ==============

@app.get("/")
async def root():
    """API health check"""
    return {
        "name": "AudioAI STT Preprocessing API",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/api/upload")
async def upload_audio(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Audio fayl yuklash va processing boshlash.
    
    Args:
        file: Upload qilingan audio fayl
        
    Returns:
        Task ID va status
    """
    # Fayl tekshirish
    if not file.filename:
        raise HTTPException(status_code=400, detail="Fayl nomi topilmadi")
    
    # Extension tekshirish
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Ruxsat berilmagan format. Faqat: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Fayl hajmi tekshirish
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Fayl juda katta. Maksimum: {MAX_FILE_SIZE // (1024*1024)} MB"
        )
    
    # Task ID yaratish
    task_id = str(uuid.uuid4())
    
    # Original filename saqlash (o'zgartirmaslik!)
    original_filename = file.filename
    
    # Vaqtinchalik fayl nomi (ichki ishlatish uchun)
    temp_filename = f"{task_id}{file_ext}"
    input_path = UPLOAD_DIR / temp_filename
    output_path = PROCESSED_DIR / original_filename  # Original nom bilan saqlash
    
    # Faylni saqlash
    with open(input_path, 'wb') as f:
        f.write(content)
    
    logger.info(f"File uploaded: {original_filename} -> {input_path}")
    
    # Processing status yaratish
    processing_status[task_id] = {
        'task_id': task_id,
        'status': 'pending',
        'progress': 0,
        'message': 'Navbatda...',
        'original_filename': original_filename,
        'original_duration': None,
        'processed_duration': None,
        'download_url': None,
        'input_path': str(input_path),
        'output_path': str(output_path)
    }
    
    return {
        'task_id': task_id,
        'filename': original_filename,
        'message': 'Fayl qabul qilindi'
    }


@app.post("/api/process/{task_id}")
async def start_processing(
    task_id: str,
    options: ProcessingOptions = None,
    background_tasks: BackgroundTasks = None
):
    """
    Audio processing boshlash.
    
    Args:
        task_id: Upload qilingan fayl task ID
        options: Processing parametrlari
    """
    if task_id not in processing_status:
        raise HTTPException(status_code=404, detail="Task topilmadi")
    
    task = processing_status[task_id]
    
    if task['status'] == 'processing':
        raise HTTPException(status_code=400, detail="Processing allaqachon boshlangan")
    
    if options is None:
        options = ProcessingOptions()
    
    # Background task boshlash
    background_tasks.add_task(
        run_processing,
        task_id,
        task['input_path'],
        task['output_path'],
        options
    )
    
    return {'task_id': task_id, 'status': 'processing started'}


async def run_processing(
    task_id: str,
    input_path: str,
    output_path: str,
    options: ProcessingOptions
):
    """Background processing task"""
    try:
        await processor.process(input_path, output_path, options, task_id)
        processing_status[task_id]['download_url'] = f"/api/download/{task_id}"
    except Exception as e:
        logger.error(f"Processing failed for {task_id}: {e}")
        processing_status[task_id]['status'] = 'failed'
        processing_status[task_id]['message'] = str(e)


@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    """
    Processing statusini olish.
    
    Args:
        task_id: Task ID
        
    Returns:
        Processing holati
    """
    if task_id not in processing_status:
        raise HTTPException(status_code=404, detail="Task topilmadi")
    
    return processing_status[task_id]


@app.get("/api/download/{task_id}")
async def download_processed(task_id: str):
    """
    Processed audio faylni yuklab olish.
    
    Args:
        task_id: Task ID
        
    Returns:
        Audio fayl (original nom bilan)
    """
    if task_id not in processing_status:
        raise HTTPException(status_code=404, detail="Task topilmadi")
    
    task = processing_status[task_id]
    
    if task['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Processing tugallanmagan")
    
    output_path = Path(task['output_path'])
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Fayl topilmadi")
    
    return FileResponse(
        path=output_path,
        filename=task['original_filename'],  # Original nom!
        media_type='audio/wav'
    )


@app.delete("/api/cleanup/{task_id}")
async def cleanup_task(task_id: str):
    """
    Task fayllarini tozalash.
    
    Args:
        task_id: Task ID
    """
    if task_id not in processing_status:
        raise HTTPException(status_code=404, detail="Task topilmadi")
    
    task = processing_status[task_id]
    
    # Fayllarni o'chirish
    try:
        input_path = Path(task['input_path'])
        output_path = Path(task['output_path'])
        
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()
        
        del processing_status[task_id]
        
        return {'message': 'Tozalandi'}
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-and-process")
async def upload_and_process(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Audio yuklash va darhol processing boshlash.
    One-click processing endpoint.
    """
    # Upload
    upload_result = await upload_audio(file, background_tasks)
    task_id = upload_result['task_id']
    
    # Default options bilan processing
    options = ProcessingOptions()
    task = processing_status[task_id]
    
    background_tasks.add_task(
        run_processing,
        task_id,
        task['input_path'],
        task['output_path'],
        options
    )
    
    return {
        'task_id': task_id,
        'filename': upload_result['filename'],
        'status': 'processing',
        'message': 'Processing boshlandi'
    }


# ============== Startup/Shutdown ==============

@app.on_event("startup")
async def startup():
    """App ishga tushganda"""
    logger.info("AudioAI API started")
    logger.info(f"Upload dir: {UPLOAD_DIR}")
    logger.info(f"Processed dir: {PROCESSED_DIR}")


@app.on_event("shutdown")
async def shutdown():
    """App to'xtaganda"""
    logger.info("AudioAI API shutting down")


# ============== Run ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
