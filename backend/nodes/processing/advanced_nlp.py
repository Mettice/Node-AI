"""
Advanced NLP Node for NodeAI.

This node supports multiple NLP tasks with various providers:
- Summarization
- Named Entity Recognition (NER)
- Classification
- Extraction
- Sentiment Analysis
- Question Answering
- Translation

Supports multiple providers:
- HuggingFace (local/cloud)
- Azure Cognitive Services
- OpenAI
- Anthropic
- Custom API
"""

from typing import Any, Dict, List, Optional
import json
import hashlib

from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger
from backend.core.cache import get_cache
from backend.core.secret_resolver import resolve_api_key

logger = get_logger(__name__)

# Cache for NLP results
_nlp_cache = get_cache()


class AdvancedNLPNode(BaseNode):
    """
    Advanced NLP Node.
    
    Supports multiple NLP tasks with various providers.
    """

    node_type = "advanced_nlp"
    name = "Advanced NLP"
    description = "Perform advanced NLP tasks: summarization, NER, classification, extraction, sentiment, QA, translation"
    category = "processing"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the Advanced NLP node.
        
        Routes to appropriate task handler based on task type and provider.
        Supports batch processing, caching, and custom API providers.
        """
        node_id = config.get("_node_id", "advanced_nlp")
        task_type = config.get("task_type", "summarization")
        provider = config.get("provider", "huggingface")
        enable_cache = config.get("enable_cache", True)
        cache_ttl = config.get("cache_ttl_seconds", 3600)  # Default 1 hour
        
        # Get input text - support both single text and batch
        # Check multiple common output field names from different node types
        text_input = (
            inputs.get("text") or 
            inputs.get("input") or 
            inputs.get("content") or 
            inputs.get("output") or  # From CrewAI, LangChain agents, etc.
            inputs.get("report") or  # From CrewAI agents
            inputs.get("response") or  # From chat nodes
            ""
        )
        texts = inputs.get("texts") or inputs.get("batch") or []
        
        # Determine if batch processing
        is_batch = bool(texts) or (isinstance(text_input, list) and len(text_input) > 1)
        
        if is_batch:
            # Batch processing
            if texts:
                text_list = texts
            elif isinstance(text_input, list):
                text_list = text_input
            else:
                text_list = [text_input] if text_input else []
            
            if not text_list:
                raise ValueError("No texts provided for batch processing")
            
            return await self._process_batch(text_list, task_type, provider, config, node_id, enable_cache, cache_ttl)
        else:
            # Single text processing
            if not text_input:
                raise ValueError("No text provided in inputs")
            
            # Check cache if enabled
            if enable_cache:
                cache_key = self._generate_cache_key(task_type, provider, text_input, config)
                cached_result = _nlp_cache.get(cache_key)
                if cached_result is not None:
                    await self.stream_progress(node_id, 1.0, "Returning cached result")
                    return cached_result
            
            await self.stream_progress(node_id, 0.1, f"Starting {task_type} with {provider}...")
            
            # Check for fine-tuned model first
            use_finetuned = config.get("use_finetuned_model", False)
            finetuned_model_id = config.get("finetuned_model_id")
            if use_finetuned and finetuned_model_id:
                result = await self._process_finetuned_model(text_input, task_type, provider, finetuned_model_id, config, node_id)
            # Check for custom API provider
            elif provider == "custom":
                result = await self._process_custom_api(text_input, task_type, config, node_id)
            # Route to appropriate task handler
            elif task_type == "summarization":
                result = await self._summarize(text_input, inputs, config, node_id)
            elif task_type == "ner":
                result = await self._named_entity_recognition(text_input, inputs, config, node_id)
            elif task_type == "classification":
                result = await self._classify(text_input, inputs, config, node_id)
            elif task_type == "extraction":
                result = await self._extract(text_input, inputs, config, node_id)
            elif task_type == "sentiment":
                result = await self._sentiment_analysis(text_input, inputs, config, node_id)
            elif task_type == "qa":
                result = await self._question_answering(text_input, inputs, config, node_id)
            elif task_type == "translation":
                result = await self._translate(text_input, inputs, config, node_id)
            else:
                raise ValueError(f"Unsupported NLP task: {task_type}")
            
            # Cache result if enabled
            if enable_cache:
                _nlp_cache.set(cache_key, result, ttl_seconds=cache_ttl)
            
            return result

    def _generate_cache_key(
        self, task_type: str, provider: str, text: str, config: Dict[str, Any]
    ) -> str:
        """Generate a cache key for the NLP task."""
        # Create a hash of the task parameters
        key_data = {
            "task": task_type,
            "provider": provider,
            "text": text,
            "config": {k: v for k, v in config.items() if k not in ["_node_id", "_execution_id"]},
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return f"nlp:{hashlib.md5(key_str.encode()).hexdigest()}"

    def _calculate_openai_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for OpenAI API calls based on model pricing."""
        # Pricing per 1M tokens (as of 2025)
        pricing = {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-4": {"input": 30.00, "output": 60.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            "o1": {"input": 15.00, "output": 60.00},
            "o1-mini": {"input": 3.00, "output": 12.00},
        }
        # Default to gpt-4o-mini pricing if model not found
        model_pricing = pricing.get(model, pricing["gpt-4o-mini"])
        input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (output_tokens / 1_000_000) * model_pricing["output"]
        return round(input_cost + output_cost, 6)

    async def _process_batch(
        self,
        texts: List[str],
        task_type: str,
        provider: str,
        config: Dict[str, Any],
        node_id: str,
        enable_cache: bool,
        cache_ttl: int,
    ) -> Dict[str, Any]:
        """Process multiple texts in batch."""
        await self.stream_progress(node_id, 0.1, f"Processing batch of {len(texts)} texts...")
        
        results = []
        cached_count = 0
        
        for i, text in enumerate(texts):
            progress = 0.1 + (i / len(texts)) * 0.8
            await self.stream_progress(node_id, progress, f"Processing text {i+1}/{len(texts)}...")
            
            # Check cache for each text
            if enable_cache:
                cache_key = self._generate_cache_key(task_type, provider, text, config)
                cached_result = _nlp_cache.get(cache_key)
                if cached_result is not None:
                    results.append(cached_result)
                    cached_count += 1
                    continue
            
            # Process text
            inputs = {"text": text}
            if task_type == "summarization":
                result = await self._summarize(text, inputs, config, node_id)
            elif task_type == "ner":
                result = await self._named_entity_recognition(text, inputs, config, node_id)
            elif task_type == "classification":
                result = await self._classify(text, inputs, config, node_id)
            elif task_type == "extraction":
                result = await self._extract(text, inputs, config, node_id)
            elif task_type == "sentiment":
                result = await self._sentiment_analysis(text, inputs, config, node_id)
            elif task_type == "qa":
                result = await self._question_answering(text, inputs, config, node_id)
            elif task_type == "translation":
                result = await self._translate(text, inputs, config, node_id)
            else:
                raise ValueError(f"Unsupported NLP task: {task_type}")
            
            # Cache result
            if enable_cache:
                _nlp_cache.set(cache_key, result, ttl_seconds=cache_ttl)
            
            results.append(result)
        
        await self.stream_progress(node_id, 1.0, f"Batch complete! ({cached_count} from cache)")
        
        return {
            "output": results,
            "results": results,
            "count": len(results),
            "cached_count": cached_count,
            "task": task_type,
            "provider": provider,
            "batch_size": len(texts),
        }

    async def _summarize(
        self,
        text: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Summarize text using selected provider."""
        provider = config.get("provider", "huggingface")
        max_length = config.get("max_length", 150)
        min_length = config.get("min_length", 30)
        
        await self.stream_progress(node_id, 0.2, f"Summarizing with {provider}...")
        
        if provider == "huggingface":
            return await self._summarize_huggingface(text, config, node_id, max_length, min_length)
        elif provider == "openai":
            return await self._summarize_openai(text, config, node_id, max_length, min_length)
        elif provider == "anthropic":
            return await self._summarize_anthropic(text, config, node_id, max_length, min_length)
        elif provider == "azure":
            return await self._summarize_azure(text, config, node_id, max_length, min_length)
        elif provider == "custom":
            return await self._process_custom_api(text, "summarization", config, node_id)
        else:
            raise ValueError(f"Unsupported provider for summarization: {provider}")

    async def _named_entity_recognition(
        self,
        text: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Extract named entities from text."""
        provider = config.get("provider", "huggingface")
        
        await self.stream_progress(node_id, 0.2, f"Extracting entities with {provider}...")
        
        if provider == "huggingface":
            return await self._ner_huggingface(text, config, node_id)
        elif provider == "openai":
            return await self._ner_openai(text, config, node_id)
        elif provider == "anthropic":
            return await self._ner_anthropic(text, config, node_id)
        elif provider == "azure":
            return await self._ner_azure(text, config, node_id)
        elif provider == "custom":
            return await self._process_custom_api(text, "ner", config, node_id)
        else:
            raise ValueError(f"Unsupported provider for NER: {provider}")

    async def _classify(
        self,
        text: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Classify text into categories."""
        provider = config.get("provider", "huggingface")
        categories = config.get("categories", [])
        
        if not categories:
            raise ValueError("Categories are required for classification")
        
        await self.stream_progress(node_id, 0.2, f"Classifying with {provider}...")
        
        if provider == "huggingface":
            return await self._classify_huggingface(text, categories, config, node_id)
        elif provider == "openai":
            return await self._classify_openai(text, categories, config, node_id)
        elif provider == "anthropic":
            return await self._classify_anthropic(text, categories, config, node_id)
        elif provider == "azure":
            return await self._classify_azure(text, categories, config, node_id)
        elif provider == "custom":
            return await self._process_custom_api(text, "classification", config, node_id)
        else:
            raise ValueError(f"Unsupported provider for classification: {provider}")

    async def _extract(
        self,
        text: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Extract structured information from text."""
        provider = config.get("provider", "openai")
        extraction_schema = config.get("extraction_schema", {})
        
        if not extraction_schema:
            raise ValueError("Extraction schema is required")
        
        await self.stream_progress(node_id, 0.2, f"Extracting information with {provider}...")
        
        if provider == "openai":
            return await self._extract_openai(text, extraction_schema, config, node_id)
        elif provider == "anthropic":
            return await self._extract_anthropic(text, extraction_schema, config, node_id)
        elif provider == "huggingface":
            return await self._extract_huggingface(text, extraction_schema, config, node_id)
        elif provider == "custom":
            return await self._process_custom_api(text, "extraction", config, node_id)
        else:
            raise ValueError(f"Unsupported provider for extraction: {provider}")

    async def _sentiment_analysis(
        self,
        text: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Analyze sentiment of text."""
        provider = config.get("provider", "huggingface")
        
        await self.stream_progress(node_id, 0.2, f"Analyzing sentiment with {provider}...")
        
        if provider == "huggingface":
            return await self._sentiment_huggingface(text, config, node_id)
        elif provider == "openai":
            return await self._sentiment_openai(text, config, node_id)
        elif provider == "azure":
            return await self._sentiment_azure(text, config, node_id)
        elif provider == "custom":
            return await self._process_custom_api(text, "sentiment", config, node_id)
        else:
            raise ValueError(f"Unsupported provider for sentiment analysis: {provider}")

    async def _question_answering(
        self,
        text: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Answer questions based on text context."""
        provider = config.get("provider", "huggingface")
        question = config.get("question") or inputs.get("question", "")
        
        if not question:
            raise ValueError("Question is required for question answering")
        
        await self.stream_progress(node_id, 0.2, f"Answering question with {provider}...")
        
        if provider == "huggingface":
            return await self._qa_huggingface(text, question, config, node_id)
        elif provider == "openai":
            return await self._qa_openai(text, question, config, node_id)
        elif provider == "anthropic":
            return await self._qa_anthropic(text, question, config, node_id)
        elif provider == "custom":
            return await self._process_custom_api(text, "qa", config, node_id)
        else:
            raise ValueError(f"Unsupported provider for question answering: {provider}")

    async def _translate(
        self,
        text: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Translate text to target language."""
        provider = config.get("provider", "huggingface")
        target_language = config.get("target_language", "en")
        source_language = config.get("source_language", "auto")
        
        await self.stream_progress(node_id, 0.2, f"Translating with {provider}...")
        
        if provider == "huggingface":
            return await self._translate_huggingface(text, source_language, target_language, config, node_id)
        elif provider == "openai":
            return await self._translate_openai(text, source_language, target_language, config, node_id)
        elif provider == "azure":
            return await self._translate_azure(text, source_language, target_language, config, node_id)
        elif provider == "custom":
            return await self._process_custom_api(text, "translation", config, node_id)
        else:
            raise ValueError(f"Unsupported provider for translation: {provider}")

    # HuggingFace Implementations
    async def _summarize_huggingface(
        self, text: str, config: Dict[str, Any], node_id: str, max_length: int, min_length: int
    ) -> Dict[str, Any]:
        """Summarize using HuggingFace."""
        try:
            from transformers import pipeline
        except ImportError:
            raise ValueError("transformers not installed. Install with: pip install transformers torch")
        
        model_name = config.get("hf_model", "facebook/bart-large-cnn")
        
        await self.stream_progress(node_id, 0.4, f"Loading model {model_name}...")
        
        summarizer = pipeline("summarization", model=model_name)
        
        await self.stream_progress(node_id, 0.6, "Generating summary...")
        
        result = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        summary = result[0]["summary_text"]
        
        await self.stream_progress(node_id, 1.0, "Summary complete!")
        
        return {
            "output": summary,
            "summary": summary,
            "task": "summarization",
            "provider": "huggingface",
            "model": model_name,
            "original_length": len(text),
            "summary_length": len(summary),
        }

    async def _ner_huggingface(self, text: str, config: Dict[str, Any], node_id: str) -> Dict[str, Any]:
        """Extract named entities using HuggingFace."""
        try:
            from transformers import pipeline
        except ImportError:
            raise ValueError("transformers not installed. Install with: pip install transformers torch")
        
        model_name = config.get("hf_model", "dbmdz/bert-large-cased-finetuned-conll03-english")
        
        await self.stream_progress(node_id, 0.4, f"Loading model {model_name}...")
        
        ner = pipeline("ner", model=model_name, aggregation_strategy="simple")
        
        await self.stream_progress(node_id, 0.6, "Extracting entities...")
        
        entities = ner(text)
        
        # Group by entity type
        grouped = {}
        for entity in entities:
            entity_type = entity["entity_group"]
            if entity_type not in grouped:
                grouped[entity_type] = []
            grouped[entity_type].append({
                "text": entity["word"],
                "score": entity["score"],
                "start": entity.get("start", 0),
                "end": entity.get("end", 0),
            })
        
        await self.stream_progress(node_id, 1.0, f"Found {len(entities)} entities")
        
        return {
            "output": entities,
            "entities": entities,
            "grouped": grouped,
            "task": "ner",
            "provider": "huggingface",
            "model": model_name,
            "count": len(entities),
        }

    async def _classify_huggingface(
        self, text: str, categories: List[str], config: Dict[str, Any], node_id: str
    ) -> Dict[str, Any]:
        """Classify text using HuggingFace."""
        try:
            from transformers import pipeline
        except ImportError:
            raise ValueError("transformers not installed. Install with: pip install transformers torch")
        
        model_name = config.get("hf_model", "distilbert-base-uncased-finetuned-sst-2-english")
        
        await self.stream_progress(node_id, 0.4, f"Loading model {model_name}...")
        
        classifier = pipeline("text-classification", model=model_name)
        
        await self.stream_progress(node_id, 0.6, "Classifying text...")
        
        # If custom categories, use zero-shot classification
        if categories:
            from transformers import pipeline as pl
            classifier = pl("zero-shot-classification", model="facebook/bart-large-mnli")
            result = classifier(text, categories)
            label = result["labels"][0]
            score = result["scores"][0]
        else:
            result = classifier(text)[0]
            label = result["label"]
            score = result["score"]
        
        await self.stream_progress(node_id, 1.0, f"Classified as: {label}")
        
        return {
            "output": label,
            "label": label,
            "score": score,
            "categories": categories if categories else None,
            "task": "classification",
            "provider": "huggingface",
            "model": model_name,
        }

    async def _extract_huggingface(
        self, text: str, extraction_schema: Dict[str, Any], config: Dict[str, Any], node_id: str
    ) -> Dict[str, Any]:
        """Extract structured information using HuggingFace (via LLM)."""
        # HuggingFace doesn't have direct extraction, use OpenAI/Anthropic
        # Or use a fine-tuned model
        raise ValueError("Extraction with HuggingFace requires a fine-tuned model. Use OpenAI or Anthropic instead.")

    async def _sentiment_huggingface(self, text: str, config: Dict[str, Any], node_id: str) -> Dict[str, Any]:
        """Analyze sentiment using HuggingFace."""
        try:
            from transformers import pipeline
        except ImportError:
            raise ValueError("transformers not installed. Install with: pip install transformers torch")
        
        model_name = config.get("hf_model", "cardiffnlp/twitter-roberta-base-sentiment-latest")
        
        await self.stream_progress(node_id, 0.4, f"Loading model {model_name}...")
        
        sentiment = pipeline("sentiment-analysis", model=model_name)
        
        await self.stream_progress(node_id, 0.6, "Analyzing sentiment...")
        
        result = sentiment(text)[0]
        label = result["label"]
        score = result["score"]
        
        # Normalize label
        label_lower = label.lower()
        if "positive" in label_lower:
            sentiment_label = "positive"
        elif "negative" in label_lower:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        
        await self.stream_progress(node_id, 1.0, f"Sentiment: {sentiment_label} ({score:.2f})")
        
        return {
            "output": sentiment_label,
            "sentiment": sentiment_label,
            "label": label,
            "score": score,
            "task": "sentiment",
            "provider": "huggingface",
            "model": model_name,
        }

    async def _qa_huggingface(
        self, text: str, question: str, config: Dict[str, Any], node_id: str
    ) -> Dict[str, Any]:
        """Answer question using HuggingFace."""
        try:
            from transformers import pipeline
        except ImportError:
            raise ValueError("transformers not installed. Install with: pip install transformers torch")
        
        model_name = config.get("hf_model", "distilbert-base-cased-distilled-squad")
        
        await self.stream_progress(node_id, 0.4, f"Loading model {model_name}...")
        
        qa = pipeline("question-answering", model=model_name)
        
        await self.stream_progress(node_id, 0.6, "Answering question...")
        
        result = qa(question=question, context=text)
        
        await self.stream_progress(node_id, 1.0, "Answer generated!")
        
        return {
            "output": result["answer"],
            "answer": result["answer"],
            "score": result["score"],
            "start": result["start"],
            "end": result["end"],
            "question": question,
            "task": "qa",
            "provider": "huggingface",
            "model": model_name,
        }

    async def _translate_huggingface(
        self, text: str, source_lang: str, target_lang: str, config: Dict[str, Any], node_id: str
    ) -> Dict[str, Any]:
        """Translate text using HuggingFace."""
        try:
            from transformers import pipeline
        except ImportError:
            raise ValueError("transformers not installed. Install with: pip install transformers torch")
        
        # Map language codes to model names
        model_name = config.get("hf_model", "Helsinki-NLP/opus-mt-en-de")
        
        await self.stream_progress(node_id, 0.4, f"Loading model {model_name}...")
        
        translator = pipeline("translation", model=model_name)
        
        await self.stream_progress(node_id, 0.6, "Translating...")
        
        result = translator(text)[0]
        translated = result["translation_text"]
        
        await self.stream_progress(node_id, 1.0, "Translation complete!")
        
        return {
            "output": translated,
            "translated": translated,
            "source_language": source_lang,
            "target_language": target_lang,
            "task": "translation",
            "provider": "huggingface",
            "model": model_name,
        }

    # OpenAI Implementations
    async def _summarize_openai(
        self, text: str, config: Dict[str, Any], node_id: str, max_length: int, min_length: int
    ) -> Dict[str, Any]:
        """Summarize using OpenAI."""
        from openai import OpenAI
        from backend.config import settings

        user_id = config.get("_user_id")
        api_key = resolve_api_key(config, "openai_api_key", user_id=user_id) or settings.openai_api_key
        model = config.get("openai_model", "gpt-4o-mini")

        client = OpenAI(api_key=api_key)

        await self.stream_progress(node_id, 0.5, "Generating summary with OpenAI...")

        prompt = f"Summarize the following text in approximately {max_length} words:\n\n{text}"

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        summary = response.choices[0].message.content

        # Extract token usage and calculate cost
        usage = response.usage
        tokens_used = {
            "input": usage.prompt_tokens if usage else 0,
            "output": usage.completion_tokens if usage else 0,
            "total": usage.total_tokens if usage else 0,
        }
        cost = self._calculate_openai_cost(model, tokens_used["input"], tokens_used["output"])

        await self.stream_progress(node_id, 1.0, "Summary complete!")

        return {
            "output": summary,
            "summary": summary,
            "task": "summarization",
            "provider": "openai",
            "model": model,
            "original_length": len(text),
            "summary_length": len(summary),
            "tokens_used": tokens_used,
            "cost": cost,
        }

    async def _ner_openai(self, text: str, config: Dict[str, Any], node_id: str) -> Dict[str, Any]:
        """Extract named entities using OpenAI."""
        from openai import OpenAI
        from backend.config import settings

        user_id = config.get("_user_id")
        api_key = resolve_api_key(config, "openai_api_key", user_id=user_id) or settings.openai_api_key
        model = config.get("openai_model", "gpt-4o-mini")

        client = OpenAI(api_key=api_key)

        await self.stream_progress(node_id, 0.5, "Extracting entities with OpenAI...")

        prompt = f"""Extract all named entities from the following text. Return a JSON array with objects containing:
- "text": the entity text
- "type": the entity type (PERSON, ORGANIZATION, LOCATION, DATE, etc.)
- "start": character position where entity starts
- "end": character position where entity ends

Text: {text}

Return only valid JSON."""

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        entities = result.get("entities", [])

        # Group by type
        grouped = {}
        for entity in entities:
            entity_type = entity.get("type", "UNKNOWN")
            if entity_type not in grouped:
                grouped[entity_type] = []
            grouped[entity_type].append(entity)

        # Extract token usage and calculate cost
        usage = response.usage
        tokens_used = {
            "input": usage.prompt_tokens if usage else 0,
            "output": usage.completion_tokens if usage else 0,
            "total": usage.total_tokens if usage else 0,
        }
        cost = self._calculate_openai_cost(model, tokens_used["input"], tokens_used["output"])

        await self.stream_progress(node_id, 1.0, f"Found {len(entities)} entities")

        return {
            "output": entities,
            "entities": entities,
            "grouped": grouped,
            "task": "ner",
            "provider": "openai",
            "model": model,
            "count": len(entities),
            "tokens_used": tokens_used,
            "cost": cost,
        }

    async def _classify_openai(
        self, text: str, categories: List[str], config: Dict[str, Any], node_id: str
    ) -> Dict[str, Any]:
        """Classify text using OpenAI."""
        from openai import OpenAI
        from backend.config import settings
        
        user_id = config.get("_user_id")
        api_key = resolve_api_key(config, "openai_api_key", user_id=user_id) or settings.openai_api_key
        model = config.get("openai_model", "gpt-4o-mini")
        
        client = OpenAI(api_key=api_key)
        
        await self.stream_progress(node_id, 0.5, "Classifying with OpenAI...")
        
        categories_str = ", ".join(categories)
        prompt = f"""Classify the following text into one of these categories: {categories_str}

Text: {text}

Return a JSON object with:
- "label": the selected category
- "score": confidence score (0-1)
- "reasoning": brief explanation"""
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        
        result = json.loads(response.choices[0].message.content)

        # Extract token usage and calculate cost
        usage = response.usage
        tokens_used = {
            "input": usage.prompt_tokens if usage else 0,
            "output": usage.completion_tokens if usage else 0,
            "total": usage.total_tokens if usage else 0,
        }
        cost = self._calculate_openai_cost(model, tokens_used["input"], tokens_used["output"])

        await self.stream_progress(node_id, 1.0, f"Classified as: {result['label']}")

        return {
            "output": result["label"],
            "label": result["label"],
            "score": result.get("score", 0.0),
            "reasoning": result.get("reasoning", ""),
            "categories": categories,
            "task": "classification",
            "provider": "openai",
            "model": model,
            "tokens_used": tokens_used,
            "cost": cost,
        }

    async def _extract_openai(
        self, text: str, extraction_schema: Dict[str, Any], config: Dict[str, Any], node_id: str
    ) -> Dict[str, Any]:
        """Extract structured information using OpenAI."""
        from openai import OpenAI
        from backend.config import settings
        
        user_id = config.get("_user_id")
        api_key = resolve_api_key(config, "openai_api_key", user_id=user_id) or settings.openai_api_key
        model = config.get("openai_model", "gpt-4o-mini")
        
        client = OpenAI(api_key=api_key)
        
        await self.stream_progress(node_id, 0.5, "Extracting information with OpenAI...")
        
        schema_str = json.dumps(extraction_schema, indent=2)
        prompt = f"""Extract structured information from the following text according to this schema:

Schema:
{schema_str}

Text: {text}

Return a JSON object matching the schema."""
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        
        extracted = json.loads(response.choices[0].message.content)

        # Extract token usage and calculate cost
        usage = response.usage
        tokens_used = {
            "input": usage.prompt_tokens if usage else 0,
            "output": usage.completion_tokens if usage else 0,
            "total": usage.total_tokens if usage else 0,
        }
        cost = self._calculate_openai_cost(model, tokens_used["input"], tokens_used["output"])

        await self.stream_progress(node_id, 1.0, "Extraction complete!")

        return {
            "output": extracted,
            "extracted": extracted,
            "schema": extraction_schema,
            "task": "extraction",
            "provider": "openai",
            "model": model,
            "tokens_used": tokens_used,
            "cost": cost,
        }

    async def _sentiment_openai(self, text: str, config: Dict[str, Any], node_id: str) -> Dict[str, Any]:
        """Analyze sentiment using OpenAI."""
        from openai import OpenAI
        from backend.config import settings
        
        user_id = config.get("_user_id")
        api_key = resolve_api_key(config, "openai_api_key", user_id=user_id) or settings.openai_api_key
        model = config.get("openai_model", "gpt-4o-mini")
        
        client = OpenAI(api_key=api_key)
        
        await self.stream_progress(node_id, 0.5, "Analyzing sentiment with OpenAI...")
        
        prompt = f"""Analyze the sentiment of the following text. Return a JSON object with:
- "sentiment": one of "positive", "negative", or "neutral"
- "score": confidence score (0-1)
- "reasoning": brief explanation

Text: {text}"""
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        
        result = json.loads(response.choices[0].message.content)

        # Extract token usage and calculate cost
        usage = response.usage
        tokens_used = {
            "input": usage.prompt_tokens if usage else 0,
            "output": usage.completion_tokens if usage else 0,
            "total": usage.total_tokens if usage else 0,
        }
        cost = self._calculate_openai_cost(model, tokens_used["input"], tokens_used["output"])

        await self.stream_progress(node_id, 1.0, f"Sentiment: {result['sentiment']}")

        return {
            "output": result["sentiment"],
            "sentiment": result["sentiment"],
            "score": result.get("score", 0.0),
            "reasoning": result.get("reasoning", ""),
            "task": "sentiment",
            "provider": "openai",
            "model": model,
            "tokens_used": tokens_used,
            "cost": cost,
        }

    async def _qa_openai(
        self, text: str, question: str, config: Dict[str, Any], node_id: str
    ) -> Dict[str, Any]:
        """Answer question using OpenAI."""
        from openai import OpenAI
        from backend.config import settings
        
        user_id = config.get("_user_id")
        api_key = resolve_api_key(config, "openai_api_key", user_id=user_id) or settings.openai_api_key
        model = config.get("openai_model", "gpt-4o-mini")
        
        client = OpenAI(api_key=api_key)
        
        await self.stream_progress(node_id, 0.5, "Answering question with OpenAI...")
        
        prompt = f"""Answer the following question based on the provided context. If the answer cannot be found in the context, say "I don't know."

Context: {text}

Question: {question}

Answer:"""
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        
        answer = response.choices[0].message.content

        # Extract token usage and calculate cost
        usage = response.usage
        tokens_used = {
            "input": usage.prompt_tokens if usage else 0,
            "output": usage.completion_tokens if usage else 0,
            "total": usage.total_tokens if usage else 0,
        }
        cost = self._calculate_openai_cost(model, tokens_used["input"], tokens_used["output"])

        await self.stream_progress(node_id, 1.0, "Answer generated!")

        return {
            "output": answer,
            "answer": answer,
            "question": question,
            "task": "qa",
            "provider": "openai",
            "model": model,
            "tokens_used": tokens_used,
            "cost": cost,
        }

    async def _translate_openai(
        self, text: str, source_lang: str, target_lang: str, config: Dict[str, Any], node_id: str
    ) -> Dict[str, Any]:
        """Translate text using OpenAI."""
        from openai import OpenAI
        from backend.config import settings

        user_id = config.get("_user_id")
        api_key = resolve_api_key(config, "openai_api_key", user_id=user_id) or settings.openai_api_key
        model = config.get("openai_model", "gpt-4o-mini")

        client = OpenAI(api_key=api_key)

        await self.stream_progress(node_id, 0.5, "Translating with OpenAI...")

        lang_map = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
        }

        target_lang_name = lang_map.get(target_lang, target_lang)
        source_lang_name = lang_map.get(source_lang, source_lang) if source_lang != "auto" else "the detected language"

        prompt = f"Translate the following text from {source_lang_name} to {target_lang_name}:\n\n{text}"

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        translated = response.choices[0].message.content

        # Extract token usage and calculate cost
        usage = response.usage
        tokens_used = {
            "input": usage.prompt_tokens if usage else 0,
            "output": usage.completion_tokens if usage else 0,
            "total": usage.total_tokens if usage else 0,
        }
        cost = self._calculate_openai_cost(model, tokens_used["input"], tokens_used["output"])

        await self.stream_progress(node_id, 1.0, "Translation complete!")

        return {
            "output": translated,
            "translated": translated,
            "source_language": source_lang,
            "target_language": target_lang,
            "task": "translation",
            "provider": "openai",
            "model": model,
            "tokens_used": tokens_used,
            "cost": cost,
        }

    # Anthropic Implementations (similar to OpenAI)
    async def _summarize_anthropic(
        self, text: str, config: Dict[str, Any], node_id: str, max_length: int, min_length: int
    ) -> Dict[str, Any]:
        """Summarize using Anthropic."""
        try:
            import anthropic
        except ImportError:
            raise ValueError("anthropic not installed. Install with: pip install anthropic")
        
        from backend.config import settings
        
        api_key = resolve_api_key(config, "anthropic_api_key", user_id=user_id) or settings.anthropic_api_key
        model = config.get("anthropic_model", "claude-sonnet-4-5-20250929")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        await self.stream_progress(node_id, 0.5, "Generating summary with Anthropic...")
        
        prompt = f"Summarize the following text in approximately {max_length} words:\n\n{text}"
        
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        
        summary = message.content[0].text
        
        await self.stream_progress(node_id, 1.0, "Summary complete!")
        
        return {
            "output": summary,
            "summary": summary,
            "task": "summarization",
            "provider": "anthropic",
            "model": model,
            "original_length": len(text),
            "summary_length": len(summary),
        }

    async def _ner_anthropic(self, text: str, config: Dict[str, Any], node_id: str) -> Dict[str, Any]:
        """Extract named entities using Anthropic."""
        try:
            import anthropic
        except ImportError:
            raise ValueError("anthropic not installed. Install with: pip install anthropic")
        
        from backend.config import settings
        
        api_key = resolve_api_key(config, "anthropic_api_key", user_id=user_id) or settings.anthropic_api_key
        model = config.get("anthropic_model", "claude-sonnet-4-5-20250929")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        await self.stream_progress(node_id, 0.5, "Extracting entities with Anthropic...")
        
        prompt = f"""Extract all named entities from the following text. Return a JSON array with objects containing:
- "text": the entity text
- "type": the entity type (PERSON, ORGANIZATION, LOCATION, DATE, etc.)
- "start": character position where entity starts
- "end": character position where entity ends

Text: {text}

Return only valid JSON."""
        
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        
        result = json.loads(message.content[0].text)
        entities = result.get("entities", [])
        
        # Group by type
        grouped = {}
        for entity in entities:
            entity_type = entity.get("type", "UNKNOWN")
            if entity_type not in grouped:
                grouped[entity_type] = []
            grouped[entity_type].append(entity)
        
        await self.stream_progress(node_id, 1.0, f"Found {len(entities)} entities")
        
        return {
            "output": entities,
            "entities": entities,
            "grouped": grouped,
            "task": "ner",
            "provider": "anthropic",
            "model": model,
            "count": len(entities),
        }

    async def _classify_anthropic(
        self, text: str, categories: List[str], config: Dict[str, Any], node_id: str
    ) -> Dict[str, Any]:
        """Classify text using Anthropic."""
        try:
            import anthropic
        except ImportError:
            raise ValueError("anthropic not installed. Install with: pip install anthropic")
        
        from backend.config import settings
        
        api_key = resolve_api_key(config, "anthropic_api_key", user_id=user_id) or settings.anthropic_api_key
        model = config.get("anthropic_model", "claude-sonnet-4-5-20250929")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        await self.stream_progress(node_id, 0.5, "Classifying with Anthropic...")
        
        categories_str = ", ".join(categories)
        prompt = f"""Classify the following text into one of these categories: {categories_str}

Text: {text}

Return a JSON object with:
- "label": the selected category
- "score": confidence score (0-1)
- "reasoning": brief explanation"""
        
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        
        result = json.loads(message.content[0].text)
        
        await self.stream_progress(node_id, 1.0, f"Classified as: {result['label']}")
        
        return {
            "output": result["label"],
            "label": result["label"],
            "score": result.get("score", 0.0),
            "reasoning": result.get("reasoning", ""),
            "categories": categories,
            "task": "classification",
            "provider": "anthropic",
            "model": model,
        }

    async def _extract_anthropic(
        self, text: str, extraction_schema: Dict[str, Any], config: Dict[str, Any], node_id: str
    ) -> Dict[str, Any]:
        """Extract structured information using Anthropic."""
        try:
            import anthropic
        except ImportError:
            raise ValueError("anthropic not installed. Install with: pip install anthropic")
        
        from backend.config import settings
        
        api_key = resolve_api_key(config, "anthropic_api_key", user_id=user_id) or settings.anthropic_api_key
        model = config.get("anthropic_model", "claude-sonnet-4-5-20250929")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        await self.stream_progress(node_id, 0.5, "Extracting information with Anthropic...")
        
        schema_str = json.dumps(extraction_schema, indent=2)
        prompt = f"""Extract structured information from the following text according to this schema:

Schema:
{schema_str}

Text: {text}

Return a JSON object matching the schema."""
        
        message = client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        
        extracted = json.loads(message.content[0].text)
        
        await self.stream_progress(node_id, 1.0, "Extraction complete!")
        
        return {
            "output": extracted,
            "extracted": extracted,
            "schema": extraction_schema,
            "task": "extraction",
            "provider": "anthropic",
            "model": model,
        }

    async def _qa_anthropic(
        self, text: str, question: str, config: Dict[str, Any], node_id: str
    ) -> Dict[str, Any]:
        """Answer question using Anthropic."""
        try:
            import anthropic
        except ImportError:
            raise ValueError("anthropic not installed. Install with: pip install anthropic")
        
        from backend.config import settings
        
        api_key = resolve_api_key(config, "anthropic_api_key", user_id=user_id) or settings.anthropic_api_key
        model = config.get("anthropic_model", "claude-sonnet-4-5-20250929")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        await self.stream_progress(node_id, 0.5, "Answering question with Anthropic...")
        
        prompt = f"""Answer the following question based on the provided context. If the answer cannot be found in the context, say "I don't know."

Context: {text}

Question: {question}

Answer:"""
        
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        
        answer = message.content[0].text
        
        await self.stream_progress(node_id, 1.0, "Answer generated!")
        
        return {
            "output": answer,
            "answer": answer,
            "question": question,
            "task": "qa",
            "provider": "anthropic",
            "model": model,
        }

    # Azure Cognitive Services Implementations
    async def _summarize_azure(
        self, text: str, config: Dict[str, Any], node_id: str, max_length: int, min_length: int
    ) -> Dict[str, Any]:
        """Summarize using Azure Cognitive Services (via Azure OpenAI or Text Analytics)."""
        # Azure Text Analytics doesn't have summarization, use Azure OpenAI instead
        from openai import OpenAI
        from backend.config import settings
        
        api_key = resolve_api_key(config, "azure_openai_api_key", user_id=user_id) or config.get("azure_api_key")
        endpoint = config.get("azure_openai_endpoint") or config.get("azure_endpoint")
        deployment_name = config.get("azure_openai_deployment") or config.get("azure_deployment", "gpt-4o-mini")
        api_version = config.get("azure_openai_api_version", "2024-02-15-preview")
        
        if not api_key or not endpoint or not deployment_name:
            raise ValueError(
                "Azure OpenAI configuration required for summarization. "
                "Set azure_openai_api_key, azure_openai_endpoint, and azure_openai_deployment."
            )
        
        client = OpenAI(
            api_key=api_key,
            base_url=f"{endpoint.rstrip('/')}/openai/deployments",
            default_headers={"api-key": api_key},
            default_query={"api-version": api_version},
        )
        
        await self.stream_progress(node_id, 0.5, "Generating summary with Azure OpenAI...")
        
        prompt = f"Summarize the following text in approximately {max_length} words:\n\n{text}"
        
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        
        summary = response.choices[0].message.content
        
        await self.stream_progress(node_id, 1.0, "Summary complete!")
        
        return {
            "output": summary,
            "summary": summary,
            "task": "summarization",
            "provider": "azure",
            "model": deployment_name,
            "original_length": len(text),
            "summary_length": len(summary),
        }

    async def _ner_azure(self, text: str, config: Dict[str, Any], node_id: str) -> Dict[str, Any]:
        """Extract named entities using Azure Cognitive Services Text Analytics."""
        try:
            from azure.ai.textanalytics import TextAnalyticsClient
            from azure.core.credentials import AzureKeyCredential
        except ImportError:
            raise ValueError("azure-ai-textanalytics not installed. Install with: pip install azure-ai-textanalytics")
        
        endpoint = config.get("azure_text_analytics_endpoint") or config.get("azure_endpoint")
        api_key = config.get("azure_text_analytics_api_key") or config.get("azure_api_key")
        
        if not endpoint or not api_key:
            raise ValueError(
                "Azure Text Analytics configuration required. "
                "Set azure_text_analytics_endpoint and azure_text_analytics_api_key."
            )
        
        client = TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))
        
        await self.stream_progress(node_id, 0.5, "Extracting entities with Azure Text Analytics...")
        
        # Azure Text Analytics recognizes entities
        response = client.recognize_entities([text])
        result = [doc for doc in response if not doc.is_error][0]
        
        entities = []
        for entity in result.entities:
            entities.append({
                "text": entity.text,
                "type": entity.category,
                "subcategory": entity.subcategory,
                "confidence_score": entity.confidence_score,
                "offset": entity.offset,
                "length": entity.length,
            })
        
        # Group by type
        grouped = {}
        for entity in entities:
            entity_type = entity["type"]
            if entity_type not in grouped:
                grouped[entity_type] = []
            grouped[entity_type].append(entity)
        
        await self.stream_progress(node_id, 1.0, f"Found {len(entities)} entities")
        
        return {
            "output": entities,
            "entities": entities,
            "grouped": grouped,
            "task": "ner",
            "provider": "azure",
            "count": len(entities),
        }

    async def _classify_azure(
        self, text: str, categories: List[str], config: Dict[str, Any], node_id: str
    ) -> Dict[str, Any]:
        """Classify text using Azure Cognitive Services (via Azure OpenAI)."""
        # Azure Text Analytics doesn't have custom classification, use Azure OpenAI
        from openai import OpenAI
        from backend.config import settings
        
        api_key = resolve_api_key(config, "azure_openai_api_key", user_id=user_id) or config.get("azure_api_key")
        endpoint = config.get("azure_openai_endpoint") or config.get("azure_endpoint")
        deployment_name = config.get("azure_openai_deployment") or config.get("azure_deployment", "gpt-4o-mini")
        api_version = config.get("azure_openai_api_version", "2024-02-15-preview")
        
        if not api_key or not endpoint or not deployment_name:
            raise ValueError(
                "Azure OpenAI configuration required for classification. "
                "Set azure_openai_api_key, azure_openai_endpoint, and azure_openai_deployment."
            )
        
        client = OpenAI(
            api_key=api_key,
            base_url=f"{endpoint.rstrip('/')}/openai/deployments",
            default_headers={"api-key": api_key},
            default_query={"api-version": api_version},
        )
        
        await self.stream_progress(node_id, 0.5, "Classifying with Azure OpenAI...")
        
        categories_str = ", ".join(categories)
        prompt = f"""Classify the following text into one of these categories: {categories_str}

Text: {text}

Return a JSON object with:
- "label": the selected category
- "score": confidence score (0-1)
- "reasoning": brief explanation"""
        
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        
        result = json.loads(response.choices[0].message.content)
        
        await self.stream_progress(node_id, 1.0, f"Classified as: {result['label']}")
        
        return {
            "output": result["label"],
            "label": result["label"],
            "score": result.get("score", 0.0),
            "reasoning": result.get("reasoning", ""),
            "categories": categories,
            "task": "classification",
            "provider": "azure",
            "model": deployment_name,
        }

    async def _sentiment_azure(self, text: str, config: Dict[str, Any], node_id: str) -> Dict[str, Any]:
        """Analyze sentiment using Azure Cognitive Services Text Analytics."""
        try:
            from azure.ai.textanalytics import TextAnalyticsClient
            from azure.core.credentials import AzureKeyCredential
        except ImportError:
            raise ValueError("azure-ai-textanalytics not installed. Install with: pip install azure-ai-textanalytics")
        
        endpoint = config.get("azure_text_analytics_endpoint") or config.get("azure_endpoint")
        api_key = config.get("azure_text_analytics_api_key") or config.get("azure_api_key")
        
        if not endpoint or not api_key:
            raise ValueError(
                "Azure Text Analytics configuration required. "
                "Set azure_text_analytics_endpoint and azure_text_analytics_api_key."
            )
        
        client = TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))
        
        await self.stream_progress(node_id, 0.5, "Analyzing sentiment with Azure Text Analytics...")
        
        # Azure Text Analytics sentiment analysis
        response = client.analyze_sentiment([text], show_opinion_mining=True)
        result = [doc for doc in response if not doc.is_error][0]
        
        # Map Azure sentiment to our format
        sentiment_map = {
            "positive": "positive",
            "negative": "negative",
            "neutral": "neutral",
            "mixed": "neutral",
        }
        sentiment_label = sentiment_map.get(result.sentiment.lower(), "neutral")
        
        await self.stream_progress(node_id, 1.0, f"Sentiment: {sentiment_label} ({result.confidence_scores.positive:.2f})")
        
        return {
            "output": sentiment_label,
            "sentiment": sentiment_label,
            "label": result.sentiment,
            "score": result.confidence_scores.positive if sentiment_label == "positive" else (
                result.confidence_scores.negative if sentiment_label == "negative" else result.confidence_scores.neutral
            ),
            "confidence_scores": {
                "positive": result.confidence_scores.positive,
                "negative": result.confidence_scores.negative,
                "neutral": result.confidence_scores.neutral,
            },
            "task": "sentiment",
            "provider": "azure",
        }

    async def _translate_azure(
        self, text: str, source_lang: str, target_lang: str, config: Dict[str, Any], node_id: str
    ) -> Dict[str, Any]:
        """Translate text using Azure Translator."""
        try:
            from azure.ai.translation.text import TextTranslationClient, TranslatorCredential
            from azure.core.credentials import AzureKeyCredential
        except ImportError:
            raise ValueError("azure-ai-translation-text not installed. Install with: pip install azure-ai-translation-text")
        
        endpoint = config.get("azure_translator_endpoint") or config.get("azure_endpoint")
        api_key = config.get("azure_translator_api_key") or config.get("azure_api_key")
        region = config.get("azure_translator_region", "global")
        
        if not endpoint or not api_key:
            raise ValueError(
                "Azure Translator configuration required. "
                "Set azure_translator_endpoint and azure_translator_api_key."
            )
        
        credential = TranslatorCredential(api_key, region)
        client = TextTranslationClient(endpoint=endpoint, credential=credential)
        
        await self.stream_progress(node_id, 0.5, "Translating with Azure Translator...")
        
        # Handle auto-detect
        from_lang = None if source_lang == "auto" else source_lang
        
        response = client.translate(
            content=[text],
            to=[target_lang],
            from_language=from_lang,
        )
        
        translated = response[0].translations[0].text
        detected_language = response[0].detected_language.language if from_lang is None else source_lang
        
        await self.stream_progress(node_id, 1.0, "Translation complete!")
        
        return {
            "output": translated,
            "translated": translated,
            "source_language": detected_language,
            "target_language": target_lang,
            "task": "translation",
            "provider": "azure",
        }

    async def _process_custom_api(
        self, text: str, task_type: str, config: Dict[str, Any], node_id: str
    ) -> Dict[str, Any]:
        """Process NLP task using a custom API endpoint."""
        import httpx
        
        api_url = config.get("custom_api_url")
        api_key = config.get("custom_api_key", "")
        method = config.get("custom_api_method", "POST")
        
        if not api_url:
            raise ValueError("Custom API URL is required for custom provider")
        
        await self.stream_progress(node_id, 0.3, f"Calling custom API: {api_url}...")
        
        headers = {
            "Content-Type": "application/json",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "text": text,
            "task": task_type,
            "config": {k: v for k, v in config.items() if not k.startswith("_") and k not in ["custom_api_url", "custom_api_key", "custom_api_method"]},
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "POST":
                    response = await client.post(api_url, json=payload, headers=headers)
                else:
                    # GET request - add params to URL
                    response = await client.get(api_url, params=payload, headers=headers)
                
                response.raise_for_status()
                result = response.json()
                
                await self.stream_progress(node_id, 1.0, "Custom API call complete!")
                
                return {
                    "output": result.get("output") or result.get("result") or result,
                    "task": task_type,
                    "provider": "custom",
                    "api_url": api_url,
                    "raw_response": result,
                }
        except httpx.HTTPError as e:
            raise ValueError(f"Custom API call failed: {str(e)}")

    async def _process_finetuned_model(
        self, text: str, task_type: str, provider: str, model_id: str, config: Dict[str, Any], node_id: str
    ) -> Dict[str, Any]:
        """Process NLP task using a fine-tuned model from the registry."""
        try:
            import httpx
            import os
            
            api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
            url = f"{api_base}/api/v1/models/{model_id}"
            
            await self.stream_progress(node_id, 0.2, f"Fetching fine-tuned model {model_id}...")
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    model_data = response.json()
                    # Verify provider matches
                    if model_data.get("provider") == provider and model_data.get("status") == "ready":
                        model_endpoint = model_data.get("endpoint") or model_data.get("api_url")
                        model_api_key = model_data.get("api_key") or config.get("custom_api_key")
                        
                        if not model_endpoint:
                            raise ValueError(f"Fine-tuned model {model_id} does not have an endpoint configured")
                        
                        await self.stream_progress(node_id, 0.4, f"Using fine-tuned model endpoint: {model_endpoint}")
                        
                        # Use custom API processing with fine-tuned model endpoint
                        custom_config = config.copy()
                        custom_config["custom_api_url"] = model_endpoint
                        if model_api_key:
                            custom_config["custom_api_key"] = model_api_key
                        
                        result = await self._process_custom_api(text, task_type, custom_config, node_id)
                        result["finetuned_model_id"] = model_id
                        result["is_finetuned"] = True
                        
                        # Record model usage
                        try:
                            usage_url = f"{api_base}/api/v1/models/{model_id}/usage"
                            await client.post(
                                usage_url,
                                json={
                                    "node_type": "advanced_nlp",
                                    "execution_id": config.get("_execution_id"),
                                    "task": task_type,
                                },
                                timeout=2.0,
                            )
                        except Exception:
                            pass  # Non-critical
                        
                        return result
                    else:
                        raise ValueError(f"Fine-tuned model {model_id} is not ready or provider mismatch")
                else:
                    raise ValueError(f"Fine-tuned model {model_id} not found")
        except Exception as e:
            logger.error(f"Fine-tuned model processing error: {e}")
            raise ValueError(f"Failed to use fine-tuned model: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for Advanced NLP node configuration."""
        return {
            "type": "object",
            "properties": {
                "task_type": {
                    "type": "string",
                    "title": "NLP Task",
                    "description": "Select the NLP task to perform",
                    "enum": [
                        "summarization",
                        "ner",
                        "classification",
                        "extraction",
                        "sentiment",
                        "qa",
                        "translation",
                    ],
                    "default": "summarization",
                },
                "provider": {
                    "type": "string",
                    "title": "Provider",
                    "description": "Select the provider for the NLP task",
                    "enum": ["huggingface", "openai", "anthropic", "azure", "custom"],
                    "default": "huggingface",
                },
                # HuggingFace config
                "hf_model": {
                    "type": "string",
                    "title": "HuggingFace Model",
                    "description": "HuggingFace model name (optional, uses default for task)",
                    "default": "",
                },
                # OpenAI config
                "openai_api_key": {
                    "type": "string",
                    "title": "OpenAI API Key",
                    "description": "OpenAI API key (optional, uses environment variable if not provided)",
                    "default": "",
                },
                "openai_model": {
                    "type": "string",
                    "title": "OpenAI Model",
                    "description": "OpenAI model to use",
                    "default": "gpt-4o-mini",
                },
                # Anthropic config
                "anthropic_api_key": {
                    "type": "string",
                    "title": "Anthropic API Key",
                    "description": "Anthropic API key (optional, uses environment variable if not provided)",
                    "default": "",
                },
                "anthropic_model": {
                    "type": "string",
                    "title": "Anthropic Model",
                    "description": "Anthropic model to use",
                    "default": "claude-sonnet-4-5-20250929",
                },
                # Summarization config
                "max_length": {
                    "type": "integer",
                    "title": "Max Length",
                    "description": "Maximum length for summary (words or tokens)",
                    "default": 150,
                    "minimum": 10,
                    "maximum": 1000,
                },
                "min_length": {
                    "type": "integer",
                    "title": "Min Length",
                    "description": "Minimum length for summary (words or tokens)",
                    "default": 30,
                    "minimum": 5,
                    "maximum": 500,
                },
                # Classification config
                "categories": {
                    "type": "array",
                    "title": "Categories",
                    "description": "List of categories for classification (required for classification task)",
                    "items": {"type": "string"},
                    "default": [],
                },
                # Extraction config
                "extraction_schema": {
                    "type": "object",
                    "title": "Extraction Schema",
                    "description": "JSON schema defining what to extract (required for extraction task)",
                    "default": {},
                },
                # Question Answering config
                "question": {
                    "type": "string",
                    "title": "Question",
                    "description": "Question to answer (required for QA task)",
                    "default": "",
                },
                # Translation config
                "source_language": {
                    "type": "string",
                    "title": "Source Language",
                    "description": "Source language code (e.g., 'en', 'es', 'fr') or 'auto' for auto-detect",
                    "default": "auto",
                },
                "target_language": {
                    "type": "string",
                    "title": "Target Language",
                    "description": "Target language code (e.g., 'en', 'es', 'fr')",
                    "default": "en",
                },
                # Batch processing
                "enable_batch": {
                    "type": "boolean",
                    "title": "Enable Batch Processing",
                    "description": "Process multiple texts at once (provide 'texts' or 'batch' in inputs)",
                    "default": False,
                },
                # Caching
                "enable_cache": {
                    "type": "boolean",
                    "title": "Enable Result Caching",
                    "description": "Cache results for repeated queries",
                    "default": True,
                },
                "cache_ttl_seconds": {
                    "type": "integer",
                    "title": "Cache TTL (seconds)",
                    "description": "Time to live for cached results",
                    "default": 3600,
                    "minimum": 0,
                    "maximum": 86400,
                },
                # Custom API provider
                "custom_api_url": {
                    "type": "string",
                    "title": "Custom API URL",
                    "description": "Custom API endpoint URL (for custom provider)",
                    "default": "",
                },
                "custom_api_key": {
                    "type": "string",
                    "title": "Custom API Key",
                    "description": "API key for custom provider",
                    "default": "",
                },
                "custom_api_method": {
                    "type": "string",
                    "title": "HTTP Method",
                    "description": "HTTP method for custom API",
                    "enum": ["POST", "GET"],
                    "default": "POST",
                },
                # Fine-tuned model support
                "use_finetuned_model": {
                    "type": "boolean",
                    "title": "Use Fine-Tuned Model",
                    "description": "Use a custom fine-tuned model",
                    "default": False,
                },
                "finetuned_model_id": {
                    "type": "string",
                    "title": "Fine-Tuned Model ID",
                    "description": "ID of the fine-tuned model from registry",
                    "default": "",
                },
                # Azure Text Analytics config
                "azure_text_analytics_endpoint": {
                    "type": "string",
                    "title": "Azure Text Analytics Endpoint",
                    "description": "Azure Text Analytics endpoint URL",
                    "default": "",
                },
                "azure_text_analytics_api_key": {
                    "type": "string",
                    "title": "Azure Text Analytics API Key",
                    "description": "Azure Text Analytics API key",
                    "default": "",
                },
                # Azure Translator config
                "azure_translator_endpoint": {
                    "type": "string",
                    "title": "Azure Translator Endpoint",
                    "description": "Azure Translator endpoint URL",
                    "default": "",
                },
                "azure_translator_api_key": {
                    "type": "string",
                    "title": "Azure Translator API Key",
                    "description": "Azure Translator API key",
                    "default": "",
                },
                "azure_translator_region": {
                    "type": "string",
                    "title": "Azure Translator Region",
                    "description": "Azure Translator region (e.g., 'global', 'eastus')",
                    "default": "global",
                },
            },
            "required": ["task_type", "provider"],
        }


# Register the node
NodeRegistry.register(
    AdvancedNLPNode.node_type,
    AdvancedNLPNode,
    AdvancedNLPNode().get_metadata(),
)

