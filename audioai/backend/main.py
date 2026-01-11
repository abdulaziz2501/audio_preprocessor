"""
AudioAI - FastAPI Backend Application
STT Dataset uchun Audio Preprocessing va Verification API

Bu API quyidagi funksiyalarni bajaradi:
1. Audio fayllarni qabul qilish (upload)
2. Background noise olib tashlash
3. Silence trimming
4. Voice activity detection va speech extraction
5. Processed audio qaytarish
6. Audio-Text verification
"""

import os
import uuid
import json
import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

import numpy as np
import librosa
import soundfile as sf

import whisper
from difflib import SequenceMatcher

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
VERIFY_DIR = BASE_DIR / "uploads" / "verify"

# Papkalarni yaratish
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
VERIFY_DIR.mkdir(parents=True, exist_ok=True)

# Ruxsat berilgan formatlar
ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.ogg', '.flac', '.m4a'}

# Maksimal fayl hajmi (50 MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# Processing holatini saqlash
processing_status = {}
verification_jobs = {}

# Whisper modellari
WHISPER_MODELS = {
    'tiny': 'tiny',
    'base': 'base',
    'small': 'small',
    'medium': 'medium',
    'large-v2': 'large-v2'
}

# ============== FastAPI App ==============

app = FastAPI(
    title="AudioAI - STT Preprocessing API",
    description="Speech-to-Text dataset uchun audio preprocessing va verification servisi",
    version="2.0.0"
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


class VerificationOptions(BaseModel):
    """Verification parametrlari"""
    whisper_model: str = "base"
    language: str = "auto"
    preprocess: bool = True
    trim_silence: bool = True
    denoise: bool = True


class VerificationResult(BaseModel):
    """Verification natijasi"""
    audio_name: str
    text_name: str
    transcription: str
    reference_text: str
    similarity: float
    status: str  # valid, warning, reject
    missing_words: List[str]
    extra_words: List[str]
    processing_time: float


class VerificationJob(BaseModel):
    """Verification job"""
    job_id: str
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    total_tasks: int
    completed_tasks: int
    results: List[VerificationResult]
    summary: Dict[str, Any]
    tasks: List[Dict[str, Any]]


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

# ============== Text Similarity Functions ==============

def calculate_similarity(text1: str, text2: str) -> float:
    """
    Ikki matn o'rtasidagi o'xshashlikni hisoblash.

    Args:
        text1: Birinchi matn
        text2: Ikkinchi matn

    Returns:
        float: 0.0 - 1.0 oralig'idagi o'xshashlik
    """
    # Kichik harflarga o'tkazish va ortiqcha bo'sh joylarni olib tashlash
    text1 = text1.lower().strip()
    text2 = text2.lower().strip()

    # SequenceMatcher yordamida o'xshashlik
    matcher = SequenceMatcher(None, text1, text2)
    similarity = matcher.ratio()

    return similarity


def analyze_word_differences(reference: str, transcription: str):
    """
    Matnlar orasidagi so'z farqlarini aniqlash.

    Args:
        reference: Reference matn
        transcription: Transcription matn

    Returns:
        tuple: (missing_words, extra_words)
    """
    # So'zlarga ajratish
    ref_words = set(reference.lower().strip().split())
    trans_words = set(transcription.lower().strip().split())

    # Yo'qolgan so'zlar (reference'da bor, transcription'da yo'q)
    missing_words = list(ref_words - trans_words)

    # Ortiqcha so'zlar (transcription'da bor, reference'da yo'q)
    extra_words = list(trans_words - ref_words)

    return missing_words, extra_words


def get_similarity_status(similarity: float) -> str:
    """
    O'xshashlik qiymatiga ko'ra status aniqlash.

    Args:
        similarity: 0.0 - 1.0 oralig'idagi o'xshashlik

    Returns:
        str: valid, warning, reject
    """
    if similarity >= 0.9:  # 90% va undan yuqori
        return "valid"
    elif similarity >= 0.7:  # 70-90%
        return "warning"
    else:  # 70% dan past
        return "reject"


# ============== Verification Functions ==============

def load_whisper_model(model_name: str = "base"):
    """
    Whisper modelini yuklash.

    Args:
        model_name: Model nomi (tiny, base, small, medium, large-v2)

    Returns:
        whisper.Model: Yuklangan model
    """
    try:
        model = whisper.load_model(model_name)
        logger.info(f"Whisper model {model_name} loaded")
        return model
    except Exception as e:
        logger.error(f"Failed to load whisper model {model_name}: {e}")
        raise


async def verify_single_audio(
    audio_path: str,
    text_path: str,
    options: VerificationOptions,
    model,
    job_id: str,
    task_index: int
) -> VerificationResult:
    """
    Bitta audio va text faylini tekshirish.

    Args:
        audio_path: Audio fayl yo'li
        text_path: Text fayl yo'li
        options: Verification parametrlari
        model: Whisper model
        job_id: Job ID
        task_index: Task index

    Returns:
        VerificationResult: Verification natijasi
    """
    start_time = datetime.now()

    try:
        # Text faylni o'qish
        with open(text_path, 'r', encoding='utf-8') as f:
            reference_text = f.read().strip()

        # Audio preprocessing (agar kerak bo'lsa)
        if options.preprocess:
            temp_audio_path = f"{audio_path}.processed.wav"
            proc_options = ProcessingOptions(
                denoise=options.denoise,
                trim_silence=options.trim_silence,
                extract_speech=True,
                normalize=True
            )

            # Audio processing
            audio = processor.load_audio(audio_path)

            if options.denoise:
                processor.denoiser.noise_reduce_strength = 0.7
                audio = processor.denoiser.apply_highpass_filter(audio)
                audio = processor.denoiser.spectral_gate(audio)

            if options.trim_silence:
                audio, _ = processor.trimmer.full_trim(audio, use_adaptive=True)

            processor.save_audio(audio, temp_audio_path)
            audio_path = temp_audio_path

        # Transcription
        language = None if options.language == "auto" else options.language
        result = model.transcribe(audio_path, language=language, fp16=False)
        transcription = result["text"].strip()

        # Similarity hisoblash
        similarity = calculate_similarity(reference_text, transcription)

        # Word difference analysis
        missing_words, extra_words = analyze_word_differences(reference_text, transcription)

        # Status aniqlash
        status = get_similarity_status(similarity)

        # Vaqt hisoblash
        processing_time = (datetime.now() - start_time).total_seconds()

        # Temp faylni o'chirish (agar mavjud bo'lsa)
        if options.preprocess and 'temp_audio_path' in locals():
            try:
                os.remove(temp_audio_path)
            except:
                pass

        # Job status yangilash
        if job_id in verification_jobs:
            verification_jobs[job_id]['completed_tasks'] += 1
            total_tasks = verification_jobs[job_id]['total_tasks']
            completed_tasks = verification_jobs[job_id]['completed_tasks']
            progress = int((completed_tasks / total_tasks) * 100)
            verification_jobs[job_id]['progress'] = progress

            # Task status yangilash
            for task in verification_jobs[job_id]['tasks']:
                if task['index'] == task_index:
                    task['status'] = 'completed'
                    task['result'] = {
                        'audio_name': Path(audio_path).name,
                        'similarity': similarity,
                        'status': status
                    }
                    break

        return VerificationResult(
            audio_name=Path(audio_path).name,
            text_name=Path(text_path).name,
            transcription=transcription,
            reference_text=reference_text,
            similarity=similarity,
            status=status,
            missing_words=missing_words,
            extra_words=extra_words,
            processing_time=processing_time
        )

    except Exception as e:
        logger.error(f"Verification error for {audio_path}: {e}")

        # Job status yangilash
        if job_id in verification_jobs:
            verification_jobs[job_id]['completed_tasks'] += 1
            for task in verification_jobs[job_id]['tasks']:
                if task['index'] == task_index:
                    task['status'] = 'failed'
                    task['error'] = str(e)
                    break

        raise


async def run_verification_job(job_id: str):
    """
    Background verification job.

    Args:
        job_id: Job ID
    """
    try:
        if job_id not in verification_jobs:
            return

        job = verification_jobs[job_id]
        job['status'] = 'running'

        # Model yuklash
        model = load_whisper_model(job['options'].whisper_model)

        # Har bir audio-text juftligini tekshirish
        tasks = []
        for i, (audio_path, text_path) in enumerate(job['audio_text_pairs']):
            task = asyncio.create_task(
                verify_single_audio(
                    audio_path, text_path, job['options'],
                    model, job_id, i
                )
            )
            tasks.append(task)

        # Barcha tasklarni kutish
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Natijalarni saqlash
        valid_results = []
        for result in results:
            if isinstance(result, VerificationResult):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Task failed: {result}")

        job['results'] = valid_results
        job['status'] = 'completed'

        # Summary hisoblash
        if valid_results:
            similarities = [r.similarity for r in valid_results]
            average_similarity = sum(similarities) / len(similarities)

            valid_count = sum(1 for r in valid_results if r.status == 'valid')
            warning_count = sum(1 for r in valid_results if r.status == 'warning')
            reject_count = sum(1 for r in valid_results if r.status == 'reject')

            job['summary'] = {
                'total_processed': len(valid_results),
                'valid_count': valid_count,
                'warning_count': warning_count,
                'reject_count': reject_count,
                'average_similarity': average_similarity
            }

        logger.info(f"Verification job {job_id} completed")

    except Exception as e:
        logger.error(f"Verification job {job_id} failed: {e}")
        if job_id in verification_jobs:
            verification_jobs[job_id]['status'] = 'failed'
            verification_jobs[job_id]['error'] = str(e)


# ============== API Endpoints ==============

@app.get("/")
async def root():
    """API health check"""
    return {
        "name": "AudioAI STT Preprocessing & Verification API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "preprocessing": "/api/upload",
            "verification": "/api/verify-audios"
        }
    }


