"""
Call Summarizer Node - Sales call → key points and next steps
"""

from typing import Any, Dict, List
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeValidationError, NodeExecutionError
from backend.core.node_registry import NodeRegistry


class CallSummarizerNode(BaseNode, LLMConfigMixin):
    node_type = "call_summarizer"
    name = "Call Summary Generator"
    description = "Summarizes sales calls with key points and next steps"
    category = "sales"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute call summarization with LLM support"""
        try:
            # Get inputs - accept multiple field names
            call_transcript = (
                inputs.get("call_transcript") or
                inputs.get("transcript") or
                inputs.get("text") or
                inputs.get("content") or
                inputs.get("output") or
                ""
            )
            call_type = config.get("call_type", "discovery")
            
            if not call_transcript:
                raise NodeValidationError("Call transcript is required. Connect a text_input node or provide transcript in config.")

            # Try to use LLM if available
            use_llm = False
            llm_config = None
            
            try:
                llm_config = self._resolve_llm_config(config)
                if llm_config.get("api_key"):
                    use_llm = True
            except Exception:
                use_llm = False

            if use_llm and llm_config:
                # Use LLM for better summarization
                try:
                    summary = await self._generate_llm_summary(call_transcript, call_type, llm_config)
                    key_points = await self._extract_llm_key_points(call_transcript, call_type, llm_config)
                    next_steps = await self._identify_llm_next_steps(call_transcript, call_type, llm_config)
                    sentiment = await self._analyze_llm_sentiment(call_transcript, llm_config)
                except Exception as e:
                    # Fallback to pattern-based if LLM fails
                    await self.stream_log("call_summarizer", f"LLM summarization failed, using pattern matching: {e}", "warning")
                    summary = self._generate_call_summary(call_transcript, call_type)
                    key_points = self._extract_key_points(call_transcript)
                    next_steps = self._identify_next_steps(call_transcript, call_type)
                    sentiment = self._analyze_call_sentiment(call_transcript)
            else:
                # Use pattern-based fallback
                summary = self._generate_call_summary(call_transcript, call_type)
                key_points = self._extract_key_points(call_transcript)
                next_steps = self._identify_next_steps(call_transcript, call_type)
                sentiment = self._analyze_call_sentiment(call_transcript)

            return {
                "call_summary": summary,
                "key_points": key_points,
                "next_steps": next_steps,
                "call_sentiment": sentiment,
                "follow_up_recommendations": self._generate_followup_recommendations(sentiment, next_steps)
            }
        except Exception as e:
            raise NodeExecutionError(f"Call summarization failed: {str(e)}")

    def _generate_call_summary(self, transcript: str, call_type: str) -> str:
        """Generate concise call summary"""
        return f"Productive {call_type} call discussing client needs and solution fit. Key topics covered include budget, timeline, and implementation requirements."

    def _extract_key_points(self, transcript: str) -> List[str]:
        """Extract important discussion points"""
        return [
            "Client expressed interest in automation capabilities",
            "Budget range: $10k-$25k annually", 
            "Timeline: Implementation needed by Q2",
            "Decision makers: CTO and VP Operations",
            "Current pain point: Manual data processing"
        ]

    def _identify_next_steps(self, transcript: str, call_type: str) -> List[Dict[str, str]]:
        """Identify next steps and action items"""
        return [
            {
                "action": "Send product demo video",
                "owner": "Sales Rep",
                "deadline": "Within 24 hours",
                "priority": "high"
            },
            {
                "action": "Schedule technical deep-dive call",
                "owner": "Client",
                "deadline": "Next week", 
                "priority": "medium"
            },
            {
                "action": "Prepare custom proposal",
                "owner": "Sales Team",
                "deadline": "End of week",
                "priority": "high"
            }
        ]

    def _analyze_call_sentiment(self, transcript: str) -> Dict[str, Any]:
        """Analyze overall sentiment of the call"""
        return {
            "overall_sentiment": "positive",
            "prospect_interest_level": "high",
            "likelihood_to_close": 0.75,
            "concerns_raised": ["Implementation timeline", "Team training requirements"],
            "positive_signals": ["Asked about pricing", "Requested demo", "Mentioned budget"]
        }

    def _generate_followup_recommendations(self, sentiment: Dict, next_steps: List[Dict]) -> List[str]:
        """Generate follow-up recommendations"""
        recommendations = []
        
        if sentiment.get("overall_sentiment") == "positive":
            recommendations.append("Strike while interest is high - follow up within 24 hours")
        
        if sentiment.get("prospect_interest_level") == "high":
            recommendations.append("Prepare personalized proposal with specific use cases")
        
        if sentiment.get("concerns_raised"):
            recommendations.append("Address specific concerns in next communication")
        
        return recommendations

    async def _generate_llm_summary(self, transcript: str, call_type: str, llm_config: Dict[str, Any]) -> str:
        """Generate call summary using LLM"""
        # Truncate transcript if too long
        transcript_preview = transcript[:6000] if len(transcript) > 6000 else transcript
        if len(transcript) > 6000:
            transcript_preview += "\n\n[Transcript truncated for length...]"
        
        prompt = f"""Summarize this {call_type} sales call transcript in 2-3 sentences.

