"""
AudioAI - Whisper Transcriber Module
Whisper yordamida audio transcription

Bu modul OpenAI Whisper modelidan foydalanib
audio fayllarni matnga aylantiradi.
"""

import os
import torch
import numpy as np
import logging
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """
    Whisper bilan audio transcription.
    
    OpenAI Whisper yoki faster-whisper modellaridan
    foydalanib audio fayllarni matnga aylantiradi.
    
    Attributes:
        model_name (str): Whisper model nomi
        device (str): 'cuda' yoki 'cpu'
        compute_type (str): Compute type (float16, int8, etc.)
        language (str): Til kodi (auto, uz, ru, en, etc.)
    """
    
    # Model sizes va tavsiyalar
    MODEL_SIZES = {
        'tiny': {'vram': 1, 'speed': 'fastest', 'accuracy': 'low'},
        'base': {'vram': 1, 'speed': 'fast', 'accuracy': 'medium'},
        'small': {'vram': 2, 'speed': 'medium', 'accuracy': 'good'},
        'medium': {'vram': 5, 'speed': 'slow', 'accuracy': 'high'},
        'large-v2': {'vram': 10, 'speed': 'slowest', 'accuracy': 'best'},
        'large-v3': {'vram': 10, 'speed': 'slowest', 'accuracy': 'best'},
    }
    
    def __init__(
        self,
        model_name: str = "base",
        device: Optional[str] = None,
        compute_type: str = "float16",
        language: str = "auto",
        download_root: Optional[str] = None
    ):
        """
        Whisper transcriber ni ishga tushirish.
        
        Args:
            model_name: Model nomi (tiny, base, small, medium, large-v2, large-v3)
            device: Device (auto-detect qilinadi agar None)
            compute_type: Compute type (float16, int8_float16, int8)
            language: Til kodi (auto = avtomatik aniqlash)
            download_root: Model yuklab olish papkasi
        """
        self.model_name = model_name
        self.language = language
        self.download_root = download_root or os.path.expanduser("~/.cache/whisper")
        
        # Device aniqlash
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        # Compute type (GPU uchun float16, CPU uchun float32)
        if self.device == "cpu":
            self.compute_type = "float32"
        else:
            self.compute_type = compute_type
        
        self.model = None
        self._use_faster_whisper = True  # faster-whisper ishlatish
        
        logger.info(
            f"WhisperTranscriber initialized: model={model_name}, "
            f"device={self.device}, compute_type={self.compute_type}"
        )
    
    def load_model(self) -> None:
        """
        Whisper modelni yuklash (lazy loading).
        """
        if self.model is not None:
            return
        
        logger.info(f"Loading Whisper model: {self.model_name}")
        start_time = time.time()
        
        try:
            # faster-whisper ishlatish (tezroq va kam xotira)
            from faster_whisper import WhisperModel
            
            self.model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
                download_root=self.download_root
            )
            self._use_faster_whisper = True
            
            logger.info(f"faster-whisper model loaded in {time.time() - start_time:.2f}s")
            
        except ImportError:
            logger.warning("faster-whisper not found, using openai-whisper")
            
            # OpenAI Whisper fallback
            import whisper
            
            self.model = whisper.load_model(
                self.model_name,
                device=self.device,
                download_root=self.download_root
            )
            self._use_faster_whisper = False
            
            logger.info(f"openai-whisper model loaded in {time.time() - start_time:.2f}s")
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Audio faylni transcribe qilish.
        
        Args:
            audio_path: Audio fayl yo'li
            language: Til kodi (None = auto yoki default)
            task: 'transcribe' yoki 'translate'
            **kwargs: Qo'shimcha parametrlar
            
        Returns:
            dict: Transcription natijasi
                - text: To'liq matn
                - segments: Segmentlar ro'yxati
                - language: Aniqlangan til
                - duration: Audio davomiyligi
        """
        # Model yuklash (agar yuklanmagan bo'lsa)
        self.load_model()
        
        # Til
        lang = language or (self.language if self.language != "auto" else None)
        
        logger.info(f"Transcribing: {audio_path}")
        start_time = time.time()
        
        if self._use_faster_whisper:
            result = self._transcribe_faster_whisper(audio_path, lang, task, **kwargs)
        else:
            result = self._transcribe_openai_whisper(audio_path, lang, task, **kwargs)
        
        result['processing_time'] = time.time() - start_time
        logger.info(f"Transcription completed in {result['processing_time']:.2f}s")
        
        return result
    
    def _transcribe_faster_whisper(
        self,
        audio_path: str,
        language: Optional[str],
        task: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        faster-whisper bilan transcription.
        """
        # Transcribe
        segments, info = self.model.transcribe(
            audio_path,
            language=language,
            task=task,
            beam_size=kwargs.get('beam_size', 5),
            word_timestamps=kwargs.get('word_timestamps', True),
            vad_filter=kwargs.get('vad_filter', True),
        )
        
        # Segmentlarni list ga aylantirish
        segments_list = []
        full_text = []
        
        for segment in segments:
            seg_data = {
                'id': segment.id,
                'start': segment.start,
                'end': segment.end,
                'text': segment.text.strip(),
                'words': []
            }
            
            # Word timestamps
            if hasattr(segment, 'words') and segment.words:
                for word in segment.words:
                    seg_data['words'].append({
                        'word': word.word.strip(),
                        'start': word.start,
                        'end': word.end,
                        'probability': word.probability
                    })
            
            segments_list.append(seg_data)
            full_text.append(segment.text.strip())
        
        return {
            'text': ' '.join(full_text),
            'segments': segments_list,
            'language': info.language,
            'language_probability': info.language_probability,
            'duration': info.duration
        }
    
    def _transcribe_openai_whisper(
        self,
        audio_path: str,
        language: Optional[str],
        task: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        openai-whisper bilan transcription.
        """
        result = self.model.transcribe(
            audio_path,
            language=language,
            task=task,
            word_timestamps=kwargs.get('word_timestamps', True),
            verbose=False
        )
        
        # Segmentlarni formatlash
        segments_list = []
        for segment in result.get('segments', []):
            seg_data = {
                'id': segment['id'],
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip(),
                'words': []
            }
            
            # Word timestamps
            if 'words' in segment:
                for word in segment['words']:
                    seg_data['words'].append({
                        'word': word['word'].strip(),
                        'start': word['start'],
                        'end': word['end'],
                        'probability': word.get('probability', 1.0)
                    })
            
            segments_list.append(seg_data)
        
        return {
            'text': result['text'].strip(),
            'segments': segments_list,
            'language': result.get('language', 'unknown'),
            'language_probability': 1.0,
            'duration': segments_list[-1]['end'] if segments_list else 0
        }
    
    def transcribe_with_timestamps(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Transcription va word timestamps olish.
        
        Args:
            audio_path: Audio fayl yo'li
            language: Til kodi
            
        Returns:
            Tuple[str, List]: (matn, word_timestamps)
        """
        result = self.transcribe(audio_path, language=language, word_timestamps=True)
        
        # Barcha word timestamps yig'ish
        word_timestamps = []
        for segment in result.get('segments', []):
            for word in segment.get('words', []):
                word_timestamps.append({
                    'word': word['word'],
                    'start': word['start'],
                    'end': word['end'],
                    'confidence': word.get('probability', 1.0)
                })
        
        return result['text'], word_timestamps
    
    def get_available_models(self) -> List[str]:
        """
        Mavjud model nomlarini qaytarish.
        """
        return list(self.MODEL_SIZES.keys())
    
    def get_model_info(self, model_name: str = None) -> Dict[str, Any]:
        """
        Model haqida ma'lumot.
        """
        name = model_name or self.model_name
        if name in self.MODEL_SIZES:
            return {
                'name': name,
                **self.MODEL_SIZES[name],
                'device': self.device,
                'loaded': self.model is not None
            }
        return {'name': name, 'info': 'Unknown model'}
    
    def unload_model(self) -> None:
        """
        Modelni xotiradan tozalash.
        """
        if self.model is not None:
            del self.model
            self.model = None
            
            # GPU xotirasini tozalash
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("Model unloaded from memory")


# Global instance (lazy loading)
_transcriber_instance: Optional[WhisperTranscriber] = None


def get_transcriber(
    model_name: str = "base",
    force_reload: bool = False
) -> WhisperTranscriber:
    """
    Global transcriber instance olish.
    
    Args:
        model_name: Whisper model nomi
        force_reload: True bo'lsa, yangi instance yaratish
        
    Returns:
        WhisperTranscriber instance
    """
    global _transcriber_instance
    
    if _transcriber_instance is None or force_reload:
        _transcriber_instance = WhisperTranscriber(model_name=model_name)
    
    return _transcriber_instance


# Test
if __name__ == "__main__":
    transcriber = WhisperTranscriber(model_name="base")
    print(f"Device: {transcriber.device}")
    print(f"Available models: {transcriber.get_available_models()}")
    print(f"Model info: {transcriber.get_model_info()}")