# ============== VERIFICATION ENDPOINTS ==============

@app.post("/api/verify-audios")
async def verify_audios(
    text_files: List[UploadFile] = File(...),
    audio_files: List[UploadFile] = File(...),
    whisper_model: str = Form("base"),
    language: str = Form("auto"),
    preprocess: bool = Form(True),
    trim_silence: bool = Form(True),
    denoise: bool = Form(True),
    background_tasks: BackgroundTasks = None
):
    """
    Audio va text fayllarni nom bo'yicha moslashtirib verification qilish.

    Args:
        text_files: List of text files (.txt)
        audio_files: List of audio files
        whisper_model: Whisper model to use
        language: Transcription language (auto detect if 'auto')
        preprocess: Apply audio preprocessing
        trim_silence: Apply silence trimming
        denoise: Apply denoising

    Returns:
        Job ID va status
    """
    # Tekshirishlar
    if not text_files or not audio_files:
        raise HTTPException(status_code=400, detail="Text yoki audio fayllar topilmadi")

    # Job ID yaratish
    job_id = str(uuid.uuid4())

    # Fayllarni saqlash
    job_dir = VERIFY_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    audio_text_pairs = []
    tasks = []

    # Text fayllarni saqlash va map yaratish
    text_files_map = {}
    for text_file in text_files:
        if not text_file.filename.lower().endswith('.txt'):
            continue

        text_path = job_dir / text_file.filename
        with open(text_path, 'wb') as f:
            content = await text_file.read()
            f.write(content)

        base_name = Path(text_file.filename).stem
        text_files_map[base_name] = str(text_path)

    # Audio fayllarni saqlash va juftlash
    for audio_file in audio_files:
        audio_path = job_dir / audio_file.filename
        with open(audio_path, 'wb') as f:
            content = await audio_file.read()
            f.write(content)

        base_name = Path(audio_file.filename).stem

        # Mos keladigan text faylni topish
        if base_name in text_files_map:
            audio_text_pairs.append((str(audio_path), text_files_map[base_name]))

            # Task status qo'shish
            tasks.append({
                'index': len(tasks),
                'audio_name': audio_file.filename,
                'text_name': f"{base_name}.txt",
                'status': 'pending',
                'result': None
            })
        else:
            # Text topilmasa, faqat audio
            tasks.append({
                'index': len(tasks),
                'audio_name': audio_file.filename,
                'text_name': None,
                'status': 'no_match',
                'result': None
            })

    # Job yaratish
    options = VerificationOptions(
        whisper_model=whisper_model,
        language=language,
        preprocess=preprocess,
        trim_silence=trim_silence,
        denoise=denoise
    )

    verification_jobs[job_id] = {
        'job_id': job_id,
        'status': 'pending',
        'progress': 0,
        'total_tasks': len(audio_text_pairs),
        'completed_tasks': 0,
        'options': options,
        'audio_text_pairs': audio_text_pairs,
        'results': [],
        'summary': {},
        'tasks': tasks,
        'created_at': datetime.now().isoformat()
    }

    # Background task boshlash
    background_tasks.add_task(run_verification_job, job_id)

    logger.info(f"Verification job {job_id} started with {len(audio_text_pairs)} pairs")

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Verification boshlandi",
        "matched_pairs": len(audio_text_pairs),
        "total_files": len(audio_files) + len(text_files)
    }


