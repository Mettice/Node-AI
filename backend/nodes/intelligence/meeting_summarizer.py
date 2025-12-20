"""
Meeting Summarizer Node - Takes meeting transcripts and converts them to action items

This node processes meeting transcripts/notes and generates:
- Executive summary
- Key decisions made
- Action items with owners and deadlines
- Follow-up tasks
- Important topics discussed
"""

import re
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeExecutionError, NodeValidationError
from backend.core.node_registry import NodeRegistry


class MeetingSummarizerNode(BaseNode, LLMConfigMixin):
    node_type = "meeting_summarizer"
    name = "Meeting Summarizer"
    description = "Converts meeting transcripts into structured summaries with action items"
    category = "intelligence"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute meeting summarization"""
        try:
            await self.stream_progress("meeting_summarizer", 0.1, "Processing meeting transcript...")

            # Get inputs - accept multiple field names for flexibility
            # text_input provides "text", but we also accept "transcript", "content", "output"
            transcript = (
                inputs.get("transcript") or 
                inputs.get("text") or 
                inputs.get("content") or 
                inputs.get("output") or
                ""
            )
            meeting_title = inputs.get("meeting_title") or config.get("meeting_title", "Meeting")
            attendees = inputs.get("attendees") or config.get("attendees", [])
            meeting_date = inputs.get("meeting_date") or config.get("meeting_date", datetime.now().isoformat())
            
            # Get configuration
            summary_style = config.get("summary_style", "detailed")
            extract_action_items = config.get("extract_action_items", True)
            identify_decisions = config.get("identify_decisions", True)
            include_timestamps = config.get("include_timestamps", True)

            if not transcript:
                raise NodeValidationError("Meeting transcript is required")

            await self.stream_progress("meeting_summarizer", 0.3, "Analyzing transcript content...")

            # Parse and clean transcript
            cleaned_transcript = self._clean_transcript(transcript)
            
            await self.stream_progress("meeting_summarizer", 0.5, "Extracting key information...")

            # Extract key information (pass config for LLM support)
            summary_data = await self._extract_meeting_info(
                cleaned_transcript, meeting_title, attendees, summary_style, config
            )

            await self.stream_progress("meeting_summarizer", 0.7, "Identifying action items and decisions...")

            # Extract action items if requested
            if extract_action_items:
                action_items = self._extract_action_items(cleaned_transcript, attendees)
                summary_data["action_items"] = action_items

            # Extract decisions if requested  
            if identify_decisions:
                decisions = self._extract_decisions(cleaned_transcript)
                summary_data["decisions"] = decisions

            await self.stream_progress("meeting_summarizer", 0.9, "Generating final summary...")

            # Generate follow-up recommendations
            follow_ups = self._generate_follow_ups(summary_data)

            result = {
                "meeting_summary": summary_data,
                "follow_up_recommendations": follow_ups,
                "metadata": {
                    "meeting_title": meeting_title,
                    "meeting_date": meeting_date,
                    "attendee_count": len(attendees),
                    "transcript_length": len(transcript),
                    "processing_timestamp": datetime.now().isoformat(),
                    "summary_style": summary_style
                }
            }

            await self.stream_progress("meeting_summarizer", 1.0, "Meeting summary complete!")
            return result

        except Exception as e:
            raise NodeExecutionError(f"Meeting summarization failed: {str(e)}")

    def _clean_transcript(self, transcript: str) -> str:
        """Clean and normalize the transcript text"""
        # Remove multiple whitespaces
        cleaned = re.sub(r'\s+', ' ', transcript)
        
        # Remove common transcript artifacts
        cleaned = re.sub(r'\[INAUDIBLE\]|\[CROSSTALK\]|\[MUSIC\]|\[LAUGHTER\]', '', cleaned)
        
        # Normalize speaker labels
        cleaned = re.sub(r'(\w+):\s*', r'\1: ', cleaned)
        
        # Remove excessive punctuation
        cleaned = re.sub(r'[.]{3,}', '...', cleaned)
        
        return cleaned.strip()

    async def _extract_meeting_info(
        self, 
        transcript: str, 
        title: str, 
        attendees: List[str], 
        style: str,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Extract key meeting information and generate summary using LLM when available"""
        
        # Split transcript into segments for analysis
        segments = self._segment_transcript(transcript)
        
        # Extract topics discussed (use pattern matching for structure)
        topics = self._extract_topics(segments)
        
        # Try to use LLM for better summarization if available
        use_llm = config is not None
        llm_config = None
        
        if use_llm:
            try:
                llm_config = self._resolve_llm_config(config)
                if llm_config.get("api_key"):
                    use_llm = True
                else:
                    use_llm = False
            except Exception:
                use_llm = False
        
        # Generate executive summary - use LLM if available, otherwise use pattern matching
        if use_llm and llm_config:
            try:
                summary = await self._generate_llm_summary(transcript, title, attendees, style, topics, llm_config)
            except Exception as e:
                # Fallback to pattern matching if LLM fails
                await self.stream_log("meeting_summarizer", f"LLM summarization failed, using pattern matching: {e}", "warning")
                if style == "brief":
                    summary = self._generate_brief_summary(segments, topics)
                elif style == "detailed":
                    summary = self._generate_detailed_summary(segments, topics)
                else:
                    summary = self._generate_standard_summary(segments, topics)
        else:
            # Use pattern matching fallback
            if style == "brief":
                summary = self._generate_brief_summary(segments, topics)
            elif style == "detailed":
                summary = self._generate_detailed_summary(segments, topics)
            else:
                summary = self._generate_standard_summary(segments, topics)

        # Extract key participants and their contributions
        participants = self._analyze_participants(transcript, attendees)

        meeting_info = {
            "title": title,
            "executive_summary": summary,
            "main_topics": topics,
            "participants": participants,
            "duration_estimate": self._estimate_meeting_duration(transcript),
            "key_quotes": self._extract_key_quotes(segments),
            "next_steps": []  # Will be populated by action items
        }

        return meeting_info

    def _segment_transcript(self, transcript: str) -> List[Dict[str, str]]:
        """Split transcript into speaker segments"""
        segments = []
        
        # Pattern to match speaker changes (Name: content)
        speaker_pattern = r'(\w+(?:\s+\w+)*?):\s*(.*?)(?=\w+:|$)'
        matches = re.finditer(speaker_pattern, transcript, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            speaker = match.group(1).strip()
            content = match.group(2).strip()
            
            if content:  # Only include non-empty segments
                segments.append({
                    "speaker": speaker,
                    "content": content,
                    "timestamp": None  # Could be extracted if present in transcript
                })
        
        # If no speaker patterns found, treat as single segment
        if not segments:
            segments.append({
                "speaker": "Unknown",
                "content": transcript,
                "timestamp": None
            })
        
        return segments

    def _extract_topics(self, segments: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Extract main topics from meeting segments"""
        topics = []
        
        # Keywords that indicate topic changes
        topic_indicators = [
            r'\b(?:let\'s talk about|moving on to|next topic|regarding|about)\b',
            r'\b(?:first|second|third|next|finally|lastly)\b',
            r'\b(?:agenda item|point \d+|item \d+)\b'
        ]
        
        current_topic = None
        topic_content = []
        
        for segment in segments:
            content = segment["content"].lower()
            
            # Check for topic change indicators
            topic_change = any(re.search(pattern, content) for pattern in topic_indicators)
            
            if topic_change or current_topic is None:
                # Save previous topic if exists
                if current_topic and topic_content:
                    topics.append({
                        "topic": current_topic,
                        "content": " ".join(topic_content),
                        "speakers": list(set([s["speaker"] for s in segments if s["content"] in topic_content]))
                    })
                
                # Start new topic
                current_topic = self._extract_topic_name(segment["content"])
                topic_content = [segment["content"]]
            else:
                # Continue current topic
                if current_topic:
                    topic_content.append(segment["content"])
        
        # Add the last topic
        if current_topic and topic_content:
            topics.append({
                "topic": current_topic,
                "content": " ".join(topic_content),
                "speakers": list(set([s["speaker"] for s in segments if s["content"] in topic_content]))
            })
        
        return topics

    def _extract_topic_name(self, content: str) -> str:
        """Extract topic name from content"""
        # Look for topic-indicating phrases
        topic_patterns = [
            r'(?:talk about|discuss|regarding|about)\s+([^.,]+)',
            r'(?:topic|subject|matter)\s+(?:is|was)?\s*([^.,]+)',
            r'(?:moving on to|next is)\s+([^.,]+)'
        ]
        
        for pattern in topic_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: use first few words
        words = content.split()[:5]
        return " ".join(words) + "..."

    def _extract_action_items(self, transcript: str, attendees: List[str]) -> List[Dict[str, Any]]:
        """Extract action items from transcript"""
        action_items = []
        
        # Patterns that indicate action items
        action_patterns = [
            r'\b(?:action item|todo|task|assignment|deliverable)[:,]?\s*(.+?)(?:\.|$)',
            r'\b(?:will|should|need to|must|responsible for)\s+(.+?)(?:\.|$)',
            r'\b(?:by \w+|deadline|due|complete by)\s+(.+?)(?:\.|$)',
            r'\b(?:follow up|next step|action)\s*[:,]?\s*(.+?)(?:\.|$)'
        ]
        
        sentences = transcript.split('.')
        
        for i, sentence in enumerate(sentences):
            for pattern in action_patterns:
                matches = re.finditer(pattern, sentence, re.IGNORECASE)
                for match in matches:
                    action_text = match.group(1).strip()
                    
                    if len(action_text) > 10:  # Filter out very short matches
                        # Try to identify owner/assignee
                        owner = self._identify_action_owner(sentence, attendees)
                        
                        # Try to extract deadline
                        deadline = self._extract_deadline(action_text)
                        
                        action_item = {
                            "description": action_text,
                            "owner": owner,
                            "deadline": deadline,
                            "priority": self._assess_action_priority(action_text),
                            "status": "pending",
                            "context": sentence.strip()
                        }
                        
                        action_items.append(action_item)
        
        # Remove duplicates based on description similarity
        action_items = self._deduplicate_actions(action_items)
        
        return action_items

    def _identify_action_owner(self, sentence: str, attendees: List[str]) -> Optional[str]:
        """Try to identify who is responsible for an action item"""
        sentence_lower = sentence.lower()
        
        # Look for explicit assignment patterns
        for attendee in attendees:
            attendee_lower = attendee.lower()
            assignment_patterns = [
                f'{attendee_lower} will',
                f'{attendee_lower} should',
                f'{attendee_lower} to',
                f'assign(?:ed)? to {attendee_lower}',
                f'{attendee_lower}(?:\'s| is) responsible'
            ]
            
            for pattern in assignment_patterns:
                if re.search(pattern, sentence_lower):
                    return attendee
        
        return None

    def _extract_deadline(self, action_text: str) -> Optional[str]:
        """Extract deadline from action text"""
        deadline_patterns = [
            r'\b(?:by|before|due)\s+(\w+\s+\d+)',
            r'\b(?:next|this)\s+(week|month|friday|monday|tuesday|wednesday|thursday)',
            r'\b(\d+)\s+(days?|weeks?|months?)',
            r'\b(tomorrow|today|asap|immediately)\b'
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, action_text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None

    def _assess_action_priority(self, action_text: str) -> str:
        """Assess priority level of action item"""
        high_priority_indicators = [
            'urgent', 'asap', 'immediately', 'critical', 'important', 'priority'
        ]
        
        low_priority_indicators = [
            'whenever', 'eventually', 'nice to have', 'optional'
        ]
        
        action_lower = action_text.lower()
        
        if any(indicator in action_lower for indicator in high_priority_indicators):
            return "high"
        elif any(indicator in action_lower for indicator in low_priority_indicators):
            return "low"
        else:
            return "medium"

    def _extract_decisions(self, transcript: str) -> List[Dict[str, Any]]:
        """Extract decisions made during the meeting"""
        decisions = []
        
        decision_patterns = [
            r'\b(?:we decided|decision|concluded|agreed|resolved)\s+(?:that\s+)?(.+?)(?:\.|$)',
            r'\b(?:final|outcome|result)\s*[:,]?\s*(.+?)(?:\.|$)',
            r'\b(?:vote|consensus|unanimous)\s+(?:on|for)?\s*(.+?)(?:\.|$)'
        ]
        
        sentences = transcript.split('.')
        
        for sentence in sentences:
            for pattern in decision_patterns:
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    decision_text = match.group(1).strip()
                    
                    if len(decision_text) > 10:
                        decision = {
                            "description": decision_text,
                            "context": sentence.strip(),
                            "impact": self._assess_decision_impact(decision_text),
                            "type": self._classify_decision_type(decision_text)
                        }
                        decisions.append(decision)
        
        return self._deduplicate_decisions(decisions)

    def _generate_brief_summary(self, segments: List[Dict], topics: List[Dict]) -> str:
        """Generate a brief meeting summary"""
        if not topics:
            return "Meeting covered various topics with participant discussions."
        
        topic_names = [topic["topic"] for topic in topics[:3]]
        summary = f"Meeting covered {len(topics)} main topics including: {', '.join(topic_names)}"
        
        if len(topics) > 3:
            summary += f" and {len(topics) - 3} other topics."
        
        return summary

    def _generate_detailed_summary(self, segments: List[Dict], topics: List[Dict]) -> str:
        """Generate a detailed meeting summary"""
        summary_parts = []
        
        summary_parts.append(f"Meeting involved {len(set([s['speaker'] for s in segments]))} participants discussing {len(topics)} main topics.")
        
        for i, topic in enumerate(topics[:5]):  # Limit to 5 topics for detailed view
            summary_parts.append(f"{i+1}. {topic['topic']}: {topic['content'][:200]}{'...' if len(topic['content']) > 200 else ''}")
        
        return "\n\n".join(summary_parts)

    def _generate_standard_summary(self, segments: List[Dict], topics: List[Dict]) -> str:
        """Generate a standard meeting summary"""
        summary_parts = []
        
        # Overview
        participant_count = len(set([s['speaker'] for s in segments]))
        summary_parts.append(f"Meeting with {participant_count} participants covered {len(topics)} key topics.")
        
        # Main topics
        if topics:
            topic_list = [f"• {topic['topic']}" for topic in topics[:4]]
            summary_parts.append("Main topics discussed:\n" + "\n".join(topic_list))
            
            if len(topics) > 4:
                summary_parts.append(f"...and {len(topics) - 4} additional topics.")
        
        return "\n\n".join(summary_parts)

    async def _generate_llm_summary(
        self,
        transcript: str,
        title: str,
        attendees: List[str],
        style: str,
        topics: List[Dict],
        llm_config: Dict[str, Any]
    ) -> str:
        """Generate meeting summary using LLM for better quality"""
        
        # Prepare transcript summary for LLM (truncate if too long)
        transcript_preview = transcript[:8000] if len(transcript) > 8000 else transcript
        if len(transcript) > 8000:
            transcript_preview += "\n\n[Transcript truncated for length...]"
        
        # Build prompt based on style
        if style == "brief":
            prompt = f"""Summarize this meeting transcript in 2-3 sentences.

Meeting Title: {title}
Attendees: {', '.join(attendees) if attendees else 'Not specified'}
Main Topics Identified: {', '.join([t['topic'] for t in topics[:5]])}

Transcript:
{transcript_preview}

Provide a concise executive summary focusing on key outcomes and decisions."""
        
        elif style == "detailed":
            prompt = f"""Create a comprehensive meeting summary with the following structure:

1. Executive Summary (2-3 paragraphs)
2. Key Topics Discussed (bullet points)
3. Main Decisions Made
4. Important Points Raised

Meeting Title: {title}
Attendees: {', '.join(attendees) if attendees else 'Not specified'}

Transcript:
{transcript_preview}

Generate a detailed, well-structured summary."""
        
        else:  # standard
            prompt = f"""Summarize this meeting transcript in a clear, structured format.

Meeting Title: {title}
Attendees: {', '.join(attendees) if attendees else 'Not specified'}

Transcript:
{transcript_preview}

Provide a summary that includes:
- Overview of what was discussed
- Key topics covered
- Main outcomes or decisions

Format the summary in a professional, easy-to-read manner."""
        
        # Call LLM
        llm_response = await self._call_llm(prompt, llm_config, max_tokens=2000)
        
        return llm_response.strip()

    def _analyze_participants(self, transcript: str, attendees: List[str]) -> List[Dict[str, Any]]:
        """Analyze participant contributions"""
        participants = []
        
        segments = self._segment_transcript(transcript)
        speaker_stats = {}
        
        for segment in segments:
            speaker = segment["speaker"]
            if speaker not in speaker_stats:
                speaker_stats[speaker] = {
                    "segments": 0,
                    "words": 0,
                    "topics": set()
                }
            
            speaker_stats[speaker]["segments"] += 1
            speaker_stats[speaker]["words"] += len(segment["content"].split())
        
        for speaker, stats in speaker_stats.items():
            participant = {
                "name": speaker,
                "segments_count": stats["segments"],
                "word_count": stats["words"],
                "participation_level": self._assess_participation_level(stats, speaker_stats)
            }
            participants.append(participant)
        
        return sorted(participants, key=lambda x: x["word_count"], reverse=True)

    def _assess_participation_level(self, speaker_stats: Dict, all_stats: Dict) -> str:
        """Assess how active a participant was"""
        total_words = sum(stats["words"] for stats in all_stats.values())
        speaker_percentage = speaker_stats["words"] / total_words if total_words > 0 else 0
        
        if speaker_percentage > 0.4:
            return "high"
        elif speaker_percentage > 0.15:
            return "medium"
        else:
            return "low"

    def _extract_key_quotes(self, segments: List[Dict]) -> List[Dict[str, str]]:
        """Extract notable quotes from the meeting"""
        quotes = []
        
        # Look for segments with decision-making language or strong statements
        quote_indicators = [
            r'\b(?:i believe|i think|in my opinion|i strongly|i recommend)\b',
            r'\b(?:the key is|most important|critical|essential)\b',
            r'\b(?:we should|we must|we need to|we have to)\b'
        ]
        
        for segment in segments:
            content = segment["content"]
            if len(content.split()) > 10:  # Only consider substantial statements
                for pattern in quote_indicators:
                    if re.search(pattern, content, re.IGNORECASE):
                        quotes.append({
                            "speaker": segment["speaker"],
                            "quote": content[:200] + "..." if len(content) > 200 else content
                        })
                        break
        
        return quotes[:5]  # Limit to 5 key quotes

    def _estimate_meeting_duration(self, transcript: str) -> str:
        """Estimate meeting duration based on transcript length"""
        word_count = len(transcript.split())
        
        # Rough estimate: 150 words per minute average speaking rate
        estimated_minutes = word_count / 150
        
        if estimated_minutes < 60:
            return f"~{int(estimated_minutes)} minutes"
        else:
            hours = int(estimated_minutes // 60)
            minutes = int(estimated_minutes % 60)
            return f"~{hours}h {minutes}m"

    def _deduplicate_actions(self, actions: List[Dict]) -> List[Dict]:
        """Remove duplicate action items"""
        seen = set()
        unique_actions = []
        
        for action in actions:
            # Create a simple hash based on description
            desc_hash = action["description"].lower().strip()[:50]
            if desc_hash not in seen:
                seen.add(desc_hash)
                unique_actions.append(action)
        
        return unique_actions

    def _deduplicate_decisions(self, decisions: List[Dict]) -> List[Dict]:
        """Remove duplicate decisions"""
        seen = set()
        unique_decisions = []
        
        for decision in decisions:
            desc_hash = decision["description"].lower().strip()[:50]
            if desc_hash not in seen:
                seen.add(desc_hash)
                unique_decisions.append(decision)
        
        return unique_decisions

    def _assess_decision_impact(self, decision_text: str) -> str:
        """Assess the impact level of a decision"""
        high_impact_words = ['budget', 'hire', 'fire', 'strategy', 'launch', 'cancel', 'invest']
        medium_impact_words = ['schedule', 'meeting', 'process', 'update', 'change']
        
        decision_lower = decision_text.lower()
        
        if any(word in decision_lower for word in high_impact_words):
            return "high"
        elif any(word in decision_lower for word in medium_impact_words):
            return "medium"
        else:
            return "low"

    def _classify_decision_type(self, decision_text: str) -> str:
        """Classify the type of decision"""
        decision_lower = decision_text.lower()
        
        if any(word in decision_lower for word in ['budget', 'cost', 'money', 'price']):
            return "financial"
        elif any(word in decision_lower for word in ['hire', 'team', 'staff', 'role']):
            return "personnel"
        elif any(word in decision_lower for word in ['product', 'feature', 'launch']):
            return "product"
        elif any(word in decision_lower for word in ['process', 'workflow', 'procedure']):
            return "operational"
        else:
            return "general"

    def _generate_follow_ups(self, summary_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate follow-up recommendations"""
        follow_ups = []
        
        # Follow-ups based on action items
        if "action_items" in summary_data:
            action_count = len(summary_data["action_items"])
            if action_count > 0:
                follow_ups.append({
                    "type": "action_tracking",
                    "recommendation": f"Set up tracking for {action_count} action items",
                    "priority": "high"
                })
                
                # Check for items without owners
                unowned = [item for item in summary_data["action_items"] if not item.get("owner")]
                if unowned:
                    follow_ups.append({
                        "type": "assignment",
                        "recommendation": f"Assign owners to {len(unowned)} action items",
                        "priority": "high"
                    })
        
        # Follow-ups based on decisions
        if "decisions" in summary_data:
            high_impact_decisions = [d for d in summary_data["decisions"] if d.get("impact") == "high"]
            if high_impact_decisions:
                follow_ups.append({
                    "type": "decision_communication",
                    "recommendation": f"Communicate {len(high_impact_decisions)} high-impact decisions to stakeholders",
                    "priority": "high"
                })
        
        # General follow-ups
        follow_ups.append({
            "type": "summary_distribution",
            "recommendation": "Share meeting summary with all attendees",
            "priority": "medium"
        })
        
        return follow_ups

    def get_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        # Get LLM config schema from mixin
        llm_schema = self._get_llm_schema_section()
        
        return {
            "type": "object",
            "properties": {
                **llm_schema,  # Include LLM provider configuration
                "summary_style": {
                    "type": "string",
                    "title": "Summary Style",
                    "description": "Level of detail for the meeting summary",
                    "enum": ["brief", "standard", "detailed"],
                    "default": "detailed"
                },
                "extract_action_items": {
                    "type": "boolean",
                    "title": "Extract Action Items",
                    "description": "Automatically identify and extract action items",
                    "default": True
                },
                "identify_decisions": {
                    "type": "boolean",
                    "title": "Identify Decisions",
                    "description": "Identify and categorize decisions made",
                    "default": True
                },
                "include_timestamps": {
                    "type": "boolean",
                    "title": "Include Timestamps",
                    "description": "Include timing information if available",
                    "default": True
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        """Define expected inputs"""
        return {
            "transcript": {
                "type": "string",
                "title": "Meeting Transcript",
                "description": "Full text of the meeting transcript or notes",
                "required": True
            },
            "meeting_title": {
                "type": "string",
                "title": "Meeting Title",
                "description": "Title or subject of the meeting",
                "default": "Meeting"
            },
            "attendees": {
                "type": "array",
                "title": "Attendees",
                "description": "List of meeting attendees",
                "items": {"type": "string"},
                "default": []
            },
            "meeting_date": {
                "type": "string",
                "title": "Meeting Date",
                "description": "Date and time of the meeting (ISO format)",
                "format": "date-time"
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Define expected outputs"""
        return {
            "meeting_summary": {
                "type": "object",
                "description": "Comprehensive meeting summary with topics and insights"
            },
            "follow_up_recommendations": {
                "type": "array", 
                "description": "Recommended follow-up actions"
            },
            "metadata": {
                "type": "object",
                "description": "Meeting metadata and processing information"
            }
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        """Estimate cost based on transcript length and processing complexity"""
        transcript = inputs.get("transcript", "")
        
        # Base cost for processing
        base_cost = 0.005
        
        # Cost based on transcript length (longer transcripts require more processing)
        word_count = len(transcript.split())
        length_cost = word_count / 1000 * 0.002  # $0.002 per 1000 words
        
        # Additional cost for advanced features
        feature_cost = 0
        if config.get("extract_action_items", True):
            feature_cost += 0.001
        if config.get("identify_decisions", True):
            feature_cost += 0.001
            
        return base_cost + length_cost + feature_cost


# Register the node
NodeRegistry.register(
    "meeting_summarizer",
    MeetingSummarizerNode,
    MeetingSummarizerNode().get_metadata(),
)