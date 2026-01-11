"""
AudioAI - Forced Aligner Module
Word-level timestamps uchun forced alignment

Bu modul audio va matn orasida aniq
vaqt belgilarini aniqlash uchun ishlatiladi.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ForcedAligner:
    """
    Forced Alignment - so'zlarni audio bilan moslashtirish.
    
    Whisper word timestamps yoki WhisperX alignment
    dan foydalanadi.
    
    Attributes:
        method (str): Alignment metodi ('whisper', 'whisperx')
        language (str): Til kodi
    """
    
    def __init__(
        self,
        method: str = "whisper",
        language: str = "auto"
    ):
        """
        ForcedAligner ni ishga tushirish.
        
        Args:
            method: 'whisper' (default) yoki 'whisperx'
            language: Til kodi
        """
        self.method = method
        self.language = language
        self._whisperx_model = None
        
        logger.info(f"ForcedAligner initialized: method={method}")
    
    def align_from_whisper_result(
        self,
        whisper_result: Dict[str, Any],
        reference_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Whisper natijasidan word timestamps olish.
        
        Args:
            whisper_result: Whisper transcription natijasi
            reference_text: Reference matn (optional, alignment uchun)
            
        Returns:
            List[dict]: Word timestamps ro'yxati
        """
        word_timestamps = []
        
        # Segments dan words olish
        for segment in whisper_result.get('segments', []):
            for word_info in segment.get('words', []):
                word_timestamps.append({
                    'word': word_info.get('word', '').strip(),
                    'start': word_info.get('start', 0),
                    'end': word_info.get('end', 0),
                    'confidence': word_info.get('probability', word_info.get('confidence', 1.0))
                })
        
        # Agar reference_text berilgan bo'lsa, alignment qilish
        if reference_text:
            word_timestamps = self._align_with_reference(word_timestamps, reference_text)
        
        return word_timestamps
    
    def align(
        self,
        audio_path: str,
        text: str,
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Audio va matn orasida forced alignment.
        
        Args:
            audio_path: Audio fayl yo'li
            text: Alignment qilinadigan matn
            language: Til kodi
            
        Returns:
            List[dict]: Word timestamps
        """
        lang = language or self.language
        
        if self.method == "whisperx":
            return self._align_with_whisperx(audio_path, text, lang)
        else:
            # Default: Whisper bilan transcribe va align
            return self._align_with_whisper(audio_path, text, lang)
    
    def _align_with_whisper(
        self,
        audio_path: str,
        text: str,
        language: str
    ) -> List[Dict[str, Any]]:
        """
        Whisper yordamida alignment.
        
        Bu yerda Whisper transcription natijasidagi
        word timestamps ishlatiladi.
        """
        from .transcriber import get_transcriber
        
        transcriber = get_transcriber()
        result = transcriber.transcribe(audio_path, language=language, word_timestamps=True)
        
        word_timestamps = self.align_from_whisper_result(result, text)
        
        return word_timestamps
    
    def _align_with_whisperx(
        self,
        audio_path: str,
        text: str,
        language: str
    ) -> List[Dict[str, Any]]:
        """
        WhisperX yordamida aniqroq alignment.
        
        WhisperX phoneme-based alignment ishlatadi,
        bu aniqroq word timestamps beradi.
        """
        try:
            import whisperx
            import torch
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Audio yuklash
            audio = whisperx.load_audio(audio_path)
            
            # Whisper model (agar yuklanmagan bo'lsa)
            if self._whisperx_model is None:
                self._whisperx_model = whisperx.load_model(
                    "base",
                    device=device,
                    compute_type="float16" if device == "cuda" else "float32"
                )
            
            # Transcribe
            result = self._whisperx_model.transcribe(audio)
            
            # Alignment model yuklash
            model_a, metadata = whisperx.load_align_model(
                language_code=language if language != "auto" else "en",
                device=device
            )
            
            # Align
            result = whisperx.align(
                result["segments"],
                model_a,
                metadata,
                audio,
                device
            )
            
            # Word timestamps chiqarish
            word_timestamps = []
            for segment in result.get("segments", []):
                for word_info in segment.get("words", []):
                    word_timestamps.append({
                        'word': word_info.get('word', '').strip(),
                        'start': word_info.get('start', 0),
                        'end': word_info.get('end', 0),
                        'confidence': word_info.get('score', 1.0)
                    })
            
            return word_timestamps
            
        except ImportError:
            logger.warning("whisperx not installed, falling back to whisper alignment")
            return self._align_with_whisper(audio_path, text, language)
        except Exception as e:
            logger.error(f"WhisperX alignment error: {e}")
            return self._align_with_whisper(audio_path, text, language)
    
    def _align_with_reference(
        self,
        word_timestamps: List[Dict[str, Any]],
        reference_text: str
    ) -> List[Dict[str, Any]]:
        """
        Whisper timestamps ni reference text bilan moslashtirish.
        
        Bu qo'shimcha tekshiruv - whisper so'zlari reference
        so'zlari bilan mos kelishini ta'minlaydi.
        
        Args:
            word_timestamps: Whisper word timestamps
            reference_text: Reference matn
            
        Returns:
            List[dict]: Aligned word timestamps
        """
        if not word_timestamps or not reference_text:
            return word_timestamps
        
        # Reference so'zlari
        ref_words = reference_text.lower().split()
        
        # Whisper so'zlari
        whisper_words = [w['word'].lower().strip() for w in word_timestamps]
        
        # Agar uzunlik bir xil bo'lsa, to'g'ridan-to'g'ri moslashtirish
        if len(whisper_words) == len(ref_words):
            aligned = []
            for i, wt in enumerate(word_timestamps):
                aligned.append({
                    **wt,
                    'word': ref_words[i],  # Reference so'zini ishlatish
                    'original_word': wt['word']
                })
            return aligned
        
        # Aks holda, DTW yoki oddiy mapping
        return self._dtw_align(word_timestamps, ref_words)
    
    def _dtw_align(
        self,
        word_timestamps: List[Dict[str, Any]],
        ref_words: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Dynamic Time Warping yordamida alignment.
        
        So'zlar sonlari farq qilganda ishlatiladi.
        """
        n = len(word_timestamps)
        m = len(ref_words)
        
        if n == 0 or m == 0:
            return word_timestamps
        
        # Cost matrix (word similarity based)
        from difflib import SequenceMatcher
        
        cost = np.zeros((n + 1, m + 1))
        cost[0, :] = np.arange(m + 1)
        cost[:, 0] = np.arange(n + 1)
        
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                w1 = word_timestamps[i-1]['word'].lower()
                w2 = ref_words[j-1].lower()
                
                # Similarity score (1 = perfect match, 0 = no match)
                sim = SequenceMatcher(None, w1, w2).ratio()
                match_cost = 1 - sim  # Lower cost for better match
                
                cost[i, j] = min(
                    cost[i-1, j] + 1,      # deletion
                    cost[i, j-1] + 1,      # insertion
                    cost[i-1, j-1] + match_cost  # match/substitution
                )
        
        # Backtrack
        aligned = []
        i, j = n, m
        
        while i > 0 and j > 0:
            if i > 0 and cost[i, j] == cost[i-1, j] + 1:
                # Deletion (whisper so'zi reference da yo'q)
                aligned.append({
                    **word_timestamps[i-1],
                    'aligned': False,
                    'ref_word': None
                })
                i -= 1
            elif j > 0 and cost[i, j] == cost[i, j-1] + 1:
                # Insertion (reference so'zi whisper da yo'q)
                j -= 1
            else:
                # Match
                aligned.append({
                    **word_timestamps[i-1],
                    'word': ref_words[j-1],
                    'original_word': word_timestamps[i-1]['word'],
                    'aligned': True,
                    'ref_word': ref_words[j-1]
                })
                i -= 1
                j -= 1
        
        # Qolgan whisper so'zlari
        while i > 0:
            aligned.append({
                **word_timestamps[i-1],
                'aligned': False,
                'ref_word': None
            })
            i -= 1
        
        aligned.reverse()
        return aligned
    
    def get_duration_stats(
        self,
        word_timestamps: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Word timestamps statistikasi.
        
        Args:
            word_timestamps: Word timestamps ro'yxati
            
        Returns:
            dict: Statistika (total_duration, avg_word_duration, etc.)
        """
        if not word_timestamps:
            return {
                'total_duration': 0,
                'word_count': 0,
                'avg_word_duration': 0,
                'min_word_duration': 0,
                'max_word_duration': 0
            }
        
        durations = [w['end'] - w['start'] for w in word_timestamps]
        total_duration = word_timestamps[-1]['end'] - word_timestamps[0]['start']
        
        return {
            'total_duration': total_duration,
            'word_count': len(word_timestamps),
            'avg_word_duration': np.mean(durations),
            'min_word_duration': np.min(durations),
            'max_word_duration': np.max(durations),
            'speech_rate_wpm': len(word_timestamps) / (total_duration / 60) if total_duration > 0 else 0
        }


# Test
if __name__ == "__main__":
    aligner = ForcedAligner()
    print("ForcedAligner module initialized successfully!")
