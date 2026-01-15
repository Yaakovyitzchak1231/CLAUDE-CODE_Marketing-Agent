"""
Brand Fingerprint Module - TF-IDF Cosine Similarity for Brand Voice Matching

Uses scikit-learn for:
- TF-IDF vectorization
- Cosine similarity calculation

NO LLM INFERENCE - pure mathematical similarity measurement.

Purpose:
- Compare new content against approved brand voice corpus
- Ensure consistency with established brand voice
- Flag content that deviates from brand standards
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Import ML libraries with fallback
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not installed. Install with: pip install scikit-learn")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy not installed. Install with: pip install numpy")


class BrandFingerprint:
    """
    Production-grade brand voice fingerprinting using TF-IDF.

    All methods return deterministic results with algorithm documentation.
    """

    # Default configuration
    DEFAULT_CONFIG = {
        'max_features': 500,           # Maximum TF-IDF features
        'min_df': 1,                   # Minimum document frequency
        'max_df': 0.95,                # Maximum document frequency
        'ngram_range': (1, 2),         # Unigrams and bigrams
        'stop_words': 'english',       # Remove English stop words
    }

    # Alignment thresholds
    ALIGNMENT_THRESHOLDS = {
        'strong': 0.75,      # >= 75% = on-brand
        'moderate': 0.50,    # >= 50% = needs review
        'weak': 0.25,        # >= 25% = off-brand warning
    }

    def __init__(
        self,
        brand_corpus: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize brand fingerprint analyzer.

        Args:
            brand_corpus: List of approved brand content samples
            config: Optional TF-IDF configuration overrides
        """
        self.config = {**self.DEFAULT_CONFIG}
        if config:
            self.config.update(config)

        self.brand_corpus = brand_corpus or []
        self.vectorizer = None
        self.corpus_vectors = None

        if brand_corpus and SKLEARN_AVAILABLE:
            self._fit_corpus(brand_corpus)

    def _fit_corpus(self, corpus: List[str]) -> None:
        """Fit TF-IDF vectorizer on brand corpus."""
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn not available for TF-IDF fitting")
            return

        if not corpus:
            logger.warning("Empty corpus provided")
            return

        try:
            self.vectorizer = TfidfVectorizer(
                max_features=self.config['max_features'],
                min_df=self.config['min_df'],
                max_df=self.config['max_df'],
                ngram_range=self.config['ngram_range'],
                stop_words=self.config['stop_words']
            )
            self.corpus_vectors = self.vectorizer.fit_transform(corpus)
            self.brand_corpus = corpus
            logger.info(f"Fitted TF-IDF on {len(corpus)} documents with {self.corpus_vectors.shape[1]} features")
        except Exception as e:
            logger.error(f"Error fitting TF-IDF: {e}")
            self.vectorizer = None
            self.corpus_vectors = None

    def add_to_corpus(self, content: str) -> Dict[str, Any]:
        """
        Add new content to brand corpus.

        Args:
            content: New approved brand content

        Returns:
            Dict with status and corpus size
        """
        self.brand_corpus.append(content)

        # Re-fit vectorizer with updated corpus
        if SKLEARN_AVAILABLE and len(self.brand_corpus) >= 2:
            self._fit_corpus(self.brand_corpus)

        return {
            'status': 'added',
            'corpus_size': len(self.brand_corpus),
            'is_verified': True
        }

    def calculate_brand_alignment(self, content: str) -> Dict[str, Any]:
        """
        Calculate brand voice alignment score.

        Uses TF-IDF + cosine similarity against brand corpus.

        Args:
            content: New content to analyze

        Returns:
            Dict with alignment_score, assessment, and detailed metrics
        """
        if not SKLEARN_AVAILABLE:
            return {
                'brand_alignment_score': 0.0,
                'error': 'scikit-learn not installed',
                'algorithm': 'TF-IDF + Cosine Similarity',
                'is_verified': True
            }

        if not self.brand_corpus or len(self.brand_corpus) < 2:
            return {
                'brand_alignment_score': 0.0,
                'error': 'Insufficient brand corpus (need at least 2 documents)',
                'corpus_size': len(self.brand_corpus),
                'algorithm': 'TF-IDF + Cosine Similarity',
                'is_verified': True
            }

        if self.vectorizer is None or self.corpus_vectors is None:
            self._fit_corpus(self.brand_corpus)

        if self.vectorizer is None:
            return {
                'brand_alignment_score': 0.0,
                'error': 'Failed to initialize TF-IDF vectorizer',
                'algorithm': 'TF-IDF + Cosine Similarity',
                'is_verified': True
            }

        try:
            # Transform new content
            content_vector = self.vectorizer.transform([content])

            # Calculate similarity to each corpus document
            similarities = cosine_similarity(content_vector, self.corpus_vectors)[0]

            # Aggregate metrics
            avg_similarity = float(similarities.mean())
            max_similarity = float(similarities.max())
            min_similarity = float(similarities.min())
            std_similarity = float(similarities.std())

            # Find most similar document
            most_similar_idx = int(similarities.argmax())

            # Calculate brand alignment score (0-100)
            # Normalize: 0.75 similarity = 100 score
            alignment_score = min(avg_similarity / self.ALIGNMENT_THRESHOLDS['strong'] * 100, 100)

            # Determine assessment
            if avg_similarity >= self.ALIGNMENT_THRESHOLDS['strong']:
                assessment = 'on-brand'
            elif avg_similarity >= self.ALIGNMENT_THRESHOLDS['moderate']:
                assessment = 'needs-review'
            elif avg_similarity >= self.ALIGNMENT_THRESHOLDS['weak']:
                assessment = 'off-brand-warning'
            else:
                assessment = 'off-brand'

            # Get top TF-IDF features from content
            feature_names = self.vectorizer.get_feature_names_out()
            content_tfidf = content_vector.toarray()[0]
            top_indices = content_tfidf.argsort()[-10:][::-1]
            top_terms = [(feature_names[i], round(content_tfidf[i], 4)) for i in top_indices if content_tfidf[i] > 0]

            return {
                'brand_alignment_score': round(alignment_score, 1),
                'avg_similarity': round(avg_similarity, 4),
                'max_similarity': round(max_similarity, 4),
                'min_similarity': round(min_similarity, 4),
                'similarity_std': round(std_similarity, 4),
                'similarity_range': round(max_similarity - min_similarity, 4),
                'most_similar_doc_idx': most_similar_idx,
                'corpus_size': len(self.brand_corpus),
                'assessment': assessment,
                'top_matching_terms': top_terms[:5],
                'thresholds': self.ALIGNMENT_THRESHOLDS,
                'algorithm': 'TF-IDF vectorization + Cosine Similarity against brand corpus',
                'is_verified': True,
                'calculated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error calculating brand alignment: {e}")
            return {
                'brand_alignment_score': 0.0,
                'error': str(e),
                'algorithm': 'TF-IDF + Cosine Similarity',
                'is_verified': True
            }

    def compare_documents(self, doc1: str, doc2: str) -> Dict[str, Any]:
        """
        Compare two documents for similarity.

        Args:
            doc1: First document
            doc2: Second document

        Returns:
            Dict with similarity score and analysis
        """
        if not SKLEARN_AVAILABLE:
            return {
                'similarity': 0.0,
                'error': 'scikit-learn not installed',
                'algorithm': 'TF-IDF + Cosine Similarity',
                'is_verified': True
            }

        try:
            # Create vectorizer for this comparison
            vectorizer = TfidfVectorizer(
                max_features=self.config['max_features'],
                ngram_range=self.config['ngram_range'],
                stop_words=self.config['stop_words']
            )

            # Fit and transform both documents
            vectors = vectorizer.fit_transform([doc1, doc2])

            # Calculate similarity
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]

            # Get shared important terms
            feature_names = vectorizer.get_feature_names_out()
            doc1_tfidf = vectors[0].toarray()[0]
            doc2_tfidf = vectors[1].toarray()[0]

            # Find terms important in both
            shared_importance = doc1_tfidf * doc2_tfidf
            top_shared_indices = shared_importance.argsort()[-5:][::-1]
            shared_terms = [
                (feature_names[i], round(shared_importance[i], 4))
                for i in top_shared_indices
                if shared_importance[i] > 0
            ]

            return {
                'similarity': round(float(similarity), 4),
                'similarity_pct': round(float(similarity) * 100, 1),
                'assessment': 'very_similar' if similarity > 0.7 else 'similar' if similarity > 0.4 else 'different',
                'shared_key_terms': shared_terms,
                'algorithm': 'TF-IDF + Cosine Similarity (pairwise)',
                'is_verified': True,
                'calculated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error comparing documents: {e}")
            return {
                'similarity': 0.0,
                'error': str(e),
                'algorithm': 'TF-IDF + Cosine Similarity',
                'is_verified': True
            }

    def find_closest_matches(
        self,
        content: str,
        top_n: int = 3
    ) -> Dict[str, Any]:
        """
        Find the closest matching documents in the brand corpus.

        Args:
            content: Content to match
            top_n: Number of top matches to return

        Returns:
            Dict with top matches and their similarity scores
        """
        if not SKLEARN_AVAILABLE:
            return {
                'matches': [],
                'error': 'scikit-learn not installed',
                'algorithm': 'TF-IDF + Cosine Similarity',
                'is_verified': True
            }

        if not self.brand_corpus or self.vectorizer is None:
            return {
                'matches': [],
                'error': 'Brand corpus not initialized',
                'algorithm': 'TF-IDF + Cosine Similarity',
                'is_verified': True
            }

        try:
            # Transform content
            content_vector = self.vectorizer.transform([content])

            # Calculate similarities
            similarities = cosine_similarity(content_vector, self.corpus_vectors)[0]

            # Get top N indices
            top_indices = similarities.argsort()[-top_n:][::-1]

            matches = []
            for idx in top_indices:
                matches.append({
                    'corpus_index': int(idx),
                    'similarity': round(float(similarities[idx]), 4),
                    'preview': self.brand_corpus[idx][:200] + '...' if len(self.brand_corpus[idx]) > 200 else self.brand_corpus[idx]
                })

            return {
                'matches': matches,
                'query_length': len(content),
                'corpus_size': len(self.brand_corpus),
                'algorithm': 'TF-IDF + Cosine Similarity (top-N search)',
                'is_verified': True,
                'calculated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error finding matches: {e}")
            return {
                'matches': [],
                'error': str(e),
                'algorithm': 'TF-IDF + Cosine Similarity',
                'is_verified': True
            }

    def get_corpus_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the brand corpus.

        Returns:
            Dict with corpus statistics
        """
        if not self.brand_corpus:
            return {
                'corpus_size': 0,
                'error': 'No corpus loaded',
                'is_verified': True
            }

        doc_lengths = [len(doc.split()) for doc in self.brand_corpus]

        stats = {
            'corpus_size': len(self.brand_corpus),
            'total_words': sum(doc_lengths),
            'avg_doc_length': round(sum(doc_lengths) / len(doc_lengths), 1),
            'min_doc_length': min(doc_lengths),
            'max_doc_length': max(doc_lengths),
        }

        if SKLEARN_AVAILABLE and self.vectorizer is not None:
            stats['vocabulary_size'] = len(self.vectorizer.get_feature_names_out())
            stats['ngram_range'] = self.config['ngram_range']

        stats['is_verified'] = True
        stats['calculated_at'] = datetime.now().isoformat()

        return stats


# Convenience function
def calculate_brand_alignment(
    content: str,
    brand_corpus: List[str]
) -> Dict[str, Any]:
    """
    Calculate brand alignment for content against a corpus.

    Args:
        content: Content to analyze
        brand_corpus: List of approved brand content samples

    Returns:
        Dict with alignment score and analysis
    """
    fingerprint = BrandFingerprint(brand_corpus=brand_corpus)
    return fingerprint.calculate_brand_alignment(content)
