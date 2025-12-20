"""
Social Post Scheduler Node - One idea → optimized posts for all platforms
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeExecutionError, NodeValidationError
from backend.core.node_registry import NodeRegistry


class SocialSchedulerNode(BaseNode, LLMConfigMixin):
    node_type = "social_scheduler"
    name = "Social Post Scheduler"
    description = "Creates optimized posts for multiple social platforms from one idea"
    category = "content"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute social post generation with LLM support"""
        try:
            # Get inputs - accept multiple field names
            content_idea = (
                inputs.get("content_idea") or
                inputs.get("idea") or
                inputs.get("text") or
                inputs.get("content") or
                inputs.get("output") or
                ""
            )
            platforms = config.get("platforms", ["twitter", "linkedin"])
            schedule_time = config.get("schedule_time", "")
            
            if not content_idea:
                raise NodeValidationError("Content idea is required. Connect a text_input node or provide content_idea in config.")

            # Try to use LLM if available
            use_llm = False
            llm_config = None
            
            try:
                llm_config = self._resolve_llm_config(config)
                if llm_config.get("api_key"):
                    use_llm = True
            except Exception:
                use_llm = False

            # Generate platform-specific posts
            scheduled_posts = []
            
            for platform in platforms:
                if use_llm and llm_config:
                    try:
                        post_data = await self._create_llm_platform_post(content_idea, platform, llm_config)
                        scheduled_posts.append({
                            "platform": platform,
                            "content": post_data.get("content", ""),
                            "scheduled_time": schedule_time or (datetime.now() + timedelta(hours=1)).isoformat(),
                            "hashtags": post_data.get("hashtags", [])
                        })
                    except Exception as e:
                        # Fallback to pattern-based if LLM fails
                        await self.stream_log("social_scheduler", f"LLM post generation failed for {platform}, using pattern matching: {e}", "warning")
                        post = self._create_platform_post(content_idea, platform)
                        scheduled_posts.append({
                            "platform": platform,
                            "content": post,
                            "scheduled_time": schedule_time or (datetime.now() + timedelta(hours=1)).isoformat(),
                            "hashtags": self._generate_hashtags(content_idea, platform)
                        })
                else:
                    # Use pattern-based fallback
                    post = self._create_platform_post(content_idea, platform)
                    scheduled_posts.append({
                        "platform": platform,
                        "content": post,
                        "scheduled_time": schedule_time or (datetime.now() + timedelta(hours=1)).isoformat(),
                        "hashtags": self._generate_hashtags(content_idea, platform)
                    })

            return {
                "scheduled_posts": scheduled_posts,
                "total_posts": len(scheduled_posts),
                "scheduling_summary": f"Created {len(scheduled_posts)} posts across {len(platforms)} platforms"
            }
        except Exception as e:
            raise NodeExecutionError(f"Social post generation failed: {str(e)}")

    def _create_platform_post(self, idea: str, platform: str) -> str:
        """Create platform-optimized post content"""
        
        platform_styles = {
            "twitter": f"💡 {idea}\n\nWhat do you think? #innovation",
            "linkedin": f"Excited to share insights on {idea}.\n\nIn today's market, this approach can drive real results.\n\nThoughts?",
            "facebook": f"Here's an interesting perspective on {idea}!\n\nWe'd love to hear your experiences with this.",
            "instagram": f"✨ {idea} ✨\n\n#inspiration #business #growth"
        }
        
        return platform_styles.get(platform, idea)

    def _generate_hashtags(self, content: str, platform: str) -> List[str]:
        """Generate platform-appropriate hashtags"""
        
        base_tags = ["#innovation", "#business", "#growth"]
        
        platform_tags = {
            "twitter": ["#tech", "#startup"],
            "linkedin": ["#professional", "#leadership"], 
            "instagram": ["#inspiration", "#motivation"],
            "facebook": ["#community", "#discussion"]
        }
        
        return base_tags + platform_tags.get(platform, [])

    async def _create_llm_platform_post(
        self,
        content_idea: str,
        platform: str,
        llm_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create platform-optimized post using LLM"""
        
        platform_guidelines = {
            "twitter": "280 characters max, concise, engaging, use hashtags (2-3), can include emojis",
            "linkedin": "Professional tone, longer form (2-3 paragraphs), thought leadership, industry insights, 3-5 hashtags",
            "facebook": "Conversational, community-focused, can be longer, encourage engagement, 2-4 hashtags",
            "instagram": "Visual-first thinking, engaging captions, use emojis, 5-10 relevant hashtags, call-to-action"
        }
        
        guidelines = platform_guidelines.get(platform, "Engaging and platform-appropriate")
        
        prompt = f"""Create an optimized social media post for {platform} based on this content idea.

Content Idea: {content_idea}

Platform: {platform}
Guidelines: {guidelines}

Generate a post that:
1. Is optimized for {platform}'s audience and style
2. Follows platform best practices
3. Is engaging and shareable
4. Includes appropriate hashtags
5. Has a clear call-to-action (if appropriate)

Return as JSON object with:
- "content": The post text (ready to publish)
- "hashtags": Array of 3-10 relevant hashtags (without # symbol)
- "character_count": Number of characters
- "tone": The tone used (e.g., "professional", "casual", "engaging")

Make it authentic and platform-specific."""
        
        try:
            import json
            import re
            llm_response = await self._call_llm(prompt, llm_config, max_tokens=500)
            
            # Try to parse JSON
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                post_data = json.loads(json_match.group())
                # Ensure hashtags are formatted correctly
                hashtags = post_data.get("hashtags", [])
                if hashtags and isinstance(hashtags[0], str) and not hashtags[0].startswith("#"):
                    hashtags = [f"#{tag}" if not tag.startswith("#") else tag for tag in hashtags]
                post_data["hashtags"] = hashtags
                return post_data
            else:
                # Fallback to pattern-based
                return {
                    "content": self._create_platform_post(content_idea, platform),
                    "hashtags": self._generate_hashtags(content_idea, platform)
                }
        except Exception:
            return {
                "content": self._create_platform_post(content_idea, platform),
                "hashtags": self._generate_hashtags(content_idea, platform)
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
                    "description": "Social media platforms to create posts for",
                    "items": {"type": "string", "enum": ["twitter", "linkedin", "facebook", "instagram"]},
                    "default": ["twitter", "linkedin"]
                },
                "schedule_time": {
                    "type": "string",
                    "title": "Schedule Time",
                    "description": "When to schedule the posts (ISO format)",
                    "format": "date-time"
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "content_idea": {
                "type": "string",
                "title": "Content Idea",
                "description": "Main idea or message to share across platforms",
                "required": True
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "scheduled_posts": {"type": "array", "description": "Platform-optimized posts"},
            "total_posts": {"type": "integer", "description": "Number of posts created"}
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        platforms = config.get("platforms", [])
        return 0.01 + (len(platforms) * 0.005)  # Base cost + per-platform cost


# Register the node
NodeRegistry.register(
    "social_scheduler",
    SocialSchedulerNode,
    SocialSchedulerNode().get_metadata(),
)
