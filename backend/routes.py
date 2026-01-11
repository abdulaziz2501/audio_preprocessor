"""
API Routes - Barcha audio processing endpoint'lari
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
import os
import logging
from typing import Optional, List
import json

from noise_reducer import NoiseReducer
from segmentation import AudioSegmenter
from silence_remover import SilenceRemover
from utils.audio_utils import save_upload_file, generate_unique_filename

"""
API Routes - Barcha audio processing endpoint'lari
"""

logger = logging.getLogger(__name__)
router = APIRouter()

# Service instance'lari
noise_reducer = NoiseReducer()
segmenter = AudioSegmenter()
silence_remover = SilenceRemover()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"


@router.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """
    Audio fayl yuklash

    Args:
        file: Audio fayl (mp3, wav, m4a, ogg)

    Returns:
        file_id: Yuklangan fayl ID'si
        filename: Fayl nomi
    """
    try:
        # Fayl formatini tekshirish
        allowed_formats = ['.mp3', '.wav', '.m4a', '.ogg', '.flac']
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Noto'g'ri format. Qo'llab-quvvatlanadigan formatlar: {', '.join(allowed_formats)}"
            )

        # Faylni saqlash
        file_id = generate_unique_filename(file.filename)
        filepath = save_upload_file(file, file_id)

        logger.info(f"✅ Fayl yuklandi: {file.filename}")

        return {
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "filepath": filepath,
            "message": "Fayl muvaffaqiyatli yuklandi"
        }

    except Exception as e:
        logger.error(f"❌ Fayl yuklashda xato: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-multiple")
async def upload_multiple_audio(files: List[UploadFile] = File(...)):
    """
    Ko'plab audio fayllarni yuklash (Batch Upload)

    Args:
        files: Audio fayllar ro'yxati

    Returns:
        Yuklangan fayllar haqida ma'lumot
    """
    try:
        uploaded_files = []
        allowed_formats = ['.mp3', '.wav', '.m4a', '.ogg', '.flac']

        for file in files:
            # Format tekshirish
            file_ext = os.path.splitext(file.filename)[1].lower()

            if file_ext not in allowed_formats:
                logger.warning(f"⚠️ Noto'g'ri format o'tkazib yuborildi: {file.filename}")
                continue

            # Faylni saqlash
            file_id = generate_unique_filename(file.filename)
            filepath = save_upload_file(file, file_id)

            uploaded_files.append({
                "file_id": file_id,
                "filename": file.filename,
                "filepath": filepath
            })

            logger.info(f"✅ Fayl yuklandi: {file.filename}")

        return {
            "success": True,
            "files": uploaded_files,
            "total": len(uploaded_files),
            "message": f"{len(uploaded_files)} ta fayl muvaffaqiyatli yuklandi"
        }

    except Exception as e:
        logger.error(f"❌ Ko'p fayllarni yuklashda xato: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/noise-reduction")
async def reduce_noise(
        file_id: str = Form(...),
        noise_reduction_strength: float = Form(0.8)
):
    """
    Audio'dan shovqinni tozalash

    Args:
        file_id: Fayl ID'si
        noise_reduction_strength: Shovqin tozalash kuchi (0.0 - 1.0)

    Returns:
        Tozalangan audio fayl
    """
    try:
        # Path'ni to'g'ri yaratish
        input_path = os.path.abspath(os.path.join(UPLOAD_DIR, file_id))

        if not os.path.exists(input_path):
            logger.error(f"Fayl topilmadi: {input_path}")
            raise HTTPException(status_code=404, detail=f"Fayl topilmadi: {file_id}")

        # Shovqinni tozalash
        output_path = noise_reducer.reduce_noise(
            input_path,
            strength=noise_reduction_strength
        )

        logger.info(f"✅ Shovqin tozalandi: {file_id}")

        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename=f"cleaned_{file_id}"
        )

    except Exception as e:
        logger.error(f"❌ Shovqin tozalashda xato: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/segmentation")
async def segment_audio(
        file_id: str = Form(...),
        segment_duration: int = Form(30),
        overlap: int = Form(0)
):
    """
    Audio'ni bo'laklarga bo'lish

    Args:
        file_id: Fayl ID'si
        segment_duration: Har bir segment davomiyligi (sekundlarda)
        overlap: Segmentlar orasidagi overlap (sekundlarda)

    Returns:
        Bo'laklarga bo'lingan audio fayllar ro'yxati
    """
    try:
        input_path = os.path.abspath(os.path.join(UPLOAD_DIR, file_id))

        if not os.path.exists(input_path):
            logger.error(f"Fayl topilmadi: {input_path}")
            raise HTTPException(status_code=404, detail=f"Fayl topilmadi: {file_id}")

        # Segmentatsiya
        segments = segmenter.segment_audio(
            input_path,
            segment_duration=segment_duration,
            overlap=overlap
        )

        logger.info(f"✅ {len(segments)} ta segment yaratildi")

        return {
            "success": True,
            "segments": segments,
            "total_segments": len(segments),
            "message": f"{len(segments)} ta segment muvaffaqiyatli yaratildi"
        }

    except Exception as e:
        logger.error(f"❌ Segmentatsiyada xato: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/remove-silence")
async def remove_silence(
        file_id: str = Form(...),
        silence_threshold: int = Form(-40),
        min_silence_duration: int = Form(500)
):
    """
    Audio'dan jimlik (silence) joylarni olib tashlash

    Args:
        file_id: Fayl ID'si
        silence_threshold: Jimlik chegarasi (dB, masalan: -40)
        min_silence_duration: Minimal jimlik davomiyligi (ms, masalan: 500)

    Returns:
        Jimlik olib tashlangan audio fayl
    """
    try:
        input_path = os.path.abspath(os.path.join(UPLOAD_DIR, file_id))

        if not os.path.exists(input_path):
            logger.error(f"Fayl topilmadi: {input_path}")
            raise HTTPException(status_code=404, detail=f"Fayl topilmadi: {file_id}")



    except Exception as e:
        logger.error(f"❌ Jimlik olib tashlashda xato: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/complete")
async def complete_processing(
        file_id: str = Form(...),
        operations: str = Form(...)
):
    """
    Bir nechta operatsiyalarni ketma-ket bajarish

    Args:
        file_id: Fayl ID'si
        operations: JSON format'dagi operatsiyalar

    Returns:
        Barcha operatsiyalar bajarilgan natija
    """
    try:
        input_path = os.path.abspath(os.path.join(UPLOAD_DIR, file_id))

        if not os.path.exists(input_path):
            logger.error(f"Fayl topilmadi: {input_path}")
            raise HTTPException(status_code=404, detail=f"Fayl topilmadi: {file_id}")

        # Operations JSON'ni parse qilish
        ops = json.loads(operations)
        current_file = input_path
        results = []

        # 1. Shovqinni tozalash
        if "noise_reduction" in ops:
            strength = ops["noise_reduction"].get("strength", 0.8)
            current_file = noise_reducer.reduce_noise(current_file, strength=strength)
            results.append("Shovqin tozalandi")
            logger.info("✅ Step 1: Noise reduction completed")

        # 2. Jimlikni olib tashlash
        if "remove_silence" in ops:
            threshold = ops["remove_silence"].get("threshold", -40)
            min_duration = ops["remove_silence"].get("min_duration", 500)
            current_file = silence_remover.remove_silence(
                current_file,
                silence_threshold=threshold,
                min_silence_duration=min_duration
            )
            results.append("Jimlik olib tashlandi")
            logger.info("✅ Step 2: Silence removal completed")

        # 3. Segmentatsiya
        if "segmentation" in ops:
            duration = ops["segmentation"].get("duration", 30)
            overlap = ops["segmentation"].get("overlap", 0)
            segments = segmenter.segment_audio(
                current_file,
                segment_duration=duration,
                overlap=overlap
            )
            results.append(f"{len(segments)} ta segment yaratildi")
            logger.info("✅ Step 3: Segmentation completed")

            return {
                "success": True,
                "segments": segments,
                "operations": results,
                "message": "Barcha operatsiyalar muvaffaqiyatli bajarildi"
            }

        # Agar segmentatsiya bo'lmasa
        return FileResponse(
            current_file,
            media_type="audio/wav",
            filename=f"processed_{file_id}"
        )

    except Exception as e:
        logger.error(f"❌ To'liq processing'da xato: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/batch")
async def batch_process(
        file_ids: str = Form(...),
        operations: str = Form(...)
):
    """
    Ko'plab fayllarni bir vaqtda qayta ishlash (Batch Processing)

    Args:
        file_ids: Fayl ID'lari (JSON array)
        operations: Operatsiyalar (JSON object)

    Returns:
        Barcha fayllar uchun natijalar
    """
    try:
        # Parse JSON
        file_id_list = json.loads(file_ids)
        ops = json.loads(operations)

        results = []

        for file_id in file_id_list:
            try:
                input_path = os.path.abspath(os.path.join(UPLOAD_DIR, file_id))

                if not os.path.exists(input_path):
                    logger.warning(f"⚠️ Fayl topilmadi, o'tkazib yuborildi: {file_id}")
                    results.append({
                        "file_id": file_id,
                        "success": False,
                        "error": "Fayl topilmadi"
                    })
                    continue

                current_file = input_path

                # 1. Noise Reduction
                if "noise_reduction" in ops:
                    strength = ops["noise_reduction"].get("strength", 0.8)
                    current_file = noise_reducer.reduce_noise(current_file, strength=strength)
                    logger.info(f"✅ Noise reduction: {file_id}")

                # 2. Silence Removal
                if "remove_silence" in ops:
                    threshold = ops["remove_silence"].get("threshold", -40)
                    min_duration = ops["remove_silence"].get("min_duration", 500)
                    current_file = silence_remover.remove_silence(
                        current_file,
                        silence_threshold=threshold,
                        min_silence_duration=min_duration
                    )
                    logger.info(f"✅ Silence removal: {file_id}")

                # 3. Segmentation
                if "segmentation" in ops:
                    duration = ops["segmentation"].get("duration", 30)
                    overlap = ops["segmentation"].get("overlap", 0)
                    segments = segmenter.segment_audio(
                        current_file,
                        segment_duration=duration,
                        overlap=overlap
                    )

                    results.append({
                        "file_id": file_id,
                        "success": True,
                        "type": "segments",
                        "segments": segments
                    })
                    logger.info(f"✅ Segmentation: {file_id} - {len(segments)} segments")
                else:
                    results.append({
                        "file_id": file_id,
                        "success": True,
                        "type": "file",
                        "output_path": current_file
                    })
                    logger.info(f"✅ Processing complete: {file_id}")

            except Exception as file_error:
                logger.error(f"❌ {file_id} qayta ishlashda xato: {file_error}")
                results.append({
                    "file_id": file_id,
                    "success": False,
                    "error": str(file_error)
                })

        # Statistika
        success_count = sum(1 for r in results if r.get("success"))

        return {
            "success": True,
            "results": results,
            "total": len(file_id_list),
            "processed": success_count,
            "failed": len(file_id_list) - success_count,
            "message": f"{success_count}/{len(file_id_list)} fayl muvaffaqiyatli qayta ishlandi"
        }

    except Exception as e:
        logger.error(f"❌ Batch processing xato: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{file_id}")
async def download_file(file_id: str):
    """
    Faylni yuklab olish
    """
    try:
        for directory in [UPLOAD_DIR, OUTPUT_DIR]:
            filepath = os.path.join(directory, file_id)
            if os.path.exists(filepath):
                return FileResponse(filepath, media_type="audio/wav", filename=file_id)
        raise HTTPException(status_code=404, detail="Fayl topilmadi")
    except Exception as e:
        logger.error(f"❌ Fayl yuklab olishda xato: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{file_id}")
async def delete_file(file_id: str):
    """
    Faylni o'chirish
    """
    try:
        deleted = False
        for directory in [UPLOAD_DIR, OUTPUT_DIR]:
            filepath = os.path.join(directory, file_id)
            if os.path.exists(filepath):
                os.remove(filepath)
                deleted = True
                logger.info(f"🗑️ Fayl o'chirildi: {file_id}")

        if deleted:
            return {"success": True, "message": "Fayl muvaffaqiyatli o'chirildi"}
        else:
            raise HTTPException(status_code=404, detail="Fayl topilmadi")
    except Exception as e:
        logger.error(f"❌ Fayl o'chirishda xato: {e}")
        raise HTTPException(status_code=500, detail=str(e))