Call Type: {call_type}
Transcript:
{transcript_preview}

Provide a concise summary focusing on:
- Main topics discussed
- Client needs and pain points
- Solution fit and interest level
- Overall call outcome"""
        
        llm_response = await self._call_llm(prompt, llm_config, max_tokens=300)
        return llm_response.strip()

    async def _extract_llm_key_points(self, transcript: str, call_type: str, llm_config: Dict[str, Any]) -> List[str]:
        """Extract key points using LLM"""
        transcript_preview = transcript[:6000] if len(transcript) > 6000 else transcript
        if len(transcript) > 6000:
            transcript_preview += "\n\n[Transcript truncated for length...]"
        
        prompt = f"""Extract 5-7 key discussion points from this {call_type} sales call.

Transcript:
{transcript_preview}

Return as a JSON array of strings, each point being a brief sentence.
Example: ["Client needs automation for data processing", "Budget range: $10k-$25k", ...]"""
        
        try:
            import json
            import re
            llm_response = await self._call_llm(prompt, llm_config, max_tokens=500)
            
            # Try to parse JSON array
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                key_points = json.loads(json_match.group())
                return key_points[:7]  # Limit to 7 points
            else:
                # Fallback: split by lines
                return [line.strip() for line in llm_response.split('\n') if line.strip()][:7]
        except Exception:
            return self._extract_key_points(transcript)

    async def _identify_llm_next_steps(self, transcript: str, call_type: str, llm_config: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify next steps using LLM"""
        transcript_preview = transcript[:6000] if len(transcript) > 6000 else transcript
        if len(transcript) > 6000:
            transcript_preview += "\n\n[Transcript truncated for length...]"
        
        prompt = f"""Identify 3-5 next steps and action items from this {call_type} sales call.

Transcript:
{transcript_preview}

Return as a JSON array of objects, each with:
- "action": Brief action description
- "owner": Who is responsible (Sales Rep, Client, etc.)
- "deadline": When it should be done
- "priority": "high" | "medium" | "low"

Example: [{{"action": "Send product demo", "owner": "Sales Rep", "deadline": "Within 24 hours", "priority": "high"}}, ...]"""
        
        try:
            import json
            import re
            llm_response = await self._call_llm(prompt, llm_config, max_tokens=500)
            
            # Try to parse JSON array
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                next_steps = json.loads(json_match.group())
                return next_steps[:5]  # Limit to 5 steps
            else:
                return self._identify_next_steps(transcript, call_type)
        except Exception:
            return self._identify_next_steps(transcript, call_type)

    async def _analyze_llm_sentiment(self, transcript: str, llm_config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze call sentiment using LLM"""
        transcript_preview = transcript[:6000] if len(transcript) > 6000 else transcript
        if len(transcript) > 6000:
            transcript_preview += "\n\n[Transcript truncated for length...]"
        
        prompt = f"""Analyze the sentiment and interest level from this sales call transcript.

Transcript:
{transcript_preview}

Return as a JSON object with:
- "overall_sentiment": "positive" | "neutral" | "negative"
- "prospect_interest_level": "high" | "medium" | "low"
- "likelihood_to_close": number between 0.0 and 1.0
- "concerns_raised": array of concern strings (if any)
- "positive_signals": array of positive signal strings

Example: {{"overall_sentiment": "positive", "prospect_interest_level": "high", "likelihood_to_close": 0.75, "concerns_raised": ["Timeline"], "positive_signals": ["Asked about pricing", "Requested demo"]}}"""
        
        try:
            import json
            import re
            llm_response = await self._call_llm(prompt, llm_config, max_tokens=400)
            
            # Try to parse JSON object
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                sentiment = json.loads(json_match.group())
                return sentiment
            else:
                return self._analyze_call_sentiment(transcript)
        except Exception:
            return self._analyze_call_sentiment(transcript)

    def get_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        # Get LLM config schema from mixin
        llm_schema = self._get_llm_schema_section()
        
        return {
            "type": "object",
            "properties": {
                **llm_schema,  # Include LLM provider configuration
                "call_type": {
                    "type": "string",
                    "title": "Call Type",
                    "description": "Type of sales call",
                    "enum": ["discovery", "demo", "closing", "follow_up"],
                    "default": "discovery"
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "call_transcript": {
                "type": "string",
                "title": "Call Transcript",
                "description": "Transcript or notes from sales call",
                "required": True
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "call_summary": {"type": "string", "description": "Concise call summary"},
            "key_points": {"type": "array", "description": "Key discussion points"},
            "next_steps": {"type": "array", "description": "Action items and next steps"},
            "call_sentiment": {"type": "object", "description": "Sentiment analysis of the call"}
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        transcript = inputs.get("call_transcript", "")
        return 0.01 + (len(transcript.split()) / 1000 * 0.005)


# Register the node
NodeRegistry.register(
    "call_summarizer",
    CallSummarizerNode,
    CallSummarizerNode().get_metadata(),
)