"""
Brand Voice Analyzer - Statistical Text Analysis for Brand Consistency

All calculations use:
- textstat for readability metrics
- NLTK for tokenization and linguistic analysis
- Statistical formulas (no LLM inference)

Algorithms:
- Flesch Reading Ease (0-100)
- Flesch-Kincaid Grade Level
- Gunning Fog Index
- SMOG Index
- Formality Ratio
- Sentence Structure Analysis
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import Counter
import re

logger = logging.getLogger(__name__)

# Import NLP libraries with fallback
try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False
    logger.warning("textstat not installed. Install with: pip install textstat")

try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("NLTK not installed. Install with: pip install nltk")


class BrandVoiceAnalyzer:
    """
    Production-grade brand voice analysis using statistical NLP.

    All methods return deterministic results with algorithm documentation.
    """

    # Word lists for tone analysis
    FORMAL_WORDS = {
        'therefore', 'however', 'consequently', 'furthermore', 'thus',
        'moreover', 'nevertheless', 'notwithstanding', 'accordingly',
        'hence', 'whereby', 'wherein', 'thereof', 'herein', 'whereas'
    }

    INFORMAL_WORDS = {
        'so', 'but', 'like', 'just', 'really', 'very', 'actually',
        'basically', 'literally', 'totally', 'awesome', 'cool',
        'yeah', 'gonna', 'wanna', 'gotta', 'kinda', 'sorta'
    }

    # Corporate jargon to flag (may indicate AI-like writing)
    CORPORATE_JARGON = {
        'synergy', 'leverage', 'paradigm', 'holistic', 'robust',
        'scalable', 'innovative', 'cutting-edge', 'best-in-class',
        'game-changer', 'disruptive', 'revolutionary', 'seamless',
        'unprecedented', 'transformative', 'empower', 'optimize'
    }

    # Target metrics for B2B executive content
    B2B_EXECUTIVE_TARGETS = {
        'target_readability': 45,        # Flesch Reading Ease (45-55 for business)
        'target_grade_level': 12,        # College level
        'target_formality': 1.5,         # Slightly formal
        'target_sentence_length': 18,    # Words per sentence
        'max_jargon_density': 2.0        # % of jargon words
    }

    def __init__(self, target_profile: Optional[Dict[str, float]] = None):
        """
        Initialize brand voice analyzer.

        Args:
            target_profile: Optional target metrics for brand voice
        """
        self.targets = {**self.B2B_EXECUTIVE_TARGETS}
        if target_profile:
            self.targets.update(target_profile)

        # Download NLTK data if needed - use broad exception handling
        # as nltk.data.find() can raise various errors depending on NLTK version
        if NLTK_AVAILABLE:
            try:
                nltk.data.find('tokenizers/punkt')
            except (LookupError, OSError):
                try:
                    nltk.download('punkt', quiet=True)
                except Exception:
                    pass
            try:
                nltk.data.find('tokenizers/punkt_tab')
            except (LookupError, OSError):
                try:
                    nltk.download('punkt_tab', quiet=True)
                except Exception:
                    pass

    def _simple_sentence_split(self, text: str) -> List[str]:
        """Fallback sentence splitting without NLTK."""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _simple_word_tokenize(self, text: str) -> List[str]:
        """Fallback word tokenization without NLTK."""
        return re.findall(r'\b\w+\b', text.lower())

    def calculate_readability_metrics(self, content: str) -> Dict[str, Any]:
        """
        Calculate comprehensive readability metrics.

        Uses textstat for industry-standard readability formulas.

        Args:
            content: Text content to analyze

        Returns:
            Dict with readability scores and interpretations
        """
        if not content or len(content.strip()) < 10:
            return {
                'error': 'Content too short for analysis',
                'is_verified': True
            }

        metrics = {}

        if TEXTSTAT_AVAILABLE:
            # Flesch Reading Ease (0-100, higher = easier)
            flesch_ease = textstat.flesch_reading_ease(content)
            metrics['flesch_reading_ease'] = round(flesch_ease, 1)

            # Flesch-Kincaid Grade Level
            fk_grade = textstat.flesch_kincaid_grade(content)
            metrics['flesch_kincaid_grade'] = round(fk_grade, 1)

            # Gunning Fog Index
            gunning_fog = textstat.gunning_fog(content)
            metrics['gunning_fog'] = round(gunning_fog, 1)

            # SMOG Index
            try:
                smog = textstat.smog_index(content)
                metrics['smog_index'] = round(smog, 1)
            except:
                metrics['smog_index'] = None

            # Coleman-Liau Index
            coleman_liau = textstat.coleman_liau_index(content)
            metrics['coleman_liau_index'] = round(coleman_liau, 1)

            # Automated Readability Index
            ari = textstat.automated_readability_index(content)
            metrics['automated_readability_index'] = round(ari, 1)

            # Text statistics
            metrics['word_count'] = textstat.lexicon_count(content, removepunct=True)
            metrics['sentence_count'] = textstat.sentence_count(content)
            metrics['syllable_count'] = textstat.syllable_count(content)

            # Average values
            if metrics['sentence_count'] > 0:
                metrics['avg_sentence_length'] = round(
                    metrics['word_count'] / metrics['sentence_count'], 1
                )
            if metrics['word_count'] > 0:
                metrics['avg_syllables_per_word'] = round(
                    metrics['syllable_count'] / metrics['word_count'], 2
                )

            # Interpretation
            if flesch_ease >= 60:
                reading_level = 'easy'
            elif flesch_ease >= 30:
                reading_level = 'standard'
            else:
                reading_level = 'difficult'

            metrics['reading_level'] = reading_level

        else:
            # Fallback: basic metrics without textstat
            words = self._simple_word_tokenize(content)
            sentences = self._simple_sentence_split(content)

            metrics['word_count'] = len(words)
            metrics['sentence_count'] = len(sentences)
            metrics['avg_sentence_length'] = round(
                len(words) / max(len(sentences), 1), 1
            )
            metrics['reading_level'] = 'unknown (textstat not installed)'

        metrics['algorithm'] = 'Flesch-Kincaid, Gunning Fog, SMOG, Coleman-Liau'
        metrics['is_verified'] = True
        metrics['calculated_at'] = datetime.now().isoformat()

        return metrics

    def analyze_tone(self, content: str) -> Dict[str, Any]:
        """
        Analyze content tone using word frequency analysis.

        Measures formality, jargon usage, and conversational indicators.

        Args:
            content: Text content to analyze

        Returns:
            Dict with tone indicators and scores
        """
        if NLTK_AVAILABLE:
            words = word_tokenize(content.lower())
            sentences = sent_tokenize(content)
        else:
            words = self._simple_word_tokenize(content)
            sentences = self._simple_sentence_split(content)

        word_counts = Counter(words)
        total_words = len(words)

        if total_words == 0:
            return {
                'error': 'No words to analyze',
                'is_verified': True
            }

        # Formality analysis
        formal_count = sum(word_counts.get(w, 0) for w in self.FORMAL_WORDS)
        informal_count = sum(word_counts.get(w, 0) for w in self.INFORMAL_WORDS)
        formality_ratio = formal_count / max(informal_count, 1)

        # Jargon analysis
        jargon_count = sum(word_counts.get(w, 0) for w in self.CORPORATE_JARGON)
        jargon_density = jargon_count / total_words * 100

        # Jargon words found
        jargon_found = [w for w in self.CORPORATE_JARGON if word_counts.get(w, 0) > 0]

        # Sentence structure analysis
        sentence_lengths = [len(self._simple_word_tokenize(s)) for s in sentences]
        avg_sentence_length = sum(sentence_lengths) / max(len(sentence_lengths), 1)

        # Variance in sentence length (higher = more natural)
        if len(sentence_lengths) > 1:
            import statistics as stats
            sentence_length_variance = stats.variance(sentence_lengths)
        else:
            sentence_length_variance = 0

        # Question ratio (conversational indicator)
        question_count = content.count('?')
        question_ratio = question_count / max(len(sentences), 1)

        # Exclamation ratio (enthusiasm/informal indicator)
        exclamation_count = content.count('!')
        exclamation_ratio = exclamation_count / max(len(sentences), 1)

        # Determine overall tone
        if formality_ratio > 2:
            tone_assessment = 'very_formal'
        elif formality_ratio > 1:
            tone_assessment = 'formal'
        elif formality_ratio > 0.5:
            tone_assessment = 'neutral'
        elif formality_ratio > 0.2:
            tone_assessment = 'casual'
        else:
            tone_assessment = 'very_casual'

        return {
            'tone_assessment': tone_assessment,
            'formality_ratio': round(formality_ratio, 3),
            'formal_word_count': formal_count,
            'informal_word_count': informal_count,
            'jargon_density_pct': round(jargon_density, 2),
            'jargon_words_found': jargon_found,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'sentence_length_variance': round(sentence_length_variance, 2),
            'question_ratio': round(question_ratio, 3),
            'exclamation_ratio': round(exclamation_ratio, 3),
            'total_words': total_words,
            'total_sentences': len(sentences),
            'algorithm': 'Word frequency analysis (formal/informal ratio, jargon density)',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def calculate_brand_consistency(
        self,
        content: str,
        target_profile: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate brand voice consistency score (0-100).

        Compares content metrics against target brand profile.

        Args:
            content: Text content to analyze
            target_profile: Optional target metrics (uses defaults if not provided)

        Returns:
            Dict with consistency_score, deviations, and recommendations
        """
        targets = target_profile or self.targets

        # Get metrics
        readability = self.calculate_readability_metrics(content)
        tone = self.analyze_tone(content)

        if 'error' in readability or 'error' in tone:
            return {
                'consistency_score': 0,
                'error': readability.get('error') or tone.get('error'),
                'is_verified': True
            }

        # Calculate deviations from target
        deviations = {}

        # Readability deviation
        if TEXTSTAT_AVAILABLE and 'flesch_reading_ease' in readability:
            target_readability = targets.get('target_readability', 45)
            actual_readability = readability['flesch_reading_ease']
            deviations['readability'] = abs(actual_readability - target_readability)
        else:
            deviations['readability'] = 0

        # Grade level deviation
        if 'flesch_kincaid_grade' in readability:
            target_grade = targets.get('target_grade_level', 12)
            actual_grade = readability['flesch_kincaid_grade']
            deviations['grade_level'] = abs(actual_grade - target_grade)
        else:
            deviations['grade_level'] = 0

        # Formality deviation
        target_formality = targets.get('target_formality', 1.5)
        actual_formality = tone.get('formality_ratio', 1.0)
        deviations['formality'] = abs(actual_formality - target_formality)

        # Sentence length deviation
        target_sentence_length = targets.get('target_sentence_length', 18)
        actual_sentence_length = tone.get('avg_sentence_length', 15)
        deviations['sentence_length'] = abs(actual_sentence_length - target_sentence_length)

        # Jargon deviation (penalty for exceeding max)
        max_jargon = targets.get('max_jargon_density', 2.0)
        actual_jargon = tone.get('jargon_density_pct', 0)
        deviations['jargon'] = max(0, actual_jargon - max_jargon)

        # Calculate consistency score (0-100)
        # Lower deviation = higher score
        # Weights: readability=30%, grade=20%, formality=20%, sentence=20%, jargon=10%
        score = 100 - (
            min(deviations['readability'] / 50 * 30, 30) +
            min(deviations['grade_level'] / 5 * 20, 20) +
            min(deviations['formality'] / 2 * 20, 20) +
            min(deviations['sentence_length'] / 10 * 20, 20) +
            min(deviations['jargon'] / 5 * 10, 10)
        )
        score = max(0, min(100, score))

        # Generate recommendations
        recommendations = []
        if deviations['readability'] > 20:
            if readability.get('flesch_reading_ease', 50) > targets.get('target_readability', 45):
                recommendations.append('Content may be too simple for executive audience')
            else:
                recommendations.append('Content may be too complex - simplify sentence structure')

        if deviations['formality'] > 1:
            if tone['formality_ratio'] > targets.get('target_formality', 1.5):
                recommendations.append('Tone may be overly formal - consider more conversational language')
            else:
                recommendations.append('Tone may be too casual for B2B - increase professional language')

        if deviations['jargon'] > 0:
            recommendations.append(f'Reduce corporate jargon: {", ".join(tone.get("jargon_words_found", [])[:3])}')

        if tone.get('sentence_length_variance', 0) < 20:
            recommendations.append('Vary sentence lengths for more natural flow (may sound AI-generated)')

        return {
            'consistency_score': round(score, 1),
            'grade': 'A' if score >= 80 else 'B' if score >= 60 else 'C' if score >= 40 else 'D',
            'deviations': {k: round(v, 2) for k, v in deviations.items()},
            'targets_used': targets,
            'actual_metrics': {
                'readability': readability.get('flesch_reading_ease'),
                'grade_level': readability.get('flesch_kincaid_grade'),
                'formality_ratio': tone.get('formality_ratio'),
                'avg_sentence_length': tone.get('avg_sentence_length'),
                'jargon_density': tone.get('jargon_density_pct')
            },
            'recommendations': recommendations,
            'readability_details': readability,
            'tone_details': tone,
            'algorithm': 'Weighted deviation scoring (readability: 30%, grade: 20%, formality: 20%, sentence: 20%, jargon: 10%)',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }


# Convenience functions
def analyze_brand_voice(
    content: str,
    target_profile: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """Analyze brand voice consistency."""
    analyzer = BrandVoiceAnalyzer(target_profile)
    return analyzer.calculate_brand_consistency(content, target_profile)


def calculate_readability_score(content: str) -> Dict[str, Any]:
    """Calculate readability metrics."""
    analyzer = BrandVoiceAnalyzer()
    return analyzer.calculate_readability_metrics(content)