@app.get("/api/verify-status/{job_id}")
async def get_verification_status(job_id: str):
    """
    Verification job statusini olish.

    Args:
        job_id: Job ID

    Returns:
        Job holati
    """
    if job_id not in verification_jobs:
        raise HTTPException(status_code=404, detail="Job topilmadi")

    job = verification_jobs[job_id]

    # Minimal response
    response = {
        "job_id": job_id,
        "status": job['status'],
        "progress": job['progress'],
        "total_tasks": job['total_tasks'],
        "completed_tasks": job['completed_tasks'],
        "tasks": job['tasks']
    }

    return response


@app.get("/api/verify-result/{job_id}")
async def get_verification_results(job_id: str):
    """
    Verification natijalarini olish.

    Args:
        job_id: Job ID

    Returns:
        Barcha verification natijalari
    """
    if job_id not in verification_jobs:
        raise HTTPException(status_code=404, detail="Job topilmadi")

    job = verification_jobs[job_id]

    if job['status'] == 'pending' or job['status'] == 'running':
        return JSONResponse(
            status_code=202,
            content={
                "job_id": job_id,
                "status": job['status'],
                "message": "Processing davom etmoqda"
            }
        )

    if job['status'] == 'failed':
        return JSONResponse(
            status_code=500,
            content={
                "job_id": job_id,
                "status": "failed",
                "error": job.get('error', 'Noma\'lum xatolik')
            }
        )

    # Convert results to dict
    results_dict = []
    for result in job['results']:
        results_dict.append({
            "audio_name": result.audio_name,
            "text_name": result.text_name,
            "transcription": result.transcription,
            "reference_text": result.reference_text,
            "similarity": result.similarity,
            "status": result.status,
            "missing_words": result.missing_words,
            "extra_words": result.extra_words,
            "processing_time": result.processing_time
        })

    return {
        "job_id": job_id,
        "status": job['status'],
        "results": results_dict,
        "summary": job['summary'],
        "total_processed": len(results_dict)
    }


