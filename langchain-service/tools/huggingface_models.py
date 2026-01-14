"""
HuggingFace Model Loaders
Pre-trained models for sentiment analysis, NER, and text classification
"""

from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoModelForTokenClassification
)
from typing import List, Dict, Any, Optional
import structlog
import torch
from functools import lru_cache

logger = structlog.get_logger()


class HuggingFaceModelManager:
    """
    Manages HuggingFace model loading and inference

    Implements caching to avoid reloading models
    """

    def __init__(self, device: Optional[str] = None):
        """
        Initialize model manager

        Args:
            device: Device to run models on ('cpu', 'cuda', or None for auto-detect)
        """
        if device is None:
            self.device = 0 if torch.cuda.is_available() else -1
        else:
            self.device = device

        self._pipelines = {}

        logger.info(
            "huggingface_manager_initialized",
            device="cuda" if self.device == 0 else "cpu"
        )

    @lru_cache(maxsize=10)
    def get_pipeline(self, task: str, model: str):
        """
        Get or create HuggingFace pipeline

        Args:
            task: Task type (sentiment-analysis, ner, text-classification, etc.)
            model: Model name or path

        Returns:
            Pipeline instance
        """
        cache_key = f"{task}:{model}"

        if cache_key not in self._pipelines:
            logger.info("loading_model", task=task, model=model)

            self._pipelines[cache_key] = pipeline(
                task,
                model=model,
                device=self.device
            )

            logger.info("model_loaded", task=task, model=model)

        return self._pipelines[cache_key]


# === Sentiment Analysis ===

class SentimentAnalyzer:
    """
    Sentiment analysis using pre-trained models

    Models:
    - distilbert-base-uncased-finetuned-sst-2-english (default)
    - cardiffnlp/twitter-roberta-base-sentiment
    - finiteautomata/bertweet-base-sentiment-analysis
    """

    def __init__(
        self,
        model_name: str = "distilbert-base-uncased-finetuned-sst-2-english",
        device: Optional[str] = None
    ):
        self.manager = HuggingFaceModelManager(device=device)
        self.model_name = model_name
        self.pipeline = self.manager.get_pipeline("sentiment-analysis", model_name)

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text

        Args:
            text: Text to analyze

        Returns:
            Dictionary with label and score
        """
        try:
            result = self.pipeline(text[:512])[0]  # Limit to 512 tokens

            logger.debug(
                "sentiment_analyzed",
                text_length=len(text),
                label=result["label"],
                score=result["score"]
            )

            return {
                "text": text[:100] + "..." if len(text) > 100 else text,
                "sentiment": result["label"],
                "confidence": round(result["score"], 4),
                "model": self.model_name
            }

        except Exception as e:
            logger.error("sentiment_analysis_error", error=str(e))
            return {
                "error": str(e),
                "text": text[:100]
            }

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment of multiple texts

        Args:
            texts: List of texts to analyze

        Returns:
            List of sentiment results
        """
        try:
            # Truncate texts to 512 tokens
            truncated_texts = [text[:512] for text in texts]

            results = self.pipeline(truncated_texts)

            return [
                {
                    "text": text[:100] + "..." if len(text) > 100 else text,
                    "sentiment": result["label"],
                    "confidence": round(result["score"], 4),
                    "model": self.model_name
                }
                for text, result in zip(texts, results)
            ]

        except Exception as e:
            logger.error("batch_sentiment_error", error=str(e))
            return [{"error": str(e)} for _ in texts]


# === Named Entity Recognition ===

class NamedEntityRecognizer:
    """
    Named Entity Recognition using pre-trained models

    Models:
    - dslim/bert-base-NER (default) - General purpose NER
    - dbmdz/bert-large-cased-finetuned-conll03-english - High accuracy
    - Jean-Baptiste/camembert-ner - Multilingual support
    """

    def __init__(
        self,
        model_name: str = "dslim/bert-base-NER",
        device: Optional[str] = None
    ):
        self.manager = HuggingFaceModelManager(device=device)
        self.model_name = model_name
        self.pipeline = self.manager.get_pipeline("ner", model_name)

    def extract_entities(
        self,
        text: str,
        aggregation_strategy: str = "simple"
    ) -> Dict[str, Any]:
        """
        Extract named entities from text

        Args:
            text: Text to analyze
            aggregation_strategy: How to aggregate sub-tokens (simple, first, average, max)

        Returns:
            Dictionary with entities grouped by type
        """
        try:
            # Extract entities
            entities = self.pipeline(
                text,
                aggregation_strategy=aggregation_strategy
            )

            # Group by entity type
            grouped_entities = {}
            for entity in entities:
                entity_type = entity["entity_group"]
                entity_text = entity["word"]
                score = entity["score"]

                if entity_type not in grouped_entities:
                    grouped_entities[entity_type] = []

                grouped_entities[entity_type].append({
                    "text": entity_text,
                    "confidence": round(score, 4),
                    "start": entity["start"],
                    "end": entity["end"]
                })

            logger.debug(
                "entities_extracted",
                text_length=len(text),
                entity_count=len(entities),
                entity_types=list(grouped_entities.keys())
            )

            return {
                "text": text[:100] + "..." if len(text) > 100 else text,
                "entities": grouped_entities,
                "total_entities": len(entities),
                "model": self.model_name
            }

        except Exception as e:
            logger.error("ner_error", error=str(e))
            return {
                "error": str(e),
                "text": text[:100]
            }

    def extract_organizations(self, text: str) -> List[str]:
        """
        Extract organization names from text

        Args:
            text: Text to analyze

        Returns:
            List of organization names
        """
        result = self.extract_entities(text)

        if "error" in result:
            return []

        orgs = result.get("entities", {}).get("ORG", [])
        return [entity["text"] for entity in orgs]

    def extract_people(self, text: str) -> List[str]:
        """
        Extract person names from text

        Args:
            text: Text to analyze

        Returns:
            List of person names
        """
        result = self.extract_entities(text)

        if "error" in result:
            return []

        people = result.get("entities", {}).get("PER", [])
        return [entity["text"] for entity in people]

    def extract_locations(self, text: str) -> List[str]:
        """
        Extract location names from text

        Args:
            text: Text to analyze

        Returns:
            List of location names
        """
        result = self.extract_entities(text)

        if "error" in result:
            return []

        locations = result.get("entities", {}).get("LOC", [])
        return [entity["text"] for entity in locations]


