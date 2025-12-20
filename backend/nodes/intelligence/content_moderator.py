"""
Content Moderator Node - AI reviews text/images for policy violations

This node analyzes content for:
- Inappropriate language/hate speech
- Spam detection
- PII (Personal Identifiable Information)
- Content quality assessment
- Compliance with content policies
"""

import re
import json
from typing import Any, Dict, Optional, List
from backend.nodes.base import BaseNode
from backend.core.exceptions import NodeExecutionError, NodeValidationError
from backend.core.node_registry import NodeRegistry


class ContentModeratorNode(BaseNode):
    node_type = "content_moderator"
    name = "Content Moderator"
    description = "AI reviews text and images for policy violations and content quality"
    category = "intelligence"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute content moderation analysis"""
        try:
            await self.stream_progress("content_moderator", 0.1, "Initializing content moderation...")

            # Get inputs - accept multiple field names for flexibility
            content = (
                inputs.get("content") or 
                inputs.get("text") or 
                inputs.get("output") or
                ""
            )
            content_type = inputs.get("content_type") or config.get("content_type", "text")
            moderation_level = config.get("moderation_level", "standard")
            check_categories = config.get("check_categories", ["all"])
            custom_rules = config.get("custom_rules", [])

            if not content:
                raise NodeValidationError("Content input is required")

            await self.stream_progress("content_moderator", 0.3, "Analyzing content...")

            # Perform different types of moderation based on content type
            if content_type == "text":
                moderation_result = await self._moderate_text_content(
                    content, moderation_level, check_categories, custom_rules
                )
            elif content_type == "image":
                moderation_result = await self._moderate_image_content(
                    content, moderation_level, check_categories
                )
            else:
                raise NodeValidationError(f"Unsupported content type: {content_type}")

            await self.stream_progress("content_moderator", 0.8, "Generating recommendations...")

            # Generate action recommendations
            recommendations = self._generate_moderation_recommendations(moderation_result)

            result = {
                "moderation_result": moderation_result,
                "recommendations": recommendations,
                "content_metadata": {
                    "content_type": content_type,
                    "content_length": len(str(content)),
                    "moderation_level": moderation_level,
                    "timestamp": pd.Timestamp.now().isoformat() if 'pd' in globals() else "unknown"
                }
            }

            await self.stream_progress("content_moderator", 1.0, "Content moderation complete!")
            return result

        except Exception as e:
            raise NodeExecutionError(f"Content moderation failed: {str(e)}")

    async def _moderate_text_content(
        self, 
        text: str, 
        moderation_level: str, 
        check_categories: List[str],
        custom_rules: List[dict]
    ) -> Dict[str, Any]:
        """Moderate text content for various policy violations"""
        
        moderation_result = {
            "overall_score": 0.0,  # 0.0 = safe, 1.0 = definitely violates
            "is_safe": True,
            "violations": [],
            "warnings": [],
            "categories": {},
            "details": {}
        }

        # Check each category if requested
        if "all" in check_categories:
            categories_to_check = [
                "inappropriate_language", "hate_speech", "spam", 
                "pii", "violence", "harassment", "adult_content"
            ]
        else:
            categories_to_check = check_categories

        total_score = 0.0
        category_count = len(categories_to_check)

        for category in categories_to_check:
            category_result = await self._check_text_category(text, category, moderation_level)
            moderation_result["categories"][category] = category_result
            total_score += category_result["score"]

            # Add violations and warnings
            if category_result["violations"]:
                moderation_result["violations"].extend(category_result["violations"])
            if category_result["warnings"]:
                moderation_result["warnings"].extend(category_result["warnings"])

        # Calculate overall score
        moderation_result["overall_score"] = total_score / category_count if category_count > 0 else 0.0

        # Apply custom rules
        custom_violations = self._apply_custom_rules(text, custom_rules)
        if custom_violations:
            moderation_result["violations"].extend(custom_violations)
            moderation_result["overall_score"] = min(1.0, moderation_result["overall_score"] + 0.2)

        # Determine if content is safe based on moderation level
        threshold = self._get_safety_threshold(moderation_level)
        moderation_result["is_safe"] = moderation_result["overall_score"] < threshold

        return moderation_result

    async def _check_text_category(self, text: str, category: str, moderation_level: str) -> Dict[str, Any]:
        """Check text for specific category violations"""
        result = {
            "score": 0.0,
            "violations": [],
            "warnings": [],
            "matches": []
        }

        text_lower = text.lower()

        if category == "inappropriate_language":
            profanity_patterns = [
                r'\b(damn|hell|crap|suck|stupid|idiot|moron)\b',
                r'\b(f[u*]+ck|sh[i*]+t|b[i*]+tch|a[s*]+s|p[i*]+ss)\b',
                # Add more patterns as needed
            ]
            
            for pattern in profanity_patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    severity = 0.3 if any(c in pattern for c in ['*', '+']) else 0.6
                    result["score"] = max(result["score"], severity)
                    result["matches"].extend(matches)
                    
                    if severity > 0.5:
                        result["violations"].append({
                            "type": "profanity",
                            "severity": "high",
                            "matches": matches
                        })
                    else:
                        result["warnings"].append({
                            "type": "mild_profanity",
                            "matches": matches
                        })

        elif category == "hate_speech":
            hate_indicators = [
                r'\b(hate|kill|die|destroy)\s+(all\s+)?(jews|muslims|christians|blacks|whites|gays|women|men)\b',
                r'\b(terrorist|nazi|supremacist)\b',
                # Add more sophisticated hate speech detection
            ]
            
            for pattern in hate_indicators:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    result["score"] = 0.9
                    result["violations"].append({
                        "type": "hate_speech",
                        "severity": "critical",
                        "pattern": pattern
                    })

        elif category == "spam":
            spam_indicators = [
                r'(click here|buy now|limited time|act now|free money)',
                r'(www\.|http|\.com|\.net|\.org).*?(buy|sale|discount)',
                r'(urgent|immediate|guaranteed|100%\s+free)',
                r'(\$\d+|\d+%\s+off|prize|winner|congratulations)'
            ]
            
            spam_score = 0
            for pattern in spam_indicators:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                spam_score += matches * 0.2
            
            result["score"] = min(1.0, spam_score)
            if spam_score > 0.6:
                result["violations"].append({
                    "type": "spam",
                    "severity": "high",
                    "score": spam_score
                })
            elif spam_score > 0.3:
                result["warnings"].append({
                    "type": "potential_spam",
                    "score": spam_score
                })

        elif category == "pii":
            pii_patterns = [
                (r'\b\d{3}-\d{2}-\d{4}\b', 'ssn'),  # SSN
                (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', 'credit_card'),  # Credit card
                (r'\b[\w\.-]+@[\w\.-]+\.\w+\b', 'email'),  # Email
                (r'\b\(\d{3}\)\s*\d{3}-\d{4}\b|\b\d{3}-\d{3}-\d{4}\b', 'phone'),  # Phone
            ]
            
            for pattern, pii_type in pii_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    result["score"] = max(result["score"], 0.7)
                    result["violations"].append({
                        "type": "pii_detected",
                        "pii_type": pii_type,
                        "count": len(matches),
                        "severity": "high"
                    })

        elif category == "violence":
            violence_keywords = [
                r'\b(kill|murder|assault|attack|bomb|weapon|gun|knife|violence)\b',
                r'\b(hurt|harm|damage|destroy|beat|fight|war)\b'
            ]
            
            violence_score = 0
            for pattern in violence_keywords:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                violence_score += matches * 0.15
            
            result["score"] = min(1.0, violence_score)
            if violence_score > 0.5:
                result["violations"].append({
                    "type": "violent_content",
                    "severity": "medium",
                    "score": violence_score
                })

        return result

    async def _moderate_image_content(
        self, 
        image_data: Any, 
        moderation_level: str, 
        check_categories: List[str]
    ) -> Dict[str, Any]:
        """Moderate image content (placeholder for future AI vision integration)"""
        
        # This would integrate with image moderation APIs like:
        # - AWS Rekognition
        # - Google Vision AI
        # - Azure Content Moderator
        # - Custom vision models
        
        moderation_result = {
            "overall_score": 0.0,
            "is_safe": True,
            "violations": [],
            "warnings": [],
            "categories": {
                "adult_content": {"score": 0.0, "detected": False},
                "violence": {"score": 0.0, "detected": False},
                "inappropriate": {"score": 0.0, "detected": False}
            },
            "details": {
                "message": "Image moderation requires AI vision integration",
                "supported": False
            }
        }

        return moderation_result

    def _apply_custom_rules(self, text: str, custom_rules: List[dict]) -> List[dict]:
        """Apply custom moderation rules defined by the user"""
        violations = []
        
        for rule in custom_rules:
            rule_type = rule.get("type", "keyword")
            pattern = rule.get("pattern", "")
            action = rule.get("action", "warn")
            
            if rule_type == "keyword":
                if pattern.lower() in text.lower():
                    violation = {
                        "type": "custom_rule",
                        "rule_name": rule.get("name", "Custom Rule"),
                        "pattern": pattern,
                        "action": action,
                        "severity": "custom"
                    }
                    violations.append(violation)
            
            elif rule_type == "regex":
                try:
                    if re.search(pattern, text, re.IGNORECASE):
                        violation = {
                            "type": "custom_regex",
                            "rule_name": rule.get("name", "Custom Regex"),
                            "pattern": pattern,
                            "action": action,
                            "severity": "custom"
                        }
                        violations.append(violation)
                except re.error:
                    # Invalid regex pattern
                    pass
        
        return violations

    def _get_safety_threshold(self, moderation_level: str) -> float:
        """Get safety threshold based on moderation level"""
        thresholds = {
            "strict": 0.2,
            "standard": 0.5,
            "relaxed": 0.8
        }
        return thresholds.get(moderation_level, 0.5)

    def _generate_moderation_recommendations(self, moderation_result: Dict[str, Any]) -> List[dict]:
        """Generate action recommendations based on moderation results"""
        recommendations = []
        
        if not moderation_result["is_safe"]:
            recommendations.append({
                "action": "block_content",
                "reason": "Content violates policy",
                "priority": "high",
                "violations": moderation_result["violations"]
            })
        
        if moderation_result["warnings"]:
            recommendations.append({
                "action": "review_manually",
                "reason": "Content has potential issues",
                "priority": "medium",
                "warnings": moderation_result["warnings"]
            })
        
        # PII-specific recommendations
        pii_violations = [v for v in moderation_result["violations"] if v.get("type") == "pii_detected"]
        if pii_violations:
            recommendations.append({
                "action": "redact_pii",
                "reason": "Personal information detected",
                "priority": "high",
                "details": pii_violations
            })
        
        # Spam-specific recommendations
        spam_violations = [v for v in moderation_result["violations"] if v.get("type") == "spam"]
        if spam_violations:
            recommendations.append({
                "action": "mark_as_spam",
                "reason": "Content appears to be spam",
                "priority": "medium"
            })
        
        return recommendations

    def get_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        return {
            "type": "object",
            "properties": {
                "moderation_level": {
                    "type": "string",
                    "title": "Moderation Level",
                    "description": "Strictness of content moderation",
                    "enum": ["strict", "standard", "relaxed"],
                    "default": "standard"
                },
                "check_categories": {
                    "type": "array",
                    "title": "Check Categories",
                    "description": "Categories to check for violations",
                    "items": {
                        "type": "string",
                        "enum": [
                            "all", "inappropriate_language", "hate_speech", 
                            "spam", "pii", "violence", "harassment", "adult_content"
                        ]
                    },
                    "default": ["all"]
                },
                "custom_rules": {
                    "type": "array",
                    "title": "Custom Rules",
                    "description": "Custom moderation rules",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string", "enum": ["keyword", "regex"]},
                            "pattern": {"type": "string"},
                            "action": {"type": "string", "enum": ["warn", "block"]}
                        }
                    },
                    "default": []
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        """Define expected inputs"""
        return {
            "content": {
                "type": "any",
                "title": "Content to Moderate",
                "description": "Text or image content to analyze",
                "required": True
            },
            "content_type": {
                "type": "string",
                "title": "Content Type",
                "description": "Type of content being moderated",
                "enum": ["text", "image"],
                "default": "text"
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Define expected outputs"""
        return {
            "moderation_result": {
                "type": "object",
                "description": "Detailed moderation analysis results"
            },
            "recommendations": {
                "type": "array",
                "description": "Recommended actions based on moderation results"
            },
            "content_metadata": {
                "type": "object",
                "description": "Metadata about the moderated content"
            }
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        """Estimate cost based on content size and complexity"""
        content = inputs.get("content", "")
        content_type = inputs.get("content_type", "text")
        
        # Base cost for moderation
        if content_type == "text":
            # Text moderation is cheaper
            base_cost = 0.001
            size_cost = len(str(content)) / 1000 * 0.0005
        else:
            # Image moderation typically costs more (API calls)
            base_cost = 0.01
            size_cost = 0.005  # Flat additional cost for images
        
        return base_cost + size_cost


# Register the node
NodeRegistry.register(
    "content_moderator",
    ContentModeratorNode,
    ContentModeratorNode().get_metadata(),
)