@app.delete("/api/verify-cleanup/{job_id}")
async def cleanup_verification_job(job_id: str):
    """
    Verification job fayllarini tozalash.

    Args:
        job_id: Job ID
    """
    if job_id not in verification_jobs:
        raise HTTPException(status_code=404, detail="Job topilmadi")

    try:
        # Fayllarni o'chirish
        job_dir = VERIFY_DIR / job_id
        if job_dir.exists():
            shutil.rmtree(job_dir)

        # Job ma'lumotlarini o'chirish
        del verification_jobs[job_id]

        return {"message": f"Job {job_id} tozalandi"}
    except Exception as e:
        logger.error(f"Cleanup error for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== PREPROCESSING ENDPOINTS (Oldindagi endpointlar) ==============

@app.post("/api/upload")
async def upload_audio(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Audio fayl yuklash va processing boshlash.
    """
    # ... (oldindagi kod o'zgarmagan) ...
    # Tezlik uchun oldingi kodni saqladim, lekin sizda allaqachon mavjud
    pass


@app.post("/api/process/{task_id}")
async def start_processing(
    task_id: str,
    options: ProcessingOptions = None,
    background_tasks: BackgroundTasks = None
):
    # ... (oldindagi kod) ...
    pass


@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    # ... (oldindagi kod) ...
    pass


@app.get("/api/download/{task_id}")
async def download_processed(task_id: str):
    # ... (oldindagi kod) ...
    pass


@app.delete("/api/cleanup/{task_id}")
async def cleanup_task(task_id: str):
    # ... (oldindagi kod) ...
    pass


@app.post("/api/upload-and-process")
async def upload_and_process(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    # ... (oldindagi kod) ...
    pass


# ============== Startup/Shutdown ==============

@app.on_event("startup")
async def startup():
    """App ishga tushganda"""
    logger.info("AudioAI API started (with verification)")
    logger.info(f"Upload dir: {UPLOAD_DIR}")
    logger.info(f"Processed dir: {PROCESSED_DIR}")
    logger.info(f"Verify dir: {VERIFY_DIR}")


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