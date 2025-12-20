"""
Lead Scorer Node - AI analyzes customer data and assigns priority scores

This node evaluates leads based on multiple factors and provides:
- Lead quality score (0-100)
- Priority classification (hot/warm/cold)
- Conversion probability
- Recommended actions
- Key insights about the lead
"""

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeExecutionError, NodeValidationError
from backend.core.node_registry import NodeRegistry


class LeadScorerNode(BaseNode, LLMConfigMixin):
    node_type = "lead_scorer"
    name = "Lead Scorer"
    description = "AI analyzes customer data and assigns intelligent priority scores"
    category = "intelligence"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute lead scoring analysis"""
        try:
            await self.stream_progress("lead_scorer", 0.1, "Initializing lead analysis...")

            # Get inputs - accept multiple formats
            # Can receive as dict from JSON, or parse from text/JSON string
            lead_data_raw = (
                inputs.get("lead_data") or 
                inputs.get("data") or 
                inputs.get("text") or 
                inputs.get("content") or
                inputs.get("output") or
                {}
            )
            
            # Parse if it's a string (JSON or text)
            if isinstance(lead_data_raw, str):
                try:
                    lead_data = json.loads(lead_data_raw)
                except json.JSONDecodeError:
                    # If not JSON, treat as simple text and create basic lead data
                    lead_data = {"description": lead_data_raw, "source": "text_input"}
            elif isinstance(lead_data_raw, dict):
                lead_data = lead_data_raw
            else:
                lead_data = {}
            
            scoring_model = config.get("scoring_model", "comprehensive")
            weight_adjustments = config.get("weight_adjustments", {})
            include_recommendations = config.get("include_recommendations", True)
            industry = config.get("industry", "general")

            if not lead_data:
                raise NodeValidationError("Lead data is required. Connect a text_input node with JSON data or provide lead_data in config.")

            await self.stream_progress("lead_scorer", 0.3, "Analyzing lead characteristics...")

            # Normalize lead data
            normalized_data = self._normalize_lead_data(lead_data)
            
            await self.stream_progress("lead_scorer", 0.5, "Calculating scoring factors...")

            # Calculate various scoring factors
            scoring_factors = await self._calculate_scoring_factors(
                normalized_data, scoring_model, industry
            )

            await self.stream_progress("lead_scorer", 0.7, "Computing final score...")

            # Calculate final score with weights
            final_score = self._calculate_weighted_score(scoring_factors, weight_adjustments)
            
            await self.stream_progress("lead_scorer", 0.9, "Generating insights and recommendations...")

            # Try to use LLM for better insights and recommendations if available
            use_llm = False
            llm_config = None
            
            try:
                llm_config = self._resolve_llm_config(config)
                if llm_config.get("api_key"):
                    use_llm = True
            except Exception:
                use_llm = False
            
            # Generate insights and recommendations
            if use_llm and llm_config:
                try:
                    insights = await self._generate_llm_insights(normalized_data, scoring_factors, final_score, industry, llm_config)
                    if include_recommendations:
                        recommendations = await self._generate_llm_recommendations(normalized_data, scoring_factors, final_score, industry, llm_config)
                    else:
                        recommendations = []
                except Exception as e:
                    # Fallback to pattern-based if LLM fails
                    await self.stream_log("lead_scorer", f"LLM generation failed, using pattern matching: {e}", "warning")
                    insights = self._generate_lead_insights(normalized_data, scoring_factors, final_score)
                    if include_recommendations:
                        recommendations = self._generate_recommendations(normalized_data, scoring_factors, final_score)
                    else:
                        recommendations = []
            else:
                # Use pattern-based fallback
                insights = self._generate_lead_insights(normalized_data, scoring_factors, final_score)
                if include_recommendations:
                    recommendations = self._generate_recommendations(normalized_data, scoring_factors, final_score)
                else:
                    recommendations = []

            result = {
                "lead_score": final_score,
                "scoring_breakdown": scoring_factors,
                "lead_insights": insights,
                "recommendations": recommendations,
                "metadata": {
                    "scoring_model": scoring_model,
                    "industry": industry,
                    "scored_at": datetime.now().isoformat(),
                    "confidence_level": self._calculate_confidence_level(normalized_data)
                }
            }

            await self.stream_progress("lead_scorer", 1.0, "Lead scoring complete!")
            return result

        except Exception as e:
            raise NodeExecutionError(f"Lead scoring failed: {str(e)}")

    def _normalize_lead_data(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and clean lead data for scoring"""
        normalized = {
            # Contact Information
            "email": lead_data.get("email", "").lower().strip(),
            "phone": self._clean_phone(lead_data.get("phone", "")),
            "name": lead_data.get("name", "").strip(),
            
            # Company Information
            "company": lead_data.get("company", "").strip(),
            "company_size": self._normalize_company_size(lead_data.get("company_size", "")),
            "industry": lead_data.get("industry", "").lower().strip(),
            "revenue": self._normalize_revenue(lead_data.get("revenue", "")),
            
            # Professional Information
            "title": lead_data.get("title", "").strip(),
            "seniority_level": self._determine_seniority(lead_data.get("title", "")),
            
            # Behavioral Data
            "website_visits": int(lead_data.get("website_visits", 0)),
            "email_opens": int(lead_data.get("email_opens", 0)),
            "email_clicks": int(lead_data.get("email_clicks", 0)),
            "content_downloads": int(lead_data.get("content_downloads", 0)),
            "demo_requests": int(lead_data.get("demo_requests", 0)),
            
            # Source and Campaign Data
            "lead_source": lead_data.get("lead_source", "unknown").lower(),
            "campaign": lead_data.get("campaign", "").lower(),
            "utm_source": lead_data.get("utm_source", "").lower(),
            
            # Timing Information
            "created_date": lead_data.get("created_date", datetime.now().isoformat()),
            "last_activity": lead_data.get("last_activity", ""),
            
            # Custom Fields
            "notes": lead_data.get("notes", ""),
            "tags": lead_data.get("tags", []),
            "custom_fields": lead_data.get("custom_fields", {})
        }
        
        return normalized

    def _clean_phone(self, phone: str) -> str:
        """Clean and normalize phone number"""
        if not phone:
            return ""
        # Remove all non-digit characters
        clean = re.sub(r'[^\d]', '', phone)
        return clean

    def _normalize_company_size(self, size_input: str) -> str:
        """Normalize company size to standard categories"""
        if not size_input:
            return "unknown"
        
        size_lower = size_input.lower().strip()
        
        # Extract numbers if present
        numbers = re.findall(r'\d+', size_input)
        if numbers:
            size_num = int(numbers[0])
            if size_num < 10:
                return "startup"
            elif size_num < 50:
                return "small"
            elif size_num < 250:
                return "medium"
            elif size_num < 1000:
                return "large"
            else:
                return "enterprise"
        
        # Handle text descriptions
        if any(term in size_lower for term in ['startup', '1-10', 'solo', 'freelance']):
            return "startup"
        elif any(term in size_lower for term in ['small', '11-50', '10-50']):
            return "small"
        elif any(term in size_lower for term in ['medium', '51-250', '50-250']):
            return "medium"
        elif any(term in size_lower for term in ['large', '251-1000', '250-1000']):
            return "large"
        elif any(term in size_lower for term in ['enterprise', '1000+', 'fortune']):
            return "enterprise"
        
        return "unknown"

    def _normalize_revenue(self, revenue_input: str) -> str:
        """Normalize revenue to standard brackets"""
        if not revenue_input:
            return "unknown"
        
        # Extract numbers (assuming USD)
        numbers = re.findall(r'[\d,]+', str(revenue_input))
        if numbers:
            # Remove commas and convert to int
            revenue_num = int(numbers[0].replace(',', ''))
            
            # Handle different units (K, M, B)
            revenue_str = str(revenue_input).upper()
            if 'K' in revenue_str:
                revenue_num *= 1000
            elif 'M' in revenue_str:
                revenue_num *= 1000000
            elif 'B' in revenue_str:
                revenue_num *= 1000000000
            
            # Categorize
            if revenue_num < 100000:
                return "under_100k"
            elif revenue_num < 1000000:
                return "100k_1m"
            elif revenue_num < 10000000:
                return "1m_10m"
            elif revenue_num < 100000000:
                return "10m_100m"
            else:
                return "over_100m"
        
        return "unknown"

    def _determine_seniority(self, title: str) -> str:
        """Determine seniority level from job title"""
        if not title:
            return "unknown"
        
        title_lower = title.lower()
        
        # C-level and senior executives
        if any(term in title_lower for term in ['ceo', 'cto', 'cfo', 'cmo', 'president', 'founder', 'owner']):
            return "executive"
        
        # VPs and Directors
        elif any(term in title_lower for term in ['vp', 'vice president', 'director', 'head of']):
            return "senior_management"
        
        # Managers
        elif any(term in title_lower for term in ['manager', 'lead', 'supervisor', 'team lead']):
            return "management"
        
        # Senior individual contributors
        elif any(term in title_lower for term in ['senior', 'sr.', 'principal', 'architect', 'specialist']):
            return "senior_ic"
        
        # Junior roles
        elif any(term in title_lower for term in ['junior', 'jr.', 'associate', 'intern', 'entry']):
            return "junior"
        
        # Default to mid-level
        return "mid_level"

    async def _calculate_scoring_factors(
        self, 
        lead_data: Dict[str, Any], 
        scoring_model: str, 
        industry: str
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate various scoring factors"""
        
        factors = {}
        
        # 1. Demographic Score (0-100)
        factors["demographic"] = self._score_demographic_fit(lead_data, industry)
        
        # 2. Firmographic Score (0-100) 
        factors["firmographic"] = self._score_firmographic_fit(lead_data, industry)
        
        # 3. Behavioral Score (0-100)
        factors["behavioral"] = self._score_behavioral_engagement(lead_data)
        
        # 4. Intent Score (0-100)
        factors["intent"] = self._score_purchase_intent(lead_data)
        
        # 5. Source Quality Score (0-100)
        factors["source_quality"] = self._score_lead_source(lead_data)
        
        # 6. Recency Score (0-100)
        factors["recency"] = self._score_recency(lead_data)
        
        # 7. Data Quality Score (0-100)
        factors["data_quality"] = self._score_data_completeness(lead_data)
        
        return factors

    def _score_demographic_fit(self, lead_data: Dict[str, Any], industry: str) -> Dict[str, Any]:
        """Score based on demographic fit"""
        score = 0
        details = {}
        
        # Seniority scoring
        seniority_scores = {
            "executive": 100,
            "senior_management": 85, 
            "management": 70,
            "senior_ic": 60,
            "mid_level": 45,
            "junior": 20,
            "unknown": 30
        }
        
        seniority = lead_data.get("seniority_level", "unknown")
        seniority_score = seniority_scores.get(seniority, 30)
        score += seniority_score * 0.6  # 60% weight
        details["seniority_score"] = seniority_score
        
        # Title relevance (simple keyword matching)
        title = lead_data.get("title", "").lower()
        relevant_titles = ["marketing", "sales", "business", "growth", "product", "tech"]
        title_relevance = sum(10 for keyword in relevant_titles if keyword in title)
        score += min(title_relevance, 40)  # Max 40 points, 40% weight
        details["title_relevance"] = min(title_relevance, 40)
        
        return {
            "score": min(score, 100),
            "details": details,
            "weight": 0.15  # 15% of total score
        }

    def _score_firmographic_fit(self, lead_data: Dict[str, Any], industry: str) -> Dict[str, Any]:
        """Score based on company characteristics"""
        score = 0
        details = {}
        
        # Company size scoring
        size_scores = {
            "enterprise": 100,
            "large": 85,
            "medium": 70,
            "small": 50,
            "startup": 30,
            "unknown": 25
        }
        
        company_size = lead_data.get("company_size", "unknown")
        size_score = size_scores.get(company_size, 25)
        score += size_score * 0.4  # 40% weight
        details["company_size_score"] = size_score
        
        # Revenue scoring
        revenue_scores = {
            "over_100m": 100,
            "10m_100m": 85,
            "1m_10m": 70,
            "100k_1m": 50,
            "under_100k": 25,
            "unknown": 30
        }
        
        revenue = lead_data.get("revenue", "unknown")
        revenue_score = revenue_scores.get(revenue, 30)
        score += revenue_score * 0.4  # 40% weight
        details["revenue_score"] = revenue_score
        
        # Industry relevance
        lead_industry = lead_data.get("industry", "")
        industry_score = 80 if lead_industry and industry != "general" else 50
        score += industry_score * 0.2  # 20% weight
        details["industry_score"] = industry_score
        
        return {
            "score": min(score, 100),
            "details": details,
            "weight": 0.25  # 25% of total score
        }

    def _score_behavioral_engagement(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score based on behavioral engagement"""
        score = 0
        details = {}
        
        # Website engagement
        visits = lead_data.get("website_visits", 0)
        visit_score = min(visits * 5, 40)  # 5 points per visit, max 40
        score += visit_score
        details["website_visits_score"] = visit_score
        
        # Email engagement  
        email_opens = lead_data.get("email_opens", 0)
        email_clicks = lead_data.get("email_clicks", 0)
        
        email_score = min((email_opens * 2) + (email_clicks * 5), 30)
        score += email_score
        details["email_engagement_score"] = email_score
        
        # Content engagement
        downloads = lead_data.get("content_downloads", 0)
        content_score = min(downloads * 8, 30)  # 8 points per download, max 30
        score += content_score
        details["content_engagement_score"] = content_score
        
        return {
            "score": min(score, 100),
            "details": details,
            "weight": 0.20  # 20% of total score
        }

    def _score_purchase_intent(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score based on purchase intent signals"""
        score = 0
        details = {}
        
        # Demo requests (very high intent)
        demo_requests = lead_data.get("demo_requests", 0)
        demo_score = min(demo_requests * 40, 80)  # 40 points per demo request
        score += demo_score
        details["demo_requests_score"] = demo_score
        
        # High-intent content downloads
        notes = lead_data.get("notes", "").lower()
        tags = [tag.lower() for tag in lead_data.get("tags", [])]
        
        high_intent_signals = ["pricing", "demo", "trial", "quote", "proposal", "purchase"]
        intent_signals = 0
        
        for signal in high_intent_signals:
            if signal in notes or signal in " ".join(tags):
                intent_signals += 1
        
        signal_score = min(intent_signals * 10, 20)
        score += signal_score
        details["intent_signals_score"] = signal_score
        
        return {
            "score": min(score, 100),
            "details": details,
            "weight": 0.20  # 20% of total score
        }

    def _score_lead_source(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score based on lead source quality"""
        source_scores = {
            "referral": 100,
            "organic": 90,
            "direct": 85,
            "paid_search": 75,
            "social": 60,
            "email": 65,
            "content": 70,
            "webinar": 80,
            "trade_show": 75,
            "paid_social": 55,
            "display": 40,
            "unknown": 30
        }
        
        lead_source = lead_data.get("lead_source", "unknown")
        score = source_scores.get(lead_source, 30)
        
        return {
            "score": score,
            "details": {"source": lead_source, "quality": score},
            "weight": 0.10  # 10% of total score
        }

    def _score_recency(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score based on recency of activities"""
        score = 50  # Default score
        details = {}
        
        try:
            # Parse creation date
            created_date = datetime.fromisoformat(lead_data.get("created_date", "").replace('Z', '+00:00'))
            days_old = (datetime.now() - created_date).days
            
            # Recency scoring - fresher leads get higher scores
            if days_old <= 1:
                score = 100
            elif days_old <= 7:
                score = 85
            elif days_old <= 30:
                score = 70
            elif days_old <= 90:
                score = 50
            else:
                score = 25
            
            details["days_old"] = days_old
            details["recency_category"] = self._get_recency_category(days_old)
            
        except:
            # If date parsing fails, use default score
            details["error"] = "Could not parse creation date"
        
        return {
            "score": score,
            "details": details,
            "weight": 0.05  # 5% of total score
        }

    def _get_recency_category(self, days_old: int) -> str:
        """Get recency category for days old"""
        if days_old <= 1:
            return "hot"
        elif days_old <= 7:
            return "warm"
        elif days_old <= 30:
            return "recent"
        elif days_old <= 90:
            return "aging"
        else:
            return "cold"

    def _score_data_completeness(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score based on data quality and completeness"""
        required_fields = ["email", "name", "company"]
        important_fields = ["phone", "title", "company_size", "industry"]
        optional_fields = ["revenue", "lead_source", "notes"]
        
        score = 0
        details = {}
        
        # Required fields (must have)
        required_score = 0
        for field in required_fields:
            if lead_data.get(field) and lead_data[field].strip():
                required_score += 1
        required_percentage = (required_score / len(required_fields)) * 60  # 60% max
        score += required_percentage
        details["required_fields_score"] = required_percentage
        
        # Important fields
        important_score = 0
        for field in important_fields:
            if lead_data.get(field) and lead_data[field] not in ["", "unknown"]:
                important_score += 1
        important_percentage = (important_score / len(important_fields)) * 30  # 30% max
        score += important_percentage
        details["important_fields_score"] = important_percentage
        
        # Optional fields
        optional_score = 0
        for field in optional_fields:
            if lead_data.get(field) and lead_data[field] not in ["", "unknown"]:
                optional_score += 1
        optional_percentage = (optional_score / len(optional_fields)) * 10  # 10% max
        score += optional_percentage
        details["optional_fields_score"] = optional_percentage
        
        return {
            "score": min(score, 100),
            "details": details,
            "weight": 0.05  # 5% of total score
        }

    def _calculate_weighted_score(
        self, 
        scoring_factors: Dict[str, Dict[str, Any]], 
        weight_adjustments: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate final weighted score"""
        
        total_score = 0
        total_weight = 0
        score_breakdown = {}
        
        for factor_name, factor_data in scoring_factors.items():
            factor_score = factor_data["score"]
            factor_weight = factor_data["weight"]
            
            # Apply weight adjustments if provided
            if factor_name in weight_adjustments:
                factor_weight = weight_adjustments[factor_name]
            
            weighted_score = factor_score * factor_weight
            total_score += weighted_score
            total_weight += factor_weight
            
            score_breakdown[factor_name] = {
                "raw_score": factor_score,
                "weight": factor_weight,
                "weighted_score": weighted_score,
                "details": factor_data.get("details", {})
            }
        
        # Normalize to 0-100 scale
        final_score = (total_score / total_weight) if total_weight > 0 else 0
        
        # Determine lead grade
        grade = self._determine_lead_grade(final_score)
        
        # Calculate conversion probability
        conversion_probability = self._calculate_conversion_probability(final_score, scoring_factors)
        
        return {
            "final_score": round(final_score, 1),
            "grade": grade,
            "conversion_probability": conversion_probability,
            "score_breakdown": score_breakdown,
            "total_weight_used": total_weight
        }

    def _determine_lead_grade(self, score: float) -> str:
        """Determine letter grade based on score"""
        if score >= 80:
            return "A"
        elif score >= 65:
            return "B"
        elif score >= 50:
            return "C"
        elif score >= 35:
            return "D"
        else:
            return "F"

    def _calculate_conversion_probability(
        self, 
        final_score: float, 
        scoring_factors: Dict[str, Dict[str, Any]]
    ) -> float:
        """Calculate probability of conversion based on score and factors"""
        
        # Base conversion probability from score
        base_probability = final_score / 100 * 0.6  # Max 60% from score
        
        # Boost from high-intent signals
        intent_score = scoring_factors.get("intent", {}).get("score", 0)
        intent_boost = (intent_score / 100) * 0.3  # Max 30% boost from intent
        
        # Boost from recent activity
        recency_score = scoring_factors.get("recency", {}).get("score", 0)
        recency_boost = (recency_score / 100) * 0.1  # Max 10% boost from recency
        
        total_probability = min(base_probability + intent_boost + recency_boost, 0.95)
        
        return round(total_probability, 3)

    def _generate_lead_insights(
        self, 
        lead_data: Dict[str, Any], 
        scoring_factors: Dict[str, Dict[str, Any]], 
        final_score: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate insights about the lead"""
        insights = []
        
        score = final_score["final_score"]
        grade = final_score["grade"]
        
        # Overall assessment
        if score >= 80:
            insights.append({
                "type": "overall",
                "message": f"Excellent lead with {grade} grade ({score}/100). High conversion potential.",
                "sentiment": "positive"
            })
        elif score >= 50:
            insights.append({
                "type": "overall", 
                "message": f"Good lead with {grade} grade ({score}/100). Moderate conversion potential.",
                "sentiment": "neutral"
            })
        else:
            insights.append({
                "type": "overall",
                "message": f"Lead needs nurturing with {grade} grade ({score}/100). Lower conversion potential.",
                "sentiment": "negative"
            })
        
        # Factor-specific insights
        for factor_name, factor_data in scoring_factors.items():
            factor_score = factor_data["score"]
            
            if factor_name == "behavioral" and factor_score > 70:
                insights.append({
                    "type": "strength",
                    "message": "High behavioral engagement indicates strong interest.",
                    "sentiment": "positive"
                })
            
            elif factor_name == "intent" and factor_score > 60:
                insights.append({
                    "type": "strength",
                    "message": "Strong purchase intent signals detected.",
                    "sentiment": "positive"
                })
            
            elif factor_name == "firmographic" and factor_score > 75:
                insights.append({
                    "type": "strength",
                    "message": "Company profile matches ideal customer characteristics.",
                    "sentiment": "positive"
                })
            
            elif factor_name == "data_quality" and factor_score < 60:
                insights.append({
                    "type": "warning",
                    "message": "Incomplete lead information may affect scoring accuracy.",
                    "sentiment": "warning"
                })
        
        return insights

    def _generate_recommendations(
        self, 
        lead_data: Dict[str, Any], 
        scoring_factors: Dict[str, Dict[str, Any]], 
        final_score: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate action recommendations for the lead"""
        recommendations = []
        
        score = final_score["final_score"]
        conversion_prob = final_score["conversion_probability"]
        
        # Primary action based on score
        if score >= 80:
            recommendations.append({
                "priority": "high",
                "action": "immediate_contact",
                "description": "Contact immediately via phone or personal email",
                "timing": "within 24 hours"
            })
        elif score >= 65:
            recommendations.append({
                "priority": "medium",
                "action": "personalized_outreach",
                "description": "Send personalized email with relevant case studies",
                "timing": "within 48 hours"
            })
        elif score >= 50:
            recommendations.append({
                "priority": "medium",
                "action": "nurture_sequence",
                "description": "Add to email nurture sequence with educational content",
                "timing": "within 1 week"
            })
        else:
            recommendations.append({
                "priority": "low",
                "action": "long_term_nurture",
                "description": "Include in long-term nurture campaigns",
                "timing": "ongoing"
            })
        
        # Specific recommendations based on factors
        intent_score = scoring_factors.get("intent", {}).get("score", 0)
        if intent_score > 60:
            recommendations.append({
                "priority": "high",
                "action": "demo_offer",
                "description": "Offer product demo or trial based on expressed interest",
                "timing": "immediate"
            })
        
        behavioral_score = scoring_factors.get("behavioral", {}).get("score", 0)
        if behavioral_score > 70:
            recommendations.append({
                "priority": "medium",
                "action": "content_follow_up",
                "description": "Send follow-up content based on previous engagement",
                "timing": "within 3 days"
            })
        
        data_quality_score = scoring_factors.get("data_quality", {}).get("score", 0)
        if data_quality_score < 60:
            recommendations.append({
                "priority": "low",
                "action": "data_enrichment",
                "description": "Gather additional lead information through forms or research",
                "timing": "ongoing"
            })
        
        return recommendations

    async def _generate_llm_insights(
        self,
        lead_data: Dict[str, Any],
        scoring_factors: Dict[str, Dict[str, Any]],
        final_score: Dict[str, Any],
        industry: str,
        llm_config: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate insights using LLM for better quality"""
        
        # Prepare lead data summary
        lead_summary = f"""
Lead Information:
- Name: {lead_data.get('name', 'N/A')}
- Company: {lead_data.get('company', 'N/A')}
- Title: {lead_data.get('title', 'N/A')}
- Industry: {lead_data.get('industry', 'N/A')}
- Company Size: {lead_data.get('company_size', 'N/A')}
- Lead Source: {lead_data.get('lead_source', 'N/A')}
- Behavioral Activity: {lead_data.get('website_visits', 0)} visits, {lead_data.get('email_opens', 0)} email opens
- Notes: {lead_data.get('notes', 'None')}
"""
        
        score = final_score["final_score"]
        grade = final_score["grade"]
        conversion_prob = final_score["conversion_probability"]
        
        # Build scoring summary
        scoring_summary = f"""
Scoring Results:
- Final Score: {score}/100 (Grade: {grade})
- Conversion Probability: {conversion_prob:.1%}
- Scoring Factors:
"""
        for factor_name, factor_data in scoring_factors.items():
            factor_score = factor_data.get("score", 0)
            scoring_summary += f"  - {factor_name}: {factor_score}/100\n"
        
        prompt = f"""Analyze this lead and provide 3-5 key insights about their potential value and characteristics.

{lead_summary}

{scoring_summary}

Industry Context: {industry}

Provide insights in JSON format as an array of objects, each with:
- "type": "strength" | "warning" | "opportunity" | "risk"
- "message": Brief insight message
- "sentiment": "positive" | "negative" | "neutral" | "warning"

Focus on actionable insights that help sales teams understand the lead better."""
        
        try:
            llm_response = await self._call_llm(prompt, llm_config, max_tokens=1000)
            
            # Try to parse JSON from response
            import re
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                insights = json.loads(json_match.group())
                return insights
            else:
                # Fallback: parse as text
                return self._parse_insights_from_text(llm_response)
        except Exception as e:
            await self.stream_log("lead_scorer", f"LLM insights parsing failed: {e}", "warning")
            # Fallback to pattern-based
            return self._generate_lead_insights(lead_data, scoring_factors, final_score)

    async def _generate_llm_recommendations(
        self,
        lead_data: Dict[str, Any],
        scoring_factors: Dict[str, Dict[str, Any]],
        final_score: Dict[str, Any],
        industry: str,
        llm_config: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate recommendations using LLM for better quality"""
        
        score = final_score["final_score"]
        conversion_prob = final_score["conversion_probability"]
        
        prompt = f"""Based on this lead scoring analysis, provide 3-5 specific action recommendations.

Lead Score: {score}/100
Conversion Probability: {conversion_prob:.1%}
Industry: {industry}

Scoring Factors:
"""
        for factor_name, factor_data in scoring_factors.items():
            factor_score = factor_data.get("score", 0)
            prompt += f"- {factor_name}: {factor_score}/100\n"
        
        prompt += f"""
Lead Details:
- Company: {lead_data.get('company', 'N/A')}
- Title: {lead_data.get('title', 'N/A')}
- Behavioral Activity: {lead_data.get('website_visits', 0)} visits, {lead_data.get('email_opens', 0)} email opens

Provide recommendations in JSON format as an array of objects, each with:
- "priority": "high" | "medium" | "low"
- "action": Action name (e.g., "immediate_contact", "demo_offer", "nurture_sequence")
- "description": Brief description of the action
- "timing": When to take action (e.g., "within 24 hours", "within 1 week")

Focus on specific, actionable recommendations that sales teams can execute."""
        
        try:
            llm_response = await self._call_llm(prompt, llm_config, max_tokens=1000)
            
            # Try to parse JSON from response
            import re
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                recommendations = json.loads(json_match.group())
                return recommendations
            else:
                # Fallback to pattern-based
                return self._generate_recommendations(lead_data, scoring_factors, final_score)
        except Exception as e:
            await self.stream_log("lead_scorer", f"LLM recommendations parsing failed: {e}", "warning")
            # Fallback to pattern-based
            return self._generate_recommendations(lead_data, scoring_factors, final_score)

    def _parse_insights_from_text(self, text: str) -> List[Dict[str, str]]:
        """Parse insights from LLM text response if JSON parsing fails"""
        insights = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                insights.append({
                    "type": "insight",
                    "message": line,
                    "sentiment": "neutral"
                })
        return insights[:5]  # Limit to 5 insights

    def _calculate_confidence_level(self, lead_data: Dict[str, Any]) -> str:
        """Calculate confidence level in the scoring"""
        data_completeness = 0
        total_fields = 0
        
        important_fields = [
            "email", "name", "company", "title", "company_size", 
            "industry", "lead_source", "website_visits", "email_opens"
        ]
        
        for field in important_fields:
            total_fields += 1
            if lead_data.get(field) and lead_data[field] not in ["", "unknown", 0]:
                data_completeness += 1
        
        completeness_ratio = data_completeness / total_fields
        
        if completeness_ratio >= 0.8:
            return "high"
        elif completeness_ratio >= 0.6:
            return "medium"
        else:
            return "low"

    def get_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        # Get LLM config schema from mixin
        llm_schema = self._get_llm_schema_section()
        
        return {
            "type": "object",
            "properties": {
                **llm_schema,  # Include LLM provider configuration
                "scoring_model": {
                    "type": "string",
                    "title": "Scoring Model",
                    "description": "Lead scoring model to use",
                    "enum": ["comprehensive", "behavioral_focused", "firmographic_focused", "intent_focused"],
                    "default": "comprehensive"
                },
                "industry": {
                    "type": "string",
                    "title": "Industry Context",
                    "description": "Industry context for scoring adjustments",
                    "enum": ["general", "saas", "fintech", "healthcare", "e-commerce", "manufacturing"],
                    "default": "general"
                },
                "weight_adjustments": {
                    "type": "object",
                    "title": "Weight Adjustments",
                    "description": "Custom weights for scoring factors (0.0 to 1.0)",
                    "properties": {
                        "demographic": {"type": "number", "minimum": 0, "maximum": 1},
                        "firmographic": {"type": "number", "minimum": 0, "maximum": 1},
                        "behavioral": {"type": "number", "minimum": 0, "maximum": 1},
                        "intent": {"type": "number", "minimum": 0, "maximum": 1},
                        "source_quality": {"type": "number", "minimum": 0, "maximum": 1},
                        "recency": {"type": "number", "minimum": 0, "maximum": 1}
                    },
                    "default": {}
                },
                "include_recommendations": {
                    "type": "boolean",
                    "title": "Include Recommendations",
                    "description": "Generate action recommendations based on score",
                    "default": True
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        """Define expected inputs"""
        return {
            "lead_data": {
                "type": "object",
                "title": "Lead Data",
                "description": "Complete lead information for scoring",
                "properties": {
                    "email": {"type": "string"},
                    "name": {"type": "string"},
                    "company": {"type": "string"},
                    "title": {"type": "string"},
                    "company_size": {"type": "string"},
                    "industry": {"type": "string"},
                    "revenue": {"type": "string"},
                    "website_visits": {"type": "integer"},
                    "email_opens": {"type": "integer"},
                    "email_clicks": {"type": "integer"},
                    "content_downloads": {"type": "integer"},
                    "demo_requests": {"type": "integer"},
                    "lead_source": {"type": "string"},
                    "notes": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}}
                },
                "required": True
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Define expected outputs"""
        return {
            "lead_score": {
                "type": "object",
                "description": "Final lead score with breakdown and grade"
            },
            "scoring_breakdown": {
                "type": "object",
                "description": "Detailed breakdown of all scoring factors"
            },
            "lead_insights": {
                "type": "array",
                "description": "AI-generated insights about the lead"
            },
            "recommendations": {
                "type": "array",
                "description": "Recommended actions for the lead"
            },
            "metadata": {
                "type": "object",
                "description": "Scoring metadata and confidence information"
            }
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        """Estimate cost based on scoring complexity"""
        lead_data = inputs.get("lead_data", {})
        scoring_model = config.get("scoring_model", "comprehensive")
        
        # Base cost for scoring
        base_cost = 0.002
        
        # Additional cost based on data complexity
        data_fields = len([k for k, v in lead_data.items() if v])
        complexity_cost = data_fields * 0.0001
        
        # Model complexity cost
        model_costs = {
            "comprehensive": 0.001,
            "behavioral_focused": 0.0005,
            "firmographic_focused": 0.0005,
            "intent_focused": 0.0007
        }
        
        model_cost = model_costs.get(scoring_model, 0.001)
        
        return base_cost + complexity_cost + model_cost


# Register the node
NodeRegistry.register(
    "lead_scorer",
    LeadScorerNode,
    LeadScorerNode().get_metadata(),
)