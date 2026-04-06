"""
Comprehensive Financial Sentiment Analyzer using Multiple FinBERT Models

Provides multi-dimensional analysis using:
- FinBERT-Sentiment (yiyanghkust/finbert-tone): Positive, Neutral, Negative
- FinBERT-ESG (yiyanghkust/finbert-esg): Environmental, Social, Governance, None
- FinBERT-FLS (yiyanghkust/finbert-fls): Forward-Looking Statement classification
- ProsusAI/finbert: Alternative sentiment model

This enables comprehensive analysis of financial news for:
- Market sentiment (bullish/bearish)
- ESG relevance and classification
- Forward-looking vs historical statements
"""

from typing import List, Dict, Optional, Tuple, Literal
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

import logging
logger = logging.getLogger(__name__)


class FinBERTModel(str, Enum):
    """Available FinBERT model variants"""
    SENTIMENT = "yiyanghkust/finbert-tone"        # Positive, Neutral, Negative
    ESG = "yiyanghkust/finbert-esg"               # Environmental, Social, Governance, None
    FLS = "yiyanghkust/finbert-fls"               # Specific-FLS, Non-specific-FLS, Not-FLS
    PROSUS = "ProsusAI/finbert"                   # Alternative sentiment model


@dataclass
class SentimentResult:
    """Result of sentiment analysis"""
    text: str
    sentiment: str  # 'positive', 'negative', 'neutral'
    confidence: float
    scores: Dict[str, float]  # All class probabilities


@dataclass
class ESGResult:
    """Result of ESG classification"""
    text: str
    category: str  # 'Environmental', 'Social', 'Governance', 'None'
    confidence: float
    scores: Dict[str, float]


@dataclass
class FLSResult:
    """Result of Forward-Looking Statement classification"""
    text: str
    fls_type: str  # 'Specific_FLS', 'Non-specific_FLS', 'Not_FLS'
    is_forward_looking: bool
    confidence: float
    scores: Dict[str, float]


@dataclass
class ComprehensiveAnalysisResult:
    """Complete multi-model analysis result"""
    text: str
    sentiment: SentimentResult
    esg: Optional[ESGResult] = None
    fls: Optional[FLSResult] = None