# === Zero-Shot Classification ===

class ZeroShotClassifier:
    """
    Zero-shot text classification

    Classify text without training data by providing candidate labels
    """

    def __init__(
        self,
        model_name: str = "facebook/bart-large-mnli",
        device: Optional[str] = None
    ):
        self.manager = HuggingFaceModelManager(device=device)
        self.model_name = model_name
        self.pipeline = self.manager.get_pipeline("zero-shot-classification", model_name)

    def classify(
        self,
        text: str,
        candidate_labels: List[str],
        multi_label: bool = False
    ) -> Dict[str, Any]:
        """
        Classify text into one or more candidate labels

        Args:
            text: Text to classify
            candidate_labels: List of possible labels
            multi_label: Allow multiple labels (default: single label)

        Returns:
            Classification results with scores
        """
        try:
            result = self.pipeline(
                text[:512],
                candidate_labels=candidate_labels,
                multi_label=multi_label
            )

            logger.debug(
                "text_classified",
                text_length=len(text),
                top_label=result["labels"][0],
                score=result["scores"][0]
            )

            return {
                "text": text[:100] + "..." if len(text) > 100 else text,
                "labels": result["labels"],
                "scores": [round(score, 4) for score in result["scores"]],
                "top_label": result["labels"][0],
                "top_score": round(result["scores"][0], 4),
                "model": self.model_name
            }

        except Exception as e:
            logger.error("classification_error", error=str(e))
            return {
                "error": str(e),
                "text": text[:100]
            }


# === Content Type Classifier ===

class ContentTypeClassifier:
    """
    Classify content type (blog post, pricing page, product page, etc.)

    Uses zero-shot classification with predefined labels
    """

    def __init__(self, device: Optional[str] = None):
        self.classifier = ZeroShotClassifier(device=device)

        self.content_type_labels = [
            "blog post",
            "pricing page",
            "product page",
            "about page",
            "contact page",
            "documentation",
            "tutorial",
            "case study",
            "landing page",
            "news article"
        ]

    def classify_content(self, text: str) -> Dict[str, Any]:
        """
        Classify content type

        Args:
            text: Content to classify

        Returns:
            Classification result with content type
        """
        result = self.classifier.classify(
            text,
            candidate_labels=self.content_type_labels,
            multi_label=False
        )

        return {
            "content_type": result.get("top_label"),
            "confidence": result.get("top_score"),
            "all_types": list(zip(result.get("labels", []), result.get("scores", [])))
        }


# === Topic Extraction ===

class TopicExtractor:
    """
    Extract main topics from text using zero-shot classification
    """

    def __init__(self, device: Optional[str] = None):
        self.classifier = ZeroShotClassifier(device=device)

    def extract_topics(
        self,
        text: str,
        topic_candidates: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract topics from text

        Args:
            text: Text to analyze
            topic_candidates: Optional list of topic candidates
                            (defaults to common B2B marketing topics)

        Returns:
            Topics with confidence scores
        """
        if topic_candidates is None:
            topic_candidates = [
                "marketing strategy",
                "sales enablement",
                "customer success",
                "product development",
                "content marketing",
                "SEO and search",
                "social media",
                "email marketing",
                "analytics and data",
                "automation",
                "AI and technology",
                "leadership and management"
            ]

        result = self.classifier.classify(
            text,
            candidate_labels=topic_candidates,
            multi_label=True
        )

        # Filter topics with confidence > 0.3
        relevant_topics = [
            {"topic": label, "confidence": score}
            for label, score in zip(result["labels"], result["scores"])
            if score > 0.3
        ]

        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "topics": relevant_topics,
            "primary_topic": result["top_label"],
            "primary_confidence": result["top_score"]
        }


# === Factory Functions ===

def create_sentiment_analyzer(
    model: str = "distilbert-base-uncased-finetuned-sst-2-english"
) -> SentimentAnalyzer:
    """Create sentiment analyzer instance"""
    return SentimentAnalyzer(model_name=model)


def create_ner_extractor(
    model: str = "dslim/bert-base-NER"
) -> NamedEntityRecognizer:
    """Create NER extractor instance"""
    return NamedEntityRecognizer(model_name=model)


def create_zero_shot_classifier(
    model: str = "facebook/bart-large-mnli"
) -> ZeroShotClassifier:
    """Create zero-shot classifier instance"""
    return ZeroShotClassifier(model_name=model)


def create_content_classifier() -> ContentTypeClassifier:
    """Create content type classifier instance"""
    return ContentTypeClassifier()


def create_topic_extractor() -> TopicExtractor:
    """Create topic extractor instance"""
    return TopicExtractor()
