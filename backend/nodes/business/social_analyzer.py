"""
Social Media Analyzer Node - Pulls posts and performs sentiment analysis

This node analyzes social media content for:
- Sentiment analysis (positive/negative/neutral)
- Brand mention tracking
- Engagement metrics analysis
- Trend identification
- Competitor analysis
"""

from datetime import datetime
from typing import Any, Dict, List
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeExecutionError, NodeValidationError
from backend.core.node_registry import NodeRegistry


class SocialAnalyzerNode(BaseNode, LLMConfigMixin):
    node_type = "social_analyzer"
    name = "Social Media Analyzer"
    description = "Analyzes social media posts for sentiment and brand insights"
    category = "business"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute social media analysis"""
        try:
            await self.stream_progress("social_analyzer", 0.2, "Fetching social media data...")

            # Get inputs - accept multiple field names for flexibility
            social_data_raw = (
                inputs.get("social_data") or 
                inputs.get("data") or 
                inputs.get("text") or 
                inputs.get("content") or 
                inputs.get("output") or
                []
            )
            
            # Parse if it's a string (JSON)
            if isinstance(social_data_raw, str):
                try:
                    import json
                    social_data = json.loads(social_data_raw)
                    if not isinstance(social_data, list):
                        social_data = [social_data]
                except json.JSONDecodeError:
                    social_data = []
            else:
                social_data = social_data_raw if isinstance(social_data_raw, list) else [social_data_raw] if social_data_raw else []
            
            platforms = config.get("platforms", ["twitter", "linkedin"])
            analysis_types = config.get("analysis_types", ["sentiment", "engagement"])

            if not social_data:
                raise NodeValidationError("Social media data is required. Connect a text_input, file_loader, or data_loader node.")

            await self.stream_progress("social_analyzer", 0.6, "Analyzing sentiment and engagement...")

            # Try to use LLM if available
            use_llm = False
            llm_config = None
            
            try:
                llm_config = self._resolve_llm_config(config)
                if llm_config.get("api_key"):
                    use_llm = True
            except Exception:
                use_llm = False

            # Perform sentiment analysis
            if use_llm and llm_config:
                try:
                    sentiment_analysis = await self._analyze_llm_sentiment(social_data, llm_config)
                except Exception as e:
                    await self.stream_log("social_analyzer", f"LLM sentiment analysis failed, using pattern matching: {e}", "warning")
                    sentiment_analysis = self._analyze_sentiment(social_data)
            else:
                sentiment_analysis = self._analyze_sentiment(social_data)
            
            # Analyze engagement metrics
            engagement_analysis = self._analyze_engagement(social_data)

            result = {
                "sentiment_analysis": sentiment_analysis,
                "engagement_analysis": engagement_analysis,
                "summary": {
                    "total_posts": len(social_data),
                    "overall_sentiment": sentiment_analysis.get("overall_sentiment", "neutral"),
                    "avg_engagement": engagement_analysis.get("average_engagement", 0)
                },
                "metadata": {
                    "platforms": platforms,
                    "analyzed_at": datetime.now().isoformat()
                }
            }

            await self.stream_progress("social_analyzer", 1.0, "Social analysis complete!")
            return result

        except Exception as e:
            raise NodeExecutionError(f"Social media analysis failed: {str(e)}")

    def _analyze_sentiment(self, posts: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment of social media posts"""
        
        sentiments = {"positive": 0, "negative": 0, "neutral": 0}
        
        for post in posts:
            content = post.get("content", "")
            # Simple keyword-based sentiment (would use ML models in production)
            sentiment = self._classify_sentiment(content)
            sentiments[sentiment] += 1
        
        total = len(posts)
        if total > 0:
            sentiment_percentages = {k: (v/total)*100 for k, v in sentiments.items()}
        else:
            sentiment_percentages = {"positive": 0, "negative": 0, "neutral": 0}

        # Determine overall sentiment
        if sentiment_percentages["positive"] > 50:
            overall = "positive"
        elif sentiment_percentages["negative"] > 30:
            overall = "negative"  
        else:
            overall = "neutral"
        
        return {
            "sentiment_distribution": sentiment_percentages,
            "overall_sentiment": overall,
            "total_posts": total
        }

    def _classify_sentiment(self, text: str) -> str:
        """Simple sentiment classification"""
        positive_words = ["great", "love", "amazing", "excellent", "good", "happy", "best"]
        negative_words = ["hate", "bad", "terrible", "awful", "worst", "angry", "disappointed"]
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        else:
            return "neutral"

    def _analyze_engagement(self, posts: List[Dict]) -> Dict[str, Any]:
        """Analyze engagement metrics"""
        
        total_likes = sum(post.get("likes", 0) for post in posts)
        total_shares = sum(post.get("shares", 0) for post in posts)
        total_comments = sum(post.get("comments", 0) for post in posts)
        
        avg_engagement = (total_likes + total_shares + total_comments) / len(posts) if posts else 0
        
        return {
            "total_likes": total_likes,
            "total_shares": total_shares, 
            "total_comments": total_comments,
            "average_engagement": avg_engagement,
            "top_performing_posts": sorted(posts, key=lambda x: x.get("likes", 0) + x.get("shares", 0), reverse=True)[:3]
        }

    def get_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        # Get LLM config schema from mixin
        llm_schema = self._get_llm_schema_section()
        
        return {
            "type": "object",
            "properties": {
                **llm_schema,  # Include LLM provider configuration
                "platforms": {
                    "type": "array",
                    "title": "Social Platforms",
                    "items": {"type": "string", "enum": ["twitter", "linkedin", "facebook", "instagram"]},
                    "default": ["twitter", "linkedin"]
                },
                "analysis_types": {
                    "type": "array", 
                    "title": "Analysis Types",
                    "items": {"type": "string", "enum": ["sentiment", "engagement", "trends"]},
                    "default": ["sentiment", "engagement"]
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "social_data": {
                "type": "array",
                "title": "Social Media Posts",
                "description": "Array of social media post objects",
                "required": True
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "sentiment_analysis": {"type": "object", "description": "Sentiment analysis results"},
            "engagement_analysis": {"type": "object", "description": "Engagement metrics analysis"},
            "summary": {"type": "object", "description": "Overall analysis summary"}
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        social_data = inputs.get("social_data", [])
        return 0.005 + (len(social_data) * 0.001)  # Base cost + per-post cost


# Register the node
NodeRegistry.register(
    "social_analyzer",
    SocialAnalyzerNode,
    SocialAnalyzerNode().get_metadata(),
)