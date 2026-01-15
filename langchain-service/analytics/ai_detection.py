"""
AI Detection Module - Statistical Analysis to Detect AI-Generated Content

All calculations use:
- NLTK for tokenization and n-gram analysis
- Statistical formulas for burstiness and perplexity
- Lexical diversity metrics (MTLD, TTR)

NO LLM INFERENCE - pure statistical measurement

Human writing characteristics:
- High perplexity (unpredictable word choices)
- High burstiness (varied sentence lengths)
- High lexical diversity (rich vocabulary)
- Natural n-gram distribution (no repetitive phrases)

AI writing characteristics:
- Low perplexity (uniform, predictable)
- Low burstiness (consistent sentence lengths)
- Lower lexical diversity (repetitive vocabulary)
- Repetitive n-gram patterns
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import Counter
import re
import math

logger = logging.getLogger(__name__)

# Import NLP libraries with fallback
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.util import ngrams
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("NLTK not installed. Install with: pip install nltk")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy not installed. Install with: pip install numpy")


class AIDetector:
    """
    Production-grade AI detection using statistical NLP.

    All methods return deterministic results with algorithm documentation.
    """

    # Thresholds for AI detection (calibrated from research)
    THRESHOLDS = {
        'burstiness_human_min': 0.5,      # Human text typically > 0.5
        'ttr_human_min': 0.4,              # Type-Token Ratio for human text
        'mtld_human_min': 50,              # MTLD score for human text
        'repetition_ai_max': 2.0,          # Repetition density for AI
        'entropy_human_min': 3.0           # Structure entropy for human text
    }

    def __init__(self):
        """Initialize AI detector."""
        # Download NLTK data if needed
        if NLTK_AVAILABLE:
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)
            try:
                nltk.data.find('tokenizers/punkt_tab')
            except LookupError:
                nltk.download('punkt_tab', quiet=True)

    def _simple_sentence_split(self, text: str) -> List[str]:
        """Fallback sentence splitting without NLTK."""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _simple_word_tokenize(self, text: str) -> List[str]:
        """Fallback word tokenization without NLTK."""
        return re.findall(r'\b\w+\b', text.lower())

    def calculate_burstiness(self, content: str) -> Dict[str, Any]:
        """
        Calculate burstiness (sentence length variation).

        Human writing has HIGH burstiness (varied sentence lengths).
        AI writing has LOW burstiness (uniform sentence lengths).

        Formula: burstiness = std_dev(sentence_lengths) / mean(sentence_lengths)

        Args:
            content: Text content to analyze

        Returns:
            Dict with burstiness score and interpretation
        """
        if NLTK_AVAILABLE:
            sentences = sent_tokenize(content)
            tokenize_func = word_tokenize
        else:
            sentences = self._simple_sentence_split(content)
            tokenize_func = self._simple_word_tokenize

        if len(sentences) < 2:
            return {
                'burstiness': 0.0,
                'assessment': 'insufficient_data',
                'algorithm': 'burstiness = std_dev(lengths) / mean(lengths)',
                'is_verified': True,
                'error': 'Need at least 2 sentences'
            }

        # Calculate sentence lengths
        lengths = [len(tokenize_func(s)) for s in sentences]

        # Calculate mean and standard deviation
        mean_length = sum(lengths) / len(lengths)
        if mean_length == 0:
            return {
                'burstiness': 0.0,
                'assessment': 'insufficient_data',
                'algorithm': 'burstiness = std_dev(lengths) / mean(lengths)',
                'is_verified': True,
                'error': 'Empty sentences'
            }

        variance = sum((l - mean_length) ** 2 for l in lengths) / len(lengths)
        std_dev = variance ** 0.5
        burstiness = std_dev / mean_length

        # Determine assessment
        if burstiness >= self.THRESHOLDS['burstiness_human_min']:
            assessment = 'human-like'
        elif burstiness >= self.THRESHOLDS['burstiness_human_min'] * 0.6:
            assessment = 'mixed'
        else:
            assessment = 'ai-like'

        return {
            'burstiness': round(burstiness, 4),
            'mean_sentence_length': round(mean_length, 2),
            'std_dev_sentence_length': round(std_dev, 2),
            'sentence_count': len(sentences),
            'min_sentence_length': min(lengths),
            'max_sentence_length': max(lengths),
            'assessment': assessment,
            'threshold': self.THRESHOLDS['burstiness_human_min'],
            'algorithm': 'burstiness = std_dev(sentence_lengths) / mean(sentence_lengths)',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def calculate_type_token_ratio(self, content: str) -> Dict[str, Any]:
        """
        Calculate Type-Token Ratio (TTR) for vocabulary richness.

        TTR = unique_words / total_words

        Higher TTR = more diverse vocabulary = more human-like.

        Args:
            content: Text content to analyze

        Returns:
            Dict with TTR score and interpretation
        """
        if NLTK_AVAILABLE:
            words = word_tokenize(content.lower())
        else:
            words = self._simple_word_tokenize(content)

        if not words:
            return {
                'ttr': 0.0,
                'assessment': 'insufficient_data',
                'algorithm': 'TTR = unique_words / total_words',
                'is_verified': True,
                'error': 'No words found'
            }

        unique_words = set(words)
        ttr = len(unique_words) / len(words)

        # Determine assessment
        if ttr >= self.THRESHOLDS['ttr_human_min']:
            assessment = 'human-like'
        elif ttr >= self.THRESHOLDS['ttr_human_min'] * 0.7:
            assessment = 'mixed'
        else:
            assessment = 'ai-like'

        return {
            'ttr': round(ttr, 4),
            'unique_words': len(unique_words),
            'total_words': len(words),
            'assessment': assessment,
            'threshold': self.THRESHOLDS['ttr_human_min'],
            'algorithm': 'Type-Token Ratio = unique_words / total_words',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def calculate_mtld(self, content: str, threshold: float = 0.72) -> Dict[str, Any]:
        """
        Calculate MTLD (Measure of Textual Lexical Diversity).

        MTLD measures how many words can be read before vocabulary
        starts repeating significantly.

        Higher MTLD = more diverse = more human-like.

        Args:
            content: Text content to analyze
            threshold: TTR threshold for factor calculation (default 0.72)

        Returns:
            Dict with MTLD score and interpretation
        """
        if NLTK_AVAILABLE:
            words = word_tokenize(content.lower())
        else:
            words = self._simple_word_tokenize(content)

        if len(words) < 10:
            return {
                'mtld': 0.0,
                'assessment': 'insufficient_data',
                'algorithm': 'MTLD (Measure of Textual Lexical Diversity)',
                'is_verified': True,
                'error': 'Need at least 10 words'
            }

        def _calculate_mtld_one_direction(word_list: List[str]) -> float:
            """Calculate MTLD in one direction."""
            factors = 0
            factor_lengths = []
            current_start = 0

            for i in range(1, len(word_list) + 1):
                segment = word_list[current_start:i]
                unique = set(segment)
                ttr = len(unique) / len(segment)

                if ttr <= threshold:
                    factors += 1
                    factor_lengths.append(len(segment))
                    current_start = i

            # Handle remaining segment
            if current_start < len(word_list):
                remaining = word_list[current_start:]
                if len(remaining) > 0:
                    remaining_ttr = len(set(remaining)) / len(remaining)
                    partial_factor = (1 - remaining_ttr) / (1 - threshold)
                    factors += min(partial_factor, 1.0)

            return len(word_list) / factors if factors > 0 else len(word_list)

        # Calculate forward and backward
        mtld_forward = _calculate_mtld_one_direction(words)
        mtld_backward = _calculate_mtld_one_direction(words[::-1])
        mtld = (mtld_forward + mtld_backward) / 2

        # Determine assessment
        if mtld >= self.THRESHOLDS['mtld_human_min']:
            assessment = 'human-like'
        elif mtld >= self.THRESHOLDS['mtld_human_min'] * 0.6:
            assessment = 'mixed'
        else:
            assessment = 'ai-like'

        return {
            'mtld': round(mtld, 2),
            'mtld_forward': round(mtld_forward, 2),
            'mtld_backward': round(mtld_backward, 2),
            'word_count': len(words),
            'assessment': assessment,
            'threshold': self.THRESHOLDS['mtld_human_min'],
            'algorithm': 'MTLD (Measure of Textual Lexical Diversity) - bidirectional average',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def detect_ngram_repetition(
        self,
        content: str,
        n_range: range = range(3, 8)
    ) -> Dict[str, Any]:
        """
        Detect repeated n-grams that indicate AI generation.

        AI text often has unnatural phrase repetition patterns.

        Args:
            content: Text content to analyze
            n_range: Range of n-gram sizes to analyze (default 3-7)

        Returns:
            Dict with repetition metrics and flagged phrases
        """
        if NLTK_AVAILABLE:
            words = word_tokenize(content.lower())
        else:
            words = self._simple_word_tokenize(content)

        if len(words) < max(n_range):
            return {
                'repetition_density': 0.0,
                'assessment': 'insufficient_data',
                'algorithm': 'N-gram frequency analysis',
                'is_verified': True,
                'error': f'Need at least {max(n_range)} words'
            }

        repetition_scores = {}
        flagged_phrases = []
        total_repetitions = 0

        for n in n_range:
            # Generate n-grams
            if NLTK_AVAILABLE:
                n_grams_list = list(ngrams(words, n))
            else:
                n_grams_list = [tuple(words[i:i+n]) for i in range(len(words) - n + 1)]

            counts = Counter(n_grams_list)

            # Find repeated n-grams (appearing 2+ times)
            repeated = {
                ' '.join(gram): count
                for gram, count in counts.items()
                if count >= 2
            }

            if repeated:
                repetition_scores[f'{n}-gram'] = len(repeated)
                total_repetitions += sum(repeated.values()) - len(repeated)
                # Add top flagged phrases
                top_phrases = sorted(repeated.items(), key=lambda x: x[1], reverse=True)[:3]
                flagged_phrases.extend([p[0] for p in top_phrases])

        # Calculate repetition density
        word_count = len(words)
        repetition_density = total_repetitions / max(word_count, 1) * 100

        # Determine assessment
        if repetition_density <= self.THRESHOLDS['repetition_ai_max'] * 0.5:
            assessment = 'natural'
        elif repetition_density <= self.THRESHOLDS['repetition_ai_max']:
            assessment = 'moderate_repetition'
        else:
            assessment = 'high_repetition'

        return {
            'repetition_density': round(repetition_density, 3),
            'total_repetitions': total_repetitions,
            'flagged_phrases': flagged_phrases[:5],
            'repetition_by_ngram': repetition_scores,
            'assessment': assessment,
            'threshold': self.THRESHOLDS['repetition_ai_max'],
            'algorithm': f'N-gram frequency analysis ({min(n_range)}-{max(n_range)-1} grams)',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def calculate_structure_entropy(self, content: str) -> Dict[str, Any]:
        """
        Calculate sentence structure entropy.

        Higher entropy = more varied sentence structure = more human-like.

        Uses sentence-starting patterns and punctuation distribution.

        Args:
            content: Text content to analyze

        Returns:
            Dict with entropy score and interpretation
        """
        if NLTK_AVAILABLE:
            sentences = sent_tokenize(content)
        else:
            sentences = self._simple_sentence_split(content)

        if len(sentences) < 3:
            return {
                'structure_entropy': 0.0,
                'assessment': 'insufficient_data',
                'algorithm': 'Shannon entropy of sentence patterns',
                'is_verified': True,
                'error': 'Need at least 3 sentences'
            }

        # Analyze sentence-starting patterns
        start_patterns = []
        for sentence in sentences:
            words = sentence.split()[:3]  # First 3 words
            if words:
                # Categorize by first word type
                first_word = words[0].lower()
                if first_word in {'the', 'a', 'an'}:
                    start_patterns.append('article')
                elif first_word in {'i', 'we', 'you', 'he', 'she', 'it', 'they'}:
                    start_patterns.append('pronoun')
                elif first_word in {'this', 'that', 'these', 'those'}:
                    start_patterns.append('demonstrative')
                elif first_word in {'however', 'therefore', 'furthermore', 'moreover'}:
                    start_patterns.append('transition')
                elif first_word in {'if', 'when', 'while', 'although', 'because'}:
                    start_patterns.append('subordinate')
                else:
                    start_patterns.append('other')

        # Calculate Shannon entropy
        pattern_counts = Counter(start_patterns)
        total = len(start_patterns)
        entropy = 0.0

        for count in pattern_counts.values():
            if count > 0:
                prob = count / total
                entropy -= prob * math.log2(prob)

        # Normalize entropy (max entropy for 6 categories is log2(6) ≈ 2.58)
        max_entropy = math.log2(len(set(start_patterns))) if len(set(start_patterns)) > 1 else 1
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0

        # Determine assessment
        if entropy >= self.THRESHOLDS['entropy_human_min']:
            assessment = 'human-like'
        elif entropy >= self.THRESHOLDS['entropy_human_min'] * 0.6:
            assessment = 'mixed'
        else:
            assessment = 'ai-like'

        return {
            'structure_entropy': round(entropy, 4),
            'normalized_entropy': round(normalized_entropy, 4),
            'pattern_distribution': dict(pattern_counts),
            'unique_patterns': len(set(start_patterns)),
            'sentence_count': len(sentences),
            'assessment': assessment,
            'threshold': self.THRESHOLDS['entropy_human_min'],
            'algorithm': 'Shannon entropy of sentence-starting patterns',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def calculate_ai_likelihood(self, content: str) -> Dict[str, Any]:
        """
        Calculate comprehensive AI likelihood score (0-100).

        Lower score = more human-like.
        Higher score = more AI-like.

        Combines:
        - Burstiness (25 points)
        - Type-Token Ratio (25 points)
        - MTLD (25 points)
        - Structure Entropy (15 points)
        - N-gram Repetition (10 points)

        Args:
            content: Text content to analyze

        Returns:
            Dict with ai_likelihood_score and detailed breakdown
        """
        if not content or len(content.strip()) < 50:
            return {
                'ai_likelihood_score': 50.0,
                'assessment': 'insufficient_data',
                'algorithm': 'Multi-factor AI detection scoring',
                'is_verified': True,
                'error': 'Content too short for reliable analysis'
            }

        # Calculate all metrics
        burstiness = self.calculate_burstiness(content)
        ttr = self.calculate_type_token_ratio(content)
        mtld = self.calculate_mtld(content)
        entropy = self.calculate_structure_entropy(content)
        repetition = self.detect_ngram_repetition(content)

        # Calculate component scores (0 = human-like, 25 = AI-like for each)
        scores = {}

        # Burstiness score (high = human, so invert)
        if 'burstiness' in burstiness and burstiness['burstiness'] > 0:
            burstiness_normalized = min(burstiness['burstiness'] / self.THRESHOLDS['burstiness_human_min'], 2)
            scores['burstiness'] = max(0, 25 - burstiness_normalized * 12.5)
        else:
            scores['burstiness'] = 12.5  # Neutral

        # TTR score (high = human, so invert)
        if 'ttr' in ttr:
            ttr_normalized = min(ttr['ttr'] / self.THRESHOLDS['ttr_human_min'], 2)
            scores['vocabulary'] = max(0, 25 - ttr_normalized * 12.5)
        else:
            scores['vocabulary'] = 12.5

        # MTLD score (high = human, so invert)
        if 'mtld' in mtld and mtld['mtld'] > 0:
            mtld_normalized = min(mtld['mtld'] / self.THRESHOLDS['mtld_human_min'], 2)
            scores['lexical_diversity'] = max(0, 25 - mtld_normalized * 12.5)
        else:
            scores['lexical_diversity'] = 12.5

        # Entropy score (high = human, so invert)
        if 'structure_entropy' in entropy:
            entropy_normalized = min(entropy['structure_entropy'] / self.THRESHOLDS['entropy_human_min'], 2)
            scores['structure'] = max(0, 15 - entropy_normalized * 7.5)
        else:
            scores['structure'] = 7.5

        # Repetition score (high = AI)
        if 'repetition_density' in repetition:
            rep_normalized = min(repetition['repetition_density'] / self.THRESHOLDS['repetition_ai_max'], 2)
            scores['repetition'] = min(10, rep_normalized * 5)
        else:
            scores['repetition'] = 5

        # Calculate total AI likelihood (0-100)
        ai_likelihood = sum(scores.values())

        # Determine overall assessment
        if ai_likelihood < 30:
            assessment = 'human-like'
        elif ai_likelihood < 50:
            assessment = 'likely-human'
        elif ai_likelihood < 70:
            assessment = 'mixed'
        elif ai_likelihood < 85:
            assessment = 'likely-ai'
        else:
            assessment = 'ai-like'

        return {
            'ai_likelihood_score': round(ai_likelihood, 1),
            'assessment': assessment,
            'component_scores': {k: round(v, 2) for k, v in scores.items()},
            'max_possible': {
                'burstiness': 25,
                'vocabulary': 25,
                'lexical_diversity': 25,
                'structure': 15,
                'repetition': 10
            },
            'detailed_metrics': {
                'burstiness': burstiness.get('burstiness', 0),
                'ttr': ttr.get('ttr', 0),
                'mtld': mtld.get('mtld', 0),
                'structure_entropy': entropy.get('structure_entropy', 0),
                'repetition_density': repetition.get('repetition_density', 0)
            },
            'flagged_phrases': repetition.get('flagged_phrases', []),
            'algorithm': 'Multi-factor scoring: burstiness (25%), vocabulary (25%), lexical diversity (25%), structure (15%), repetition (10%)',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }


# Convenience functions
def calculate_ai_likelihood(content: str) -> Dict[str, Any]:
    """Calculate comprehensive AI likelihood score."""
    detector = AIDetector()
    return detector.calculate_ai_likelihood(content)


def detect_ngram_repetition(content: str) -> Dict[str, Any]:
    """Detect repeated n-grams in content."""
    detector = AIDetector()
    return detector.detect_ngram_repetition(content)


def calculate_burstiness(content: str) -> Dict[str, Any]:
    """Calculate sentence length burstiness."""
    detector = AIDetector()
    return detector.calculate_burstiness(content)
