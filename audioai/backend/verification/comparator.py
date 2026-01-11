"""
AudioAI - Text Comparator Module
Transcription va reference text solishtirish

Bu modul ikki matnni solishtirish va
similarity score hisoblash uchun ishlatiladi.
"""

import re
import logging
from typing import List, Tuple, Set, Dict, Any
from difflib import SequenceMatcher
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextComparator:
    """
    Matnlarni solishtirish va similarity hisoblash.
    
    Turli xil similarity algoritmlaridan foydalanadi:
    - Word-level comparison
    - Character-level comparison
    - Levenshtein distance
    - Jaccard similarity
    
    Attributes:
        normalize_text (bool): Matnni normalizatsiya qilish
        ignore_case (bool): Katta-kichik harflarni e'tiborsiz qoldirish
        ignore_punctuation (bool): Tinish belgilarini e'tiborsiz qoldirish
    """
    
    def __init__(
        self,
        normalize_text: bool = True,
        ignore_case: bool = True,
        ignore_punctuation: bool = True,
        ignore_numbers: bool = False
    ):
        """
        TextComparator ni ishga tushirish.
        
        Args:
            normalize_text: Matnni normalizatsiya qilish
            ignore_case: Case-insensitive solishtirish
            ignore_punctuation: Tinish belgilarini olib tashlash
            ignore_numbers: Raqamlarni olib tashlash
        """
        self.normalize_text = normalize_text
        self.ignore_case = ignore_case
        self.ignore_punctuation = ignore_punctuation
        self.ignore_numbers = ignore_numbers
        
        logger.info(
            f"TextComparator initialized: normalize={normalize_text}, "
            f"ignore_case={ignore_case}, ignore_punct={ignore_punctuation}"
        )
    
    def preprocess(self, text: str) -> str:
        """
        Matnni preprocessing qilish.
        
        Args:
            text: Input matn
            
        Returns:
            str: Preprocessed matn
        """
        if not text:
            return ""
        
        result = text
        
        # Kichik harfga o'tkazish
        if self.ignore_case:
            result = result.lower()
        
        # Tinish belgilarini olib tashlash
        if self.ignore_punctuation:
            result = re.sub(r'[^\w\s]', ' ', result)
        
        # Raqamlarni olib tashlash
        if self.ignore_numbers:
            result = re.sub(r'\d+', '', result)
        
        # Ortiqcha bo'shliqlarni tozalash
        if self.normalize_text:
            result = ' '.join(result.split())
        
        return result.strip()
    
    def get_words(self, text: str) -> List[str]:
        """
        Matndan so'zlar ro'yxatini olish.
        
        Args:
            text: Input matn
            
        Returns:
            List[str]: So'zlar ro'yxati
        """
        preprocessed = self.preprocess(text)
        return preprocessed.split() if preprocessed else []
    
    def calculate_similarity(
        self,
        transcription: str,
        reference: str,
        method: str = "combined"
    ) -> float:
        """
        Ikki matn orasidagi similarity hisoblash.
        
        Args:
            transcription: Whisper transcription
            reference: Reference matn
            method: Similarity metodi ('word', 'char', 'jaccard', 'combined')
            
        Returns:
            float: Similarity score (0-1)
        """
        if not transcription or not reference:
            return 0.0
        
        trans_processed = self.preprocess(transcription)
        ref_processed = self.preprocess(reference)
        
        if method == "word":
            return self._word_similarity(trans_processed, ref_processed)
        elif method == "char":
            return self._char_similarity(trans_processed, ref_processed)
        elif method == "jaccard":
            return self._jaccard_similarity(trans_processed, ref_processed)
        elif method == "levenshtein":
            return self._levenshtein_similarity(trans_processed, ref_processed)
        else:
            # Combined: weighted average
            return self._combined_similarity(trans_processed, ref_processed)
    
    def _word_similarity(self, text1: str, text2: str) -> float:
        """
        Word-level SequenceMatcher similarity.
        """
        words1 = text1.split()
        words2 = text2.split()
        
        if not words1 or not words2:
            return 0.0
        
        matcher = SequenceMatcher(None, words1, words2)
        return matcher.ratio()
    
    def _char_similarity(self, text1: str, text2: str) -> float:
        """
        Character-level SequenceMatcher similarity.
        """
        if not text1 or not text2:
            return 0.0
        
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio()
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """
        Jaccard similarity (unique words intersection / union).
        """
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _levenshtein_similarity(self, text1: str, text2: str) -> float:
        """
        Levenshtein distance asosida similarity.
        """
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0
        
        # Levenshtein distance hisoblash
        len1, len2 = len(text1), len(text2)
        
        # DP matrix
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j
        
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if text1[i-1] == text2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
        
        distance = dp[len1][len2]
        max_len = max(len1, len2)
        
        return 1 - (distance / max_len)
    
    def _combined_similarity(self, text1: str, text2: str) -> float:
        """
        Combined similarity (weighted average).
        """
        word_sim = self._word_similarity(text1, text2)
        char_sim = self._char_similarity(text1, text2)
        jaccard_sim = self._jaccard_similarity(text1, text2)
        
        # Weighted average (word va char muhimroq)
        weights = {
            'word': 0.4,
            'char': 0.4,
            'jaccard': 0.2
        }
        
        combined = (
            word_sim * weights['word'] +
            char_sim * weights['char'] +
            jaccard_sim * weights['jaccard']
        )
        
        return combined
    
    def find_differences(
        self,
        transcription: str,
        reference: str
    ) -> Dict[str, List[str]]:
        """
        Ikki matn orasidagi farqlarni topish.
        
        Args:
            transcription: Whisper transcription
            reference: Reference matn
            
        Returns:
            dict: missing_words, extra_words, matched_words
        """
        trans_words = self.get_words(transcription)
        ref_words = self.get_words(reference)
        
        trans_set = set(trans_words)
        ref_set = set(ref_words)
        
        # Mos kelgan so'zlar
        matched = trans_set.intersection(ref_set)
        
        # Reference da bor, transcription da yo'q
        missing = ref_set - trans_set
        
        # Transcription da bor, reference da yo'q
        extra = trans_set - ref_set
        
        return {
            'matched_words': sorted(list(matched)),
            'missing_words': sorted(list(missing)),
            'extra_words': sorted(list(extra)),
            'trans_word_count': len(trans_words),
            'ref_word_count': len(ref_words),
            'matched_count': len(matched)
        }
    
    def get_word_alignment(
        self,
        transcription: str,
        reference: str
    ) -> List[Tuple[str, str, str]]:
        """
        So'zlar alignmentini olish.
        
        Args:
            transcription: Transcription matn
            reference: Reference matn
            
        Returns:
            List of (trans_word, ref_word, status) tuples
            status: 'match', 'mismatch', 'missing', 'extra'
        """
        trans_words = self.get_words(transcription)
        ref_words = self.get_words(reference)
        
        matcher = SequenceMatcher(None, trans_words, ref_words)
        
        alignment = []
        
        for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
            if opcode == 'equal':
                for k in range(i2 - i1):
                    alignment.append((trans_words[i1 + k], ref_words[j1 + k], 'match'))
            elif opcode == 'replace':
                max_len = max(i2 - i1, j2 - j1)
                for k in range(max_len):
                    trans_word = trans_words[i1 + k] if i1 + k < i2 else ''
                    ref_word = ref_words[j1 + k] if j1 + k < j2 else ''
                    alignment.append((trans_word, ref_word, 'mismatch'))
            elif opcode == 'delete':
                for k in range(i1, i2):
                    alignment.append((trans_words[k], '', 'extra'))
            elif opcode == 'insert':
                for k in range(j1, j2):
                    alignment.append(('', ref_words[k], 'missing'))
        
        return alignment
    
    def compare(
        self,
        transcription: str,
        reference: str
    ) -> Dict[str, Any]:
        """
        To'liq comparison natijasi.
        
        Args:
            transcription: Transcription matn
            reference: Reference matn
            
        Returns:
            dict: Barcha comparison ma'lumotlari
        """
        similarity = self.calculate_similarity(transcription, reference)
        differences = self.find_differences(transcription, reference)
        
        return {
            'transcription': transcription,
            'reference': reference,
            'similarity': similarity,
            'similarity_percent': f"{similarity * 100:.1f}%",
            **differences
        }


# Test
if __name__ == "__main__":
    comparator = TextComparator()
    
    # Test
    trans = "Salom dunyo bu test matn"
    ref = "Salom dunyo, bu test matn!"
    
    result = comparator.compare(trans, ref)
    print(f"Similarity: {result['similarity']:.2%}")
    print(f"Missing: {result['missing_words']}")
    print(f"Extra: {result['extra_words']}")
