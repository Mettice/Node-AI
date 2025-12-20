"""
Follow-up Writer Node - Meeting notes → personalized follow-up emails
"""

from typing import Any, Dict
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeValidationError, NodeExecutionError
from backend.core.node_registry import NodeRegistry


class FollowupWriterNode(BaseNode, LLMConfigMixin):
    node_type = "followup_writer"
    name = "Follow-up Writer"
    description = "Generates personalized follow-up emails from meeting notes"
    category = "sales"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute follow-up email generation with LLM support"""
        try:
            # Get inputs - accept multiple field names
            meeting_notes = (
                inputs.get("meeting_notes") or
                inputs.get("notes") or
                inputs.get("text") or
                inputs.get("content") or
                inputs.get("output") or
                ""
            )
            email_tone = config.get("email_tone", "professional")
            include_attachments = config.get("include_attachments", True)
            
            if not meeting_notes:
                raise NodeValidationError("Meeting notes are required. Connect a text_input node or provide meeting_notes in config.")

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
                # Use LLM for better email generation
                try:
                    email_content = await self._generate_llm_email(meeting_notes, email_tone, llm_config)
                    suggested_attachments = await self._suggest_llm_attachments(meeting_notes, llm_config) if include_attachments else []
                    send_timing = await self._recommend_llm_timing(meeting_notes, llm_config)
                except Exception as e:
                    # Fallback to pattern-based if LLM fails
                    await self.stream_log("followup_writer", f"LLM generation failed, using pattern matching: {e}", "warning")
                    email_content = self._generate_followup_email(meeting_notes, email_tone)
                    suggested_attachments = self._suggest_attachments(meeting_notes) if include_attachments else []
                    send_timing = self._recommend_send_timing(meeting_notes)
            else:
                # Use pattern-based fallback
                email_content = self._generate_followup_email(meeting_notes, email_tone)
                suggested_attachments = self._suggest_attachments(meeting_notes) if include_attachments else []
                send_timing = self._recommend_send_timing(meeting_notes)

            return {
                "email_content": email_content,
                "suggested_attachments": suggested_attachments,
                "send_timing": send_timing,
                "email_subject": email_content.get("subject", "Follow-up from our meeting")
            }
        except Exception as e:
            raise NodeExecutionError(f"Follow-up email generation failed: {str(e)}")

    def _generate_followup_email(self, notes: str, tone: str) -> Dict[str, str]:
        """Generate personalized follow-up email"""
        
        tone_styles = {
            "professional": "formal and business-focused",
            "friendly": "warm and approachable", 
            "casual": "relaxed and conversational"
        }
        
        style = tone_styles.get(tone, "professional")
        
        return {
            "subject": "Great meeting you today - Next steps",
            "body": f"""Hi [Name],

Thank you for taking the time to meet with me today. I really enjoyed our conversation about [topic from notes].

Based on our discussion, I wanted to follow up on a few key points:
• [Key point 1 from meeting]
• [Key point 2 from meeting]  
• [Action item discussed]

As mentioned, I'm attaching [relevant materials] that should help address your questions about [specific topic].

I'd love to schedule a follow-up call next week to discuss [next steps]. Would Tuesday or Wednesday afternoon work better for you?

Looking forward to hearing from you!

Best regards,
[Your Name]""",
            "tone": style,
            "personalization_fields": ["Name", "topic from notes", "Key point 1", "Key point 2", "specific topic"]
        }

    def _suggest_attachments(self, notes: str) -> list:
        """Suggest relevant attachments based on meeting content"""
        attachments = []
        
        if "pricing" in notes.lower() or "cost" in notes.lower():
            attachments.append({
                "type": "pricing_sheet",
                "name": "Product Pricing Guide.pdf",
                "description": "Comprehensive pricing information"
            })
        
        if "demo" in notes.lower() or "product" in notes.lower():
            attachments.append({
                "type": "product_overview",
                "name": "Product Demo Video.mp4", 
                "description": "Product demonstration and features"
            })
        
        if "case study" in notes.lower() or "examples" in notes.lower():
            attachments.append({
                "type": "case_study",
                "name": "Customer Success Stories.pdf",
                "description": "Relevant customer case studies"
            })
        
        return attachments

    def _recommend_send_timing(self, notes: str) -> Dict[str, str]:
        """Recommend optimal send timing"""
        
        # Analyze urgency and context
        if "urgent" in notes.lower() or "asap" in notes.lower():
            timing = "immediate"
            delay = "Send within 1-2 hours"
        elif "follow up" in notes.lower() and "week" in notes.lower():
            timing = "delayed"
            delay = "Send in 2-3 days"
        else:
            timing = "standard"
            delay = "Send within 24 hours"
        
        return {
            "timing": timing,
            "recommended_delay": delay,
            "best_send_time": "10:00 AM - 2:00 PM on weekdays",
            "reasoning": "Based on general email engagement patterns and meeting context"
        }

    async def _generate_llm_email(self, notes: str, tone: str, llm_config: Dict[str, Any]) -> Dict[str, str]:
        """Generate personalized follow-up email using LLM"""
        # Truncate notes if too long
        notes_preview = notes[:5000] if len(notes) > 5000 else notes
        if len(notes) > 5000:
            notes_preview += "\n\n[Notes truncated for length...]"
        
        tone_descriptions = {
            "professional": "formal and business-focused",
            "friendly": "warm and approachable",
            "casual": "relaxed and conversational"
        }
        tone_desc = tone_descriptions.get(tone, "professional")
        
        prompt = f"""Generate a personalized follow-up email based on these meeting notes.