class MultiModelAnalyzer:
    """
    Multi-model financial text analyzer using various FinBERT models.

    Supports lazy loading of models to conserve memory.
    Only loads models when they are first used.
    """

    def __init__(self, device: str = "auto"):
        """
        Initialize the multi-model analyzer.

        Args:
            device: Device to run models on ('cpu', 'cuda', 'auto')
        """
        self.device = device
        self._device_id = None
        self._pipelines: Dict[str, any] = {}
        self._initialized_models: set = set()

    def _get_device_id(self) -> int:
        """Get the device ID for pipeline initialization"""
        if self._device_id is not None:
            return self._device_id

        try:
            import torch
            if self.device == "auto":
                self._device_id = 0 if torch.cuda.is_available() else -1
            elif self.device == "cuda":
                self._device_id = 0
            else:
                self._device_id = -1
        except ImportError:
            self._device_id = -1

        return self._device_id

    def _load_model(self, model_name: str) -> any:
        """Lazy load a specific model"""
        if model_name in self._pipelines:
            return self._pipelines[model_name]

        try:
            from transformers import (
                BertTokenizer,
                BertForSequenceClassification,
                pipeline,
                AutoTokenizer,
                AutoModelForSequenceClassification
            )

            logger.info(f"Loading FinBERT model: {model_name}...")

            device_id = self._get_device_id()

            # Different models have different label counts
            if model_name == FinBERTModel.SENTIMENT.value:
                model = BertForSequenceClassification.from_pretrained(model_name, num_labels=3)
                tokenizer = BertTokenizer.from_pretrained(model_name)
            elif model_name == FinBERTModel.ESG.value:
                model = BertForSequenceClassification.from_pretrained(model_name, num_labels=4)
                tokenizer = BertTokenizer.from_pretrained(model_name)
            elif model_name == FinBERTModel.FLS.value:
                model = BertForSequenceClassification.from_pretrained(model_name, num_labels=3)
                tokenizer = BertTokenizer.from_pretrained(model_name)
            elif model_name == FinBERTModel.PROSUS.value:
                model = AutoModelForSequenceClassification.from_pretrained(model_name)
                tokenizer = AutoTokenizer.from_pretrained(model_name)
            else:
                raise ValueError(f"Unknown model: {model_name}")

            nlp = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                device=device_id,
                top_k=None  # Return all class scores
            )

            self._pipelines[model_name] = nlp
            self._initialized_models.add(model_name)
            logger.info(f"Model {model_name} loaded successfully")

            return nlp

        except ImportError as e:
            logger.error(f"Failed to import transformers: {e}")
            logger.info("Install with: pip install transformers torch")
            raise
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

    def analyze_sentiment(self, text: str, model: str = FinBERTModel.SENTIMENT.value) -> SentimentResult:
        """
        Analyze sentiment of text using FinBERT-Sentiment.

        Args:
            text: Text to analyze
            model: Model to use (default: yiyanghkust/finbert-tone)

        Returns:
            SentimentResult with positive/negative/neutral classification
        """
        try:
            nlp = self._load_model(model)
            text = text[:512]  # Truncate to model max length

            results = nlp(text)[0]

            # Parse results
            scores = {r['label'].lower(): r['score'] for r in results}
            top_result = max(results, key=lambda x: x['score'])

            return SentimentResult(
                text=text[:100] + "..." if len(text) > 100 else text,
                sentiment=top_result['label'].lower(),
                confidence=top_result['score'],
                scores=scores
            )

        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return SentimentResult(
                text=text[:100] if text else "",
                sentiment='neutral',
                confidence=0.0,
                scores={'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}
            )

    def analyze_esg(self, text: str) -> ESGResult:
        """
        Classify text by ESG category using FinBERT-ESG.

        ESG Categories:
        - Environmental: Climate, pollution, sustainability
        - Social: Community, employees, human rights
        - Governance: Board, ethics, transparency
        - None: Not ESG-related

        Args:
            text: Text to classify

        Returns:
            ESGResult with category classification
        """
        try:
            nlp = self._load_model(FinBERTModel.ESG.value)
            text = text[:512]

            results = nlp(text)[0]

            # Parse results
            scores = {r['label']: r['score'] for r in results}
            top_result = max(results, key=lambda x: x['score'])

            return ESGResult(
                text=text[:100] + "..." if len(text) > 100 else text,
                category=top_result['label'],
                confidence=top_result['score'],
                scores=scores
            )

        except Exception as e:
            logger.warning(f"ESG analysis failed: {e}")
            return ESGResult(
                text=text[:100] if text else "",
                category='None',
                confidence=0.0,
                scores={'Environmental': 0.25, 'Social': 0.25, 'Governance': 0.25, 'None': 0.25}
            )

    def analyze_fls(self, text: str) -> FLSResult:
        """
        Classify text as Forward-Looking Statement using FinBERT-FLS.

        FLS Types:
        - Specific_FLS: Contains specific forward-looking information
        - Non-specific_FLS: General forward-looking statement
        - Not_FLS: Historical or factual statement

        Args:
            text: Text to classify

        Returns:
            FLSResult with FLS classification
        """
        try:
            nlp = self._load_model(FinBERTModel.FLS.value)
            text = text[:512]

            results = nlp(text)[0]

            # Parse results
            scores = {r['label']: r['score'] for r in results}
            top_result = max(results, key=lambda x: x['score'])

            fls_type = top_result['label']
            is_forward_looking = fls_type in ['Specific_FLS', 'Non-specific_FLS']

            return FLSResult(
                text=text[:100] + "..." if len(text) > 100 else text,
                fls_type=fls_type,
                is_forward_looking=is_forward_looking,
                confidence=top_result['score'],
                scores=scores
            )

        except Exception as e:
            logger.warning(f"FLS analysis failed: {e}")
            return FLSResult(
                text=text[:100] if text else "",
                fls_type='Not_FLS',
                is_forward_looking=False,
                confidence=0.0,
                scores={'Specific_FLS': 0.33, 'Non-specific_FLS': 0.33, 'Not_FLS': 0.34}
            )

    def analyze_comprehensive(
        self,
        text: str,
        include_esg: bool = True,
        include_fls: bool = True
    ) -> ComprehensiveAnalysisResult:
        """
        Perform comprehensive analysis using all available models.

        Args:
            text: Text to analyze
            include_esg: Whether to include ESG classification
            include_fls: Whether to include FLS classification

        Returns:
            ComprehensiveAnalysisResult with all analyses
        """
        sentiment = self.analyze_sentiment(text)
        esg = self.analyze_esg(text) if include_esg else None
        fls = self.analyze_fls(text) if include_fls else None

        return ComprehensiveAnalysisResult(
            text=text[:100] + "..." if len(text) > 100 else text,
            sentiment=sentiment,
            esg=esg,
            fls=fls
        )

    def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded models"""
        return list(self._initialized_models)


class SentimentAnalyzer:
    """
    Main sentiment analyzer class for forex/financial news.

    Combines multiple FinBERT models to provide comprehensive analysis.
    """

    def __init__(self, device: str = "auto", enable_esg: bool = False, enable_fls: bool = True):
        """
        Initialize the sentiment analyzer.

        Args:
            device: Device to run models on ('cpu', 'cuda', 'auto')
            enable_esg: Whether to enable ESG classification (slower)
            enable_fls: Whether to enable FLS classification
        """
        self.device = device
        self.enable_esg = enable_esg
        self.enable_fls = enable_fls
        self._analyzer = MultiModelAnalyzer(device=device)
        self._initialized = False

    def _ensure_initialized(self):
        """Ensure at least the sentiment model is loaded"""
        if not self._initialized:
            # Pre-load sentiment model
            self._analyzer._load_model(FinBERTModel.SENTIMENT.value)
            self._initialized = True

    def analyze_text(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of a single text.

        Args:
            text: Text to analyze

        Returns:
            SentimentResult with sentiment classification
        """
        self._ensure_initialized()
        return self._analyzer.analyze_sentiment(text)

    def analyze_text_comprehensive(self, text: str) -> Dict:
        """
        Perform comprehensive analysis on a single text.

        Returns dict with sentiment, ESG, and FLS results.
        """
        self._ensure_initialized()

        result = self._analyzer.analyze_comprehensive(
            text,
            include_esg=self.enable_esg,
            include_fls=self.enable_fls
        )

        output = {
            'text': result.text,
            'sentiment': {
                'label': result.sentiment.sentiment,
                'confidence': result.sentiment.confidence,
                'scores': result.sentiment.scores
            }
        }

        if result.esg:
            output['esg'] = {
                'category': result.esg.category,
                'confidence': result.esg.confidence,
                'scores': result.esg.scores
            }

        if result.fls:
            output['fls'] = {
                'type': result.fls.fls_type,
                'is_forward_looking': result.fls.is_forward_looking,
                'confidence': result.fls.confidence,
                'scores': result.fls.scores
            }

        return output

    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """Analyze sentiment of multiple texts."""
        self._ensure_initialized()
        return [self._analyzer.analyze_sentiment(text) for text in texts]

    def analyze_news_items(self, news_items: List[Dict]) -> Dict:
        """
        Analyze sentiment of news items with comprehensive metrics.

        Args:
            news_items: List of news dicts with 'title' and 'summary' keys

        Returns:
            Aggregated analysis with sentiment, FLS, and trading signals
        """
        if not news_items:
            return {
                'overall_sentiment': 'neutral',
                'overall_score': 0.0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'forward_looking_count': 0,
                'analyzed_items': [],
                'recommendation': 'No news to analyze'
            }

        self._ensure_initialized()

        analyzed_items = []
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        sentiment_scores = {'positive': [], 'negative': [], 'neutral': []}
        forward_looking_count = 0
        esg_categories = {'Environmental': 0, 'Social': 0, 'Governance': 0, 'None': 0}

        for item in news_items:
            text = f"{item.get('title', '')} {item.get('summary', '')}"

            # Get comprehensive analysis
            comprehensive = self._analyzer.analyze_comprehensive(
                text,
                include_esg=self.enable_esg,
                include_fls=self.enable_fls
            )

            # Track sentiment
            sentiment = comprehensive.sentiment.sentiment
            sentiment_counts[sentiment] += 1
            sentiment_scores[sentiment].append(comprehensive.sentiment.confidence)

            # Track FLS
            if comprehensive.fls and comprehensive.fls.is_forward_looking:
                forward_looking_count += 1

            # Track ESG
            if comprehensive.esg:
                esg_categories[comprehensive.esg.category] += 1

            # Build analyzed item
            analyzed_item = {
                'title': item.get('title', ''),
                'source': item.get('source', ''),
                'sentiment': sentiment,
                'sentiment_confidence': comprehensive.sentiment.confidence,
                'sentiment_scores': comprehensive.sentiment.scores
            }

            if comprehensive.fls:
                analyzed_item['fls_type'] = comprehensive.fls.fls_type
                analyzed_item['is_forward_looking'] = comprehensive.fls.is_forward_looking

            if comprehensive.esg:
                analyzed_item['esg_category'] = comprehensive.esg.category

            analyzed_items.append(analyzed_item)

        # Calculate aggregates
        total = len(news_items)
        positive_ratio = sentiment_counts['positive'] / total
        negative_ratio = sentiment_counts['negative'] / total
        neutral_ratio = sentiment_counts['neutral'] / total

        avg_positive = np.mean(sentiment_scores['positive']) if sentiment_scores['positive'] else 0
        avg_negative = np.mean(sentiment_scores['negative']) if sentiment_scores['negative'] else 0

        # Weighted sentiment score (-1 to 1)
        overall_score = (positive_ratio * avg_positive) - (negative_ratio * avg_negative)

        # Determine overall sentiment
        if overall_score > 0.15:
            overall_sentiment = 'bullish'
        elif overall_score < -0.15:
            overall_sentiment = 'bearish'
        else:
            overall_sentiment = 'neutral'

        # Generate recommendation considering FLS
        fls_weight = forward_looking_count / total if total > 0 else 0
        recommendation = self._generate_recommendation(
            overall_sentiment, positive_ratio, negative_ratio, fls_weight
        )

        result = {
            'overall_sentiment': overall_sentiment,
            'overall_score': float(overall_score),
            'positive_count': sentiment_counts['positive'],
            'negative_count': sentiment_counts['negative'],
            'neutral_count': sentiment_counts['neutral'],
            'positive_ratio': float(positive_ratio),
            'negative_ratio': float(negative_ratio),
            'forward_looking_count': forward_looking_count,
            'forward_looking_ratio': float(fls_weight),
            'analyzed_items': analyzed_items,
            'recommendation': recommendation
        }

        if self.enable_esg:
            result['esg_breakdown'] = esg_categories

        return result

    def _generate_recommendation(
        self,
        sentiment: str,
        positive_ratio: float,
        negative_ratio: float,
        fls_weight: float
    ) -> str:
        """Generate trading recommendation based on analysis."""
        fls_note = ""
        if fls_weight > 0.5:
            fls_note = " High forward-looking content suggests potential market movement."
        elif fls_weight > 0.3:
            fls_note = " Some forward-looking statements detected."

        if sentiment == 'bullish':
            strength = "strongly" if positive_ratio > 0.6 else ""
            return f"News sentiment is {strength} bullish ({positive_ratio:.0%} positive). Consider long positions.{fls_note}"
        elif sentiment == 'bearish':
            strength = "strongly" if negative_ratio > 0.6 else ""
            return f"News sentiment is {strength} bearish ({negative_ratio:.0%} negative). Consider short positions or caution.{fls_note}"
        else:
            return f"News sentiment is mixed/neutral. No strong directional bias from news.{fls_note}"

    def get_sentiment_for_symbol(self, symbol: str, news_items: List[Dict]) -> Dict:
        """
        Get comprehensive sentiment analysis for a trading symbol.

        Args:
            symbol: Trading symbol (e.g., 'EURUSD=X')
            news_items: News items related to this symbol

        Returns:
            Complete analysis with trading signals
        """
        analysis = self.analyze_news_items(news_items)

        # Add symbol context
        analysis['symbol'] = symbol
        analysis['news_count'] = len(news_items)

        # Determine trading bias with confidence adjustment
        score = analysis['overall_score']
        fls_ratio = analysis.get('forward_looking_ratio', 0)

        # Boost confidence if many forward-looking statements (more predictive value)
        confidence_boost = 1.0 + (fls_ratio * 0.2)

        if analysis['overall_sentiment'] == 'bullish':
            analysis['trading_bias'] = 'BUY'
            if score * confidence_boost > 0.4:
                analysis['bias_strength'] = 'strong'
            elif score * confidence_boost > 0.2:
                analysis['bias_strength'] = 'moderate'
            else:
                analysis['bias_strength'] = 'weak'
        elif analysis['overall_sentiment'] == 'bearish':
            analysis['trading_bias'] = 'SELL'
            if abs(score) * confidence_boost > 0.4:
                analysis['bias_strength'] = 'strong'
            elif abs(score) * confidence_boost > 0.2:
                analysis['bias_strength'] = 'moderate'
            else:
                analysis['bias_strength'] = 'weak'
        else:
            analysis['trading_bias'] = 'NEUTRAL'
            analysis['bias_strength'] = 'none'

        return analysis


# Singleton instances
_sentiment_analyzer_instance: Optional[SentimentAnalyzer] = None
_multi_model_analyzer_instance: Optional[MultiModelAnalyzer] = None


def get_sentiment_analyzer(
    enable_esg: bool = False,
    enable_fls: bool = True
) -> SentimentAnalyzer:
    """Get or create SentimentAnalyzer singleton"""
    global _sentiment_analyzer_instance
    if _sentiment_analyzer_instance is None:
        _sentiment_analyzer_instance = SentimentAnalyzer(
            enable_esg=enable_esg,
            enable_fls=enable_fls
        )
    return _sentiment_analyzer_instance


def get_multi_model_analyzer() -> MultiModelAnalyzer:
    """Get or create MultiModelAnalyzer singleton for direct model access"""
    global _multi_model_analyzer_instance
    if _multi_model_analyzer_instance is None:
        _multi_model_analyzer_instance = MultiModelAnalyzer()
    return _multi_model_analyzer_instance
