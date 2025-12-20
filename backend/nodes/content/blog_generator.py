"""
Blog Post Generator Node - Topic → full SEO-optimized post

This node generates complete blog posts with:
- SEO-optimized headlines and content
- Meta descriptions and tags
- Internal linking suggestions
- Content structure optimization
- Keyword integration
"""

from datetime import datetime
from typing import Any, Dict, List
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeExecutionError, NodeValidationError
from backend.core.node_registry import NodeRegistry


class BlogGeneratorNode(BaseNode, LLMConfigMixin):
    node_type = "blog_generator"
    name = "Blog Post Generator"
    description = "Generates SEO-optimized blog posts from topics"
    category = "content"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute blog post generation"""
        try:
            await self.stream_progress("blog_generator", 0.1, "Initializing LLM configuration...")

            # Accept multiple input field names for flexibility
            topic = (
                inputs.get("topic") or 
                inputs.get("text") or 
                inputs.get("content") or 
                inputs.get("output") or
                ""
            )
            target_keywords = config.get("target_keywords", [])
            content_length = config.get("content_length", "medium")
            tone = config.get("tone", "professional")

            if not topic:
                raise NodeValidationError("Topic is required. Connect a text_input node or provide topic in config.")

            await self.stream_progress("blog_generator", 0.2, "Configuring AI model...")

            # Resolve LLM configuration
            llm_config = self._resolve_llm_config(config)

            await self.stream_progress("blog_generator", 0.4, "Researching topic and generating structure...")

            # Generate blog content using AI
            blog_content = await self._generate_blog_content_ai(
                topic, target_keywords, content_length, tone, llm_config
            )
            
            await self.stream_progress("blog_generator", 0.8, "Generating SEO elements...")

            # Generate SEO elements using AI
            seo_elements = await self._generate_seo_elements_ai(
                topic, target_keywords, blog_content, llm_config
            )

            await self.stream_progress("blog_generator", 0.95, "Finalizing content...")

            result = {
                "blog_post": blog_content,
                "seo_elements": seo_elements,
                "metadata": {
                    "word_count": len(blog_content.get("content", "").split()),
                    "generated_at": datetime.now().isoformat(),
                    "target_keywords": target_keywords,
                    "model_used": f"{llm_config['provider']}:{llm_config['model']}"
                }
            }

            # Estimate and track cost
            cost = self._estimate_llm_cost(
                self._get_total_prompt_text(topic, target_keywords, content_length, tone),
                str(result),
                llm_config
            )
            result["metadata"]["estimated_cost"] = cost

            await self.stream_progress("blog_generator", 1.0, "Blog post generated!")
            return result

        except Exception as e:
            raise NodeExecutionError(f"Blog generation failed: {str(e)}")

    async def _generate_blog_content_ai(
        self, topic: str, keywords: List[str], length: str, tone: str, llm_config: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate blog post content using AI"""
        
        length_mapping = {
            "short": "500-800 words",
            "medium": "1000-1500 words", 
            "long": "2000+ words"
        }
        
        word_count = length_mapping.get(length, "1000-1500 words")
        keywords_text = ", ".join(keywords) if keywords else "relevant keywords"
        
        prompt = f"""Write a comprehensive blog post about "{topic}" with the following requirements:

Content Requirements:
- Target length: {word_count}
- Writing tone: {tone}
- Target keywords to naturally include: {keywords_text}
- SEO-optimized structure with clear headings

Structure the response as a JSON object with these exact keys:
- "title": A compelling, SEO-optimized title
- "introduction": An engaging introduction (2-3 paragraphs)
- "content": The main body content with proper headings and sections
- "conclusion": A strong conclusion that summarizes key points
- "call_to_action": A compelling call-to-action

Guidelines:
- Write in {tone} tone
- Include actionable insights and practical advice
- Use clear headings (H2, H3) throughout the content
- Naturally incorporate the target keywords: {keywords_text}
- Ensure the content is valuable and engaging for readers
- Include specific examples where relevant

Please generate only the JSON object with the blog post content."""

        try:
            response = await self._call_llm(prompt, llm_config, max_tokens=3000)
            
            # Try to parse JSON response
            import json
            try:
                blog_content = json.loads(response)
                # Ensure all required keys are present
                required_keys = ["title", "introduction", "content", "conclusion", "call_to_action"]
                for key in required_keys:
                    if key not in blog_content:
                        blog_content[key] = f"[Generated {key} for {topic}]"
                return blog_content
            except json.JSONDecodeError:
                # Fallback: parse the response manually or return structured format
                return {
                    "title": f"The Complete Guide to {topic}: Everything You Need to Know",
                    "introduction": response[:300] + "..." if len(response) > 300 else response,
                    "content": response,
                    "conclusion": f"Understanding {topic} is crucial for success. Implement these strategies to see results.",
                    "call_to_action": "Ready to get started? Contact us today for expert guidance."
                }
        except Exception as e:
            # Fallback content if AI generation fails
            return {
                "title": f"The Complete Guide to {topic}: Everything You Need to Know",
                "introduction": f"In this comprehensive guide, we'll explore {topic} and provide actionable insights for {tone} readers.",
                "content": f"[AI-generated {word_count} blog post about {topic} with keywords: {keywords_text}. Error: {str(e)}]",
                "conclusion": f"Understanding {topic} is crucial for success. Implement these strategies to see results.",
                "call_to_action": "Ready to get started? Contact us today for expert guidance."
            }

    async def _generate_seo_elements_ai(
        self, topic: str, keywords: List[str], blog_content: Dict[str, str], llm_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate SEO optimization elements using AI"""
        
        title = blog_content.get("title", topic)
        content_preview = blog_content.get("content", "")[:500]
        keywords_text = ", ".join(keywords) if keywords else "relevant keywords"
        
        prompt = f"""Generate SEO elements for a blog post with the following details:

Title: {title}
Topic: {topic}
Target Keywords: {keywords_text}
Content Preview: {content_preview}...

Generate a JSON object with these SEO elements:
- "meta_description": A compelling 150-160 character meta description
- "meta_keywords": Array of 5 most relevant keywords
- "slug": URL-friendly slug (lowercase, hyphens instead of spaces)
- "internal_links": Array of 3 internal link suggestions
- "header_tags": Object with "h1" (main title) and "h2_suggestions" (array of 4-5 H2 heading suggestions)

Guidelines:
- Meta description should be compelling and include primary keywords
- Slug should be SEO-friendly and readable
- Internal links should be contextually relevant
- H2 suggestions should create a logical content flow

Please generate only the JSON object."""

        try:
            response = await self._call_llm(prompt, llm_config, max_tokens=1000)
            
            import json
            try:
                seo_elements = json.loads(response)
                # Ensure all required keys are present with fallbacks
                if "meta_description" not in seo_elements:
                    seo_elements["meta_description"] = f"Learn everything about {topic}. Expert guide with actionable tips and strategies."
                if "meta_keywords" not in seo_elements:
                    seo_elements["meta_keywords"] = keywords[:5] if keywords else [topic.lower()]
                if "slug" not in seo_elements:
                    seo_elements["slug"] = topic.lower().replace(" ", "-").replace("'", "")
                if "internal_links" not in seo_elements:
                    seo_elements["internal_links"] = [f"Related: How to optimize {topic}", f"See also: Best practices for {topic}"]
                if "header_tags" not in seo_elements:
                    seo_elements["header_tags"] = {
                        "h1": title,
                        "h2_suggestions": [f"What is {topic}?", f"Benefits of {topic}", f"How to implement {topic}", "Best practices and tips"]
                    }
                
                return seo_elements
            except json.JSONDecodeError:
                # Fallback SEO elements
                return self._generate_fallback_seo_elements(topic, keywords, title)
        except Exception:
            return self._generate_fallback_seo_elements(topic, keywords, title)

    def _generate_fallback_seo_elements(self, topic: str, keywords: List[str], title: str) -> Dict[str, Any]:
        """Generate fallback SEO elements if AI generation fails"""
        return {
            "meta_description": f"Learn everything about {topic}. Expert guide with actionable tips and strategies.",
            "meta_keywords": keywords[:5] if keywords else [topic.lower()],
            "slug": topic.lower().replace(" ", "-").replace("'", ""),
            "internal_links": [
                f"Related: How to optimize {topic}",
                f"See also: Best practices for {topic}",
                f"Learn more: Advanced {topic} strategies"
            ],
            "header_tags": {
                "h1": title,
                "h2_suggestions": [
                    f"What is {topic}?",
                    f"Benefits of {topic}", 
                    f"How to implement {topic}",
                    "Best practices and tips",
                    f"Common {topic} mistakes to avoid"
                ]
            }
        }

    def _get_total_prompt_text(self, topic: str, keywords: List[str], length: str, tone: str) -> str:
        """Get total prompt text for cost estimation"""
        keywords_text = ", ".join(keywords) if keywords else ""
        return f"Blog post about {topic} with keywords {keywords_text} in {tone} tone, length: {length}"

    def get_schema(self) -> Dict[str, Any]:
        # Get LLM configuration from mixin
        llm_schema = self._get_llm_schema_section()
        
        return {
            "type": "object",
            "properties": {
                **llm_schema,  # Include LLM configuration
                "target_keywords": {
                    "type": "array",
                    "title": "Target Keywords",
                    "description": "SEO keywords to naturally incorporate in the content",
                    "items": {"type": "string"},
                    "default": []
                },
                "content_length": {
                    "type": "string",
                    "title": "Content Length",
                    "description": "Target length for the blog post",
                    "enum": ["short", "medium", "long"],
                    "default": "medium"
                },
                "tone": {
                    "type": "string",
                    "title": "Writing Tone",
                    "description": "Tone and style for the content",
                    "enum": ["professional", "casual", "technical", "friendly", "conversational"],
                    "default": "professional"
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "topic": {
                "type": "string",
                "title": "Blog Topic",
                "description": "Main topic or subject for the blog post",
                "required": True
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "blog_post": {"type": "object", "description": "Generated blog post content"},
            "seo_elements": {"type": "object", "description": "SEO optimization elements"},
            "metadata": {"type": "object", "description": "Generation metadata"}
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        """Estimate cost based on content length and LLM usage"""
        topic = inputs.get("topic", "")
        keywords = config.get("target_keywords", [])
        length = config.get("content_length", "medium")
        tone = config.get("tone", "professional")
        
        # Estimate prompt and response lengths
        prompt_text = self._get_total_prompt_text(topic, keywords, length, tone)
        
        # Estimate response length based on content length
        response_lengths = {
            "short": 800,    # ~800 words
            "medium": 1500,  # ~1500 words  
            "long": 2500     # ~2500 words
        }
        estimated_response_words = response_lengths.get(length, 1500)
        
        # Convert to approximate tokens (1 word ≈ 1.3 tokens)
        prompt_tokens = len(prompt_text.split()) * 1.3
        response_tokens = estimated_response_words * 1.3
        
        # Base cost using LLM pricing (will be more accurate with actual provider)
        base_cost = (prompt_tokens + response_tokens) / 1000 * 0.01  # Rough estimate
        
        return base_cost


# Register the node
NodeRegistry.register(
    "blog_generator",
    BlogGeneratorNode,
    BlogGeneratorNode().get_metadata(),
)