Meeting Notes:
{notes_preview}

Email Tone: {tone} ({tone_desc})

Generate a complete email with:
1. Subject line (concise and action-oriented)
2. Email body (personalized, references specific points from meeting)
3. Clear next steps
4. Professional closing

Return as JSON object with:
- "subject": Email subject line
- "body": Complete email body (use [Name] as placeholder for recipient name)
- "tone": The tone used
- "key_points_covered": Array of key points from meeting that are referenced

Make it personalized and specific to the meeting content."""
        
        try:
            import json
            import re
            llm_response = await self._call_llm(prompt, llm_config, max_tokens=1500)
            
            # Try to parse JSON
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                email_content = json.loads(json_match.group())
                return email_content
            else:
                # Fallback: extract subject and body from text
                return self._parse_email_from_text(llm_response, tone)
        except Exception:
            return self._generate_followup_email(notes, tone)

    async def _suggest_llm_attachments(self, notes: str, llm_config: Dict[str, Any]) -> list:
        """Suggest attachments using LLM"""
        notes_preview = notes[:3000] if len(notes) > 3000 else notes
        
        prompt = f"""Based on these meeting notes, suggest 2-4 relevant attachments that would be helpful to include in a follow-up email.

Meeting Notes:
{notes_preview}

Return as JSON array of objects, each with:
- "type": Type of attachment (e.g., "pricing_sheet", "product_overview", "case_study", "whitepaper")
- "name": Suggested filename
- "description": Why this attachment is relevant

Only suggest attachments that are clearly relevant to the meeting content."""
        
        try:
            import json
            import re
            llm_response = await self._call_llm(prompt, llm_config, max_tokens=400)
            
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                attachments = json.loads(json_match.group())
                return attachments[:4]  # Limit to 4
            else:
                return self._suggest_attachments(notes)
        except Exception:
            return self._suggest_attachments(notes)

    async def _recommend_llm_timing(self, notes: str, llm_config: Dict[str, Any]) -> Dict[str, str]:
        """Recommend send timing using LLM"""
        notes_preview = notes[:3000] if len(notes) > 3000 else notes
        
        prompt = f"""Based on these meeting notes, recommend the optimal timing for sending a follow-up email.

Meeting Notes:
{notes_preview}

Return as JSON object with:
- "timing": "immediate" | "standard" | "delayed"
- "recommended_delay": Specific delay recommendation (e.g., "Send within 24 hours")
- "best_send_time": Best time of day/day of week to send
- "reasoning": Brief explanation of the recommendation

Consider urgency, meeting context, and best practices for email engagement."""
        
        try:
            import json
            import re
            llm_response = await self._call_llm(prompt, llm_config, max_tokens=300)
            
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                timing = json.loads(json_match.group())
                return timing
            else:
                return self._recommend_send_timing(notes)
        except Exception:
            return self._recommend_send_timing(notes)

    def _parse_email_from_text(self, text: str, tone: str) -> Dict[str, str]:
        """Parse email from LLM text response if JSON parsing fails"""
        lines = text.split('\n')
        subject = ""
        body_lines = []
        in_body = False
        
        for line in lines:
            line = line.strip()
            if line.lower().startswith('subject:'):
                subject = line.split(':', 1)[1].strip()
            elif line.lower().startswith('subject line:'):
                subject = line.split(':', 1)[1].strip()
            elif line and not in_body and not line.startswith('#'):
                in_body = True
                body_lines.append(line)
            elif in_body:
                body_lines.append(line)
        
        if not subject:
            subject = "Follow-up from our meeting"
        
        body = '\n'.join(body_lines) if body_lines else text
        
        return {
            "subject": subject,
            "body": body,
            "tone": tone,
            "key_points_covered": []
        }

    def get_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        # Get LLM config schema from mixin
        llm_schema = self._get_llm_schema_section()
        
        return {
            "type": "object",
            "properties": {
                **llm_schema,  # Include LLM provider configuration
                "email_tone": {
                    "type": "string",
                    "title": "Email Tone",
                    "description": "Tone for the follow-up email",
                    "enum": ["professional", "friendly", "casual"],
                    "default": "professional"
                },
                "include_attachments": {
                    "type": "boolean",
                    "title": "Suggest Attachments",
                    "description": "Suggest relevant attachments based on meeting content",
                    "default": True
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "meeting_notes": {
                "type": "string", 
                "title": "Meeting Notes",
                "description": "Notes or summary from the meeting",
                "required": True
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "email_content": {"type": "object", "description": "Generated follow-up email"},
            "suggested_attachments": {"type": "array", "description": "Recommended attachments"},
            "send_timing": {"type": "object", "description": "Optimal send timing recommendations"}
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        return 0.008  # Fixed cost for email generation


# Register the node
NodeRegistry.register(
    "followup_writer",
    FollowupWriterNode,
    FollowupWriterNode().get_metadata(),
)