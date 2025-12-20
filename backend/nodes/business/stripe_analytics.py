"""
Stripe Analytics Node - Connect Stripe and get AI-powered revenue analysis

This node integrates with Stripe to provide:
- Revenue trend analysis
- Customer lifetime value insights
- Churn prediction and analysis
- Revenue forecasting
- Payment failure analysis
- Subscription analytics
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeExecutionError, NodeValidationError
from backend.core.node_registry import NodeRegistry


class StripeAnalyticsNode(BaseNode, LLMConfigMixin):
    node_type = "stripe_analytics"
    name = "Stripe Revenue Analytics"
    description = "AI-powered revenue analysis from Stripe data"
    category = "business"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Stripe analytics analysis"""
        try:
            await self.stream_progress("stripe_analytics", 0.1, "Connecting to Stripe...")

            # Get configuration
            stripe_api_key = config.get("stripe_api_key", "")
            analysis_period = config.get("analysis_period", "30_days")
            include_forecasting = config.get("include_forecasting", True)
            include_churn_analysis = config.get("include_churn_analysis", True)
            currency = config.get("currency", "USD")

            # Get input data - accept multiple field names for flexibility
            stripe_data_raw = (
                inputs.get("stripe_data") or 
                inputs.get("data") or 
                inputs.get("text") or 
                inputs.get("content") or 
                inputs.get("output") or
                None
            )
            
            # Parse if it's a string (JSON)
            stripe_data = None
            if stripe_data_raw:
                if isinstance(stripe_data_raw, str):
                    try:
                        import json
                        stripe_data = json.loads(stripe_data_raw)
                    except json.JSONDecodeError:
                        stripe_data = None
                else:
                    stripe_data = stripe_data_raw

            if not stripe_api_key and not stripe_data:
                raise NodeValidationError("Stripe API key or Stripe data input is required. Connect a text_input node with Stripe data or provide API key in config.")

            await self.stream_progress("stripe_analytics", 0.3, "Fetching revenue data...")

            # Fetch or use provided Stripe data
            if stripe_data:
                revenue_data = stripe_data
            else:
                revenue_data = await self._fetch_stripe_data(stripe_api_key, analysis_period)
            
            await self.stream_progress("stripe_analytics", 0.5, "Analyzing revenue trends...")

            # Analyze revenue trends
            revenue_analysis = self._analyze_revenue_trends(revenue_data, analysis_period)
            
            await self.stream_progress("stripe_analytics", 0.7, "Computing customer insights...")

            # Analyze customers and subscriptions
            customer_analysis = self._analyze_customer_metrics(revenue_data)

            # Churn analysis if requested
            churn_analysis = {}
            if include_churn_analysis:
                churn_analysis = self._analyze_churn_patterns(revenue_data)

            await self.stream_progress("stripe_analytics", 0.9, "Generating forecasts and recommendations...")

            # Revenue forecasting if requested
            forecasting = {}
            if include_forecasting:
                forecasting = self._generate_revenue_forecast(revenue_analysis, customer_analysis)

            # Generate actionable insights - use LLM if available
            use_llm = False
            llm_config = None
            
            try:
                llm_config = self._resolve_llm_config(config)
                if llm_config.get("api_key"):
                    use_llm = True
            except Exception:
                use_llm = False
            
            if use_llm and llm_config:
                try:
                    insights = await self._generate_llm_business_insights(
                        revenue_analysis, customer_analysis, churn_analysis, forecasting, currency, llm_config
                    )
                except Exception as e:
                    await self.stream_log("stripe_analytics", f"LLM insights generation failed, using pattern matching: {e}", "warning")
                    insights = self._generate_business_insights(
                        revenue_analysis, customer_analysis, churn_analysis, forecasting
                    )
            else:
                insights = self._generate_business_insights(
                    revenue_analysis, customer_analysis, churn_analysis, forecasting
                )

            result = {
                "revenue_analysis": revenue_analysis,
                "customer_analysis": customer_analysis,
                "churn_analysis": churn_analysis,
                "forecasting": forecasting,
                "business_insights": insights,
                "metadata": {
                    "analysis_period": analysis_period,
                    "currency": currency,
                    "data_points": len(revenue_data.get("transactions", [])) if isinstance(revenue_data, dict) else 0,
                    "analyzed_at": datetime.now().isoformat()
                }
            }

            await self.stream_progress("stripe_analytics", 1.0, "Stripe analytics complete!")
            return result

        except Exception as e:
            raise NodeExecutionError(f"Stripe analytics failed: {str(e)}")

    async def _fetch_stripe_data(self, api_key: str, period: str) -> Dict[str, Any]:
        """Fetch data from Stripe API (placeholder for actual integration)"""
        
        # In a real implementation, this would use the Stripe Python SDK
        # For now, return mock data structure
        
        # Calculate date range
        end_date = datetime.now()
        if period == "7_days":
            start_date = end_date - timedelta(days=7)
        elif period == "30_days":
            start_date = end_date - timedelta(days=30)
        elif period == "90_days":
            start_date = end_date - timedelta(days=90)
        elif period == "1_year":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)

        # Mock data structure representing Stripe data
        mock_data = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "transactions": [
                # This would contain actual Stripe payment data
                # {
                #     "id": "pi_...",
                #     "amount": 2999,
                #     "currency": "usd",
                #     "created": 1234567890,
                #     "customer_id": "cus_...",
                #     "status": "succeeded"
                # }
            ],
            "customers": [
                # Customer data from Stripe
                # {
                #     "id": "cus_...",
                #     "created": 1234567890,
                #     "subscriptions": [...],
                #     "total_spent": 5998
                # }
            ],
            "subscriptions": [
                # Subscription data
                # {
                #     "id": "sub_...",
                #     "customer": "cus_...",
                #     "status": "active",
                #     "current_period_start": 1234567890,
                #     "plan": {...}
                # }
            ],
            "note": "This is mock data. In production, this would fetch real Stripe data using the API key."
        }

        return mock_data

    def _analyze_revenue_trends(self, stripe_data: Dict[str, Any], period: str) -> Dict[str, Any]:
        """Analyze revenue trends from Stripe data"""
        
        transactions = stripe_data.get("transactions", [])
        
        # Calculate basic revenue metrics
        total_revenue = sum(t.get("amount", 0) for t in transactions if t.get("status") == "succeeded") / 100  # Convert from cents
        transaction_count = len([t for t in transactions if t.get("status") == "succeeded"])
        
        # Calculate average transaction value
        avg_transaction_value = total_revenue / transaction_count if transaction_count > 0 else 0
        
        # Analyze revenue by time periods
        revenue_by_day = self._group_revenue_by_period(transactions, "daily")
        revenue_by_week = self._group_revenue_by_period(transactions, "weekly")
        
        # Calculate growth rates
        growth_rate = self._calculate_growth_rate(revenue_by_day)
        
        # Identify patterns
        revenue_patterns = self._identify_revenue_patterns(revenue_by_day)
        
        return {
            "total_revenue": total_revenue,
            "transaction_count": transaction_count,
            "average_transaction_value": avg_transaction_value,
            "growth_rate": growth_rate,
            "revenue_by_day": revenue_by_day,
            "revenue_by_week": revenue_by_week,
            "patterns": revenue_patterns,
            "peak_revenue_day": max(revenue_by_day.items(), key=lambda x: x[1]) if revenue_by_day else None,
            "lowest_revenue_day": min(revenue_by_day.items(), key=lambda x: x[1]) if revenue_by_day else None
        }

    def _analyze_customer_metrics(self, stripe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze customer-related metrics"""
        
        customers = stripe_data.get("customers", [])
        transactions = stripe_data.get("transactions", [])
        subscriptions = stripe_data.get("subscriptions", [])
        
        # Calculate customer lifetime value
        customer_ltv = self._calculate_customer_ltv(customers, transactions)
        
        # Analyze customer acquisition
        new_customers = len([c for c in customers if self._is_new_customer(c, stripe_data.get("period", {}))])
        
        # Calculate customer segments
        customer_segments = self._segment_customers(customers, transactions)
        
        # Subscription analysis
        subscription_metrics = self._analyze_subscriptions(subscriptions)
        
        return {
            "total_customers": len(customers),
            "new_customers": new_customers,
            "average_ltv": customer_ltv["average"],
            "customer_segments": customer_segments,
            "subscription_metrics": subscription_metrics,
            "ltv_distribution": customer_ltv["distribution"],
            "repeat_customer_rate": self._calculate_repeat_rate(customers, transactions)
        }

    def _analyze_churn_patterns(self, stripe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze churn patterns and risk factors"""
        
        subscriptions = stripe_data.get("subscriptions", [])
        customers = stripe_data.get("customers", [])
        
        # Calculate churn rate
        active_subs = len([s for s in subscriptions if s.get("status") == "active"])
        canceled_subs = len([s for s in subscriptions if s.get("status") in ["canceled", "past_due"]])
        total_subs = len(subscriptions)
        
        churn_rate = (canceled_subs / total_subs) if total_subs > 0 else 0
        
        # Identify churn risk factors
        churn_risk_factors = self._identify_churn_risk_factors(customers, subscriptions)
        
        # Predict at-risk customers
        at_risk_customers = self._identify_at_risk_customers(customers, subscriptions)
        
        return {
            "churn_rate": churn_rate,
            "active_subscriptions": active_subs,
            "canceled_subscriptions": canceled_subs,
            "churn_risk_factors": churn_risk_factors,
            "at_risk_customers": len(at_risk_customers),
            "at_risk_customer_details": at_risk_customers[:10],  # Top 10 at-risk
            "churn_prevention_recommendations": self._generate_churn_prevention_tips(churn_risk_factors)
        }

    def _generate_revenue_forecast(
        self, 
        revenue_analysis: Dict[str, Any], 
        customer_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate revenue forecasting based on historical data"""
        
        # Simple trend-based forecasting
        growth_rate = revenue_analysis.get("growth_rate", 0)
        current_revenue = revenue_analysis.get("total_revenue", 0)
        
        # Forecast next 30, 60, 90 days
        forecasts = {}
        
        for days in [30, 60, 90]:
            # Simple linear projection (in reality, would use more sophisticated models)
            projected_growth = (growth_rate / 100) * (days / 30)
            forecasted_revenue = current_revenue * (1 + projected_growth)
            
            forecasts[f"{days}_days"] = {
                "revenue": forecasted_revenue,
                "growth_assumed": projected_growth * 100,
                "confidence": "medium"  # Would be calculated based on data variance
            }
        
        # Seasonal adjustments (placeholder)
        seasonal_factors = self._calculate_seasonal_factors(revenue_analysis)
        
        return {
            "forecasts": forecasts,
            "methodology": "trend_based",
            "seasonal_factors": seasonal_factors,
            "assumptions": [
                "Growth rate continues at current trend",
                "No major market changes",
                "Customer behavior remains consistent"
            ]
        }

    def _generate_business_insights(
        self,
        revenue_analysis: Dict[str, Any],
        customer_analysis: Dict[str, Any], 
        churn_analysis: Dict[str, Any],
        forecasting: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate actionable business insights"""
        
        insights = []
        
        # Revenue insights
        growth_rate = revenue_analysis.get("growth_rate", 0)
        if growth_rate > 10:
            insights.append({
                "type": "revenue",
                "priority": "high",
                "message": f"Strong revenue growth of {growth_rate:.1f}% indicates healthy business momentum",
                "recommendation": "Consider scaling marketing efforts to capitalize on growth"
            })
        elif growth_rate < -5:
            insights.append({
                "type": "revenue",
                "priority": "critical", 
                "message": f"Revenue declining by {abs(growth_rate):.1f}% needs immediate attention",
                "recommendation": "Analyze customer feedback and market conditions to identify issues"
            })
        
        # Customer insights
        avg_ltv = customer_analysis.get("average_ltv", 0)
        if avg_ltv > 1000:
            insights.append({
                "type": "customer",
                "priority": "medium",
                "message": f"High average LTV of ${avg_ltv:.2f} indicates valuable customer base",
                "recommendation": "Focus on customer retention and upselling opportunities"
            })
        
        # Churn insights
        churn_rate = churn_analysis.get("churn_rate", 0)
        if churn_rate > 0.1:  # 10%
            insights.append({
                "type": "churn",
                "priority": "high",
                "message": f"High churn rate of {churn_rate*100:.1f}% is impacting revenue",
                "recommendation": "Implement customer success programs and improve onboarding"
            })
        
        # Forecasting insights
        if forecasting and "forecasts" in forecasting:
            next_month_growth = forecasting["forecasts"].get("30_days", {}).get("growth_assumed", 0)
            if next_month_growth > 5:
                insights.append({
                    "type": "forecast",
                    "priority": "medium",
                    "message": f"Projected growth of {next_month_growth:.1f}% next month looks promising",
                    "recommendation": "Prepare operations for increased demand"
                })
        
        return insights

    def _group_revenue_by_period(self, transactions: List[Dict], period: str) -> Dict[str, float]:
        """Group revenue by time period"""
        
        revenue_by_period = {}
        
        for transaction in transactions:
            if transaction.get("status") != "succeeded":
                continue
                
            # Extract date (would use actual timestamp in real implementation)
            transaction_date = datetime.now().date()  # Placeholder
            
            if period == "daily":
                period_key = transaction_date.isoformat()
            elif period == "weekly":
                # Get start of week
                start_of_week = transaction_date - timedelta(days=transaction_date.weekday())
                period_key = start_of_week.isoformat()
            else:
                period_key = transaction_date.isoformat()
            
            amount = transaction.get("amount", 0) / 100  # Convert from cents
            revenue_by_period[period_key] = revenue_by_period.get(period_key, 0) + amount
        
        return revenue_by_period

    def _calculate_growth_rate(self, revenue_by_day: Dict[str, float]) -> float:
        """Calculate revenue growth rate"""
        
        if len(revenue_by_day) < 2:
            return 0.0
        
        # Sort by date
        sorted_revenue = sorted(revenue_by_day.items())
        
        # Compare first and last periods
        first_period_revenue = sorted_revenue[0][1]
        last_period_revenue = sorted_revenue[-1][1]
        
        if first_period_revenue == 0:
            return 0.0
        
        growth_rate = ((last_period_revenue - first_period_revenue) / first_period_revenue) * 100
        return growth_rate

    def _identify_revenue_patterns(self, revenue_by_day: Dict[str, float]) -> List[str]:
        """Identify patterns in revenue data"""
        
        patterns = []
        
        if not revenue_by_day:
            return patterns
        
        revenue_values = list(revenue_by_day.values())
        
        # Check for consistent growth
        increasing_days = 0
        for i in range(1, len(revenue_values)):
            if revenue_values[i] > revenue_values[i-1]:
                increasing_days += 1
        
        if increasing_days / len(revenue_values) > 0.7:
            patterns.append("Consistent upward trend")
        
        # Check for volatility
        if len(revenue_values) > 1:
            avg_revenue = sum(revenue_values) / len(revenue_values)
            variance = sum((x - avg_revenue) ** 2 for x in revenue_values) / len(revenue_values)
            std_dev = variance ** 0.5
            
            if std_dev / avg_revenue > 0.5:
                patterns.append("High volatility in daily revenue")
            elif std_dev / avg_revenue < 0.1:
                patterns.append("Stable daily revenue")
        
        return patterns

    def _calculate_customer_ltv(self, customers: List[Dict], transactions: List[Dict]) -> Dict[str, Any]:
        """Calculate customer lifetime value"""
        
        customer_spending = {}
        
        for transaction in transactions:
            if transaction.get("status") == "succeeded":
                customer_id = transaction.get("customer_id")
                amount = transaction.get("amount", 0) / 100
                customer_spending[customer_id] = customer_spending.get(customer_id, 0) + amount
        
        ltv_values = list(customer_spending.values())
        
        if not ltv_values:
            return {"average": 0, "distribution": {}}
        
        average_ltv = sum(ltv_values) / len(ltv_values)
        
        # Create LTV distribution
        distribution = {
            "0-100": len([v for v in ltv_values if v <= 100]),
            "100-500": len([v for v in ltv_values if 100 < v <= 500]),
            "500-1000": len([v for v in ltv_values if 500 < v <= 1000]),
            "1000+": len([v for v in ltv_values if v > 1000])
        }
        
        return {
            "average": average_ltv,
            "median": sorted(ltv_values)[len(ltv_values)//2],
            "distribution": distribution
        }

    def _is_new_customer(self, customer: Dict[str, Any], period: Dict[str, Any]) -> bool:
        """Check if customer was acquired in the analysis period"""
        # Placeholder implementation
        return True  # In real implementation, would check customer creation date against period

    def _segment_customers(self, customers: List[Dict], transactions: List[Dict]) -> Dict[str, int]:
        """Segment customers based on spending behavior"""
        
        customer_spending = {}
        for transaction in transactions:
            if transaction.get("status") == "succeeded":
                customer_id = transaction.get("customer_id")
                amount = transaction.get("amount", 0) / 100
                customer_spending[customer_id] = customer_spending.get(customer_id, 0) + amount
        
        segments = {
            "high_value": 0,    # >$1000
            "medium_value": 0,  # $100-$1000  
            "low_value": 0,     # <$100
            "inactive": 0       # $0
        }
        
        for customer_id in [c.get("id") for c in customers]:
            spending = customer_spending.get(customer_id, 0)
            
            if spending > 1000:
                segments["high_value"] += 1
            elif spending > 100:
                segments["medium_value"] += 1
            elif spending > 0:
                segments["low_value"] += 1
            else:
                segments["inactive"] += 1
        
        return segments

    def _analyze_subscriptions(self, subscriptions: List[Dict]) -> Dict[str, Any]:
        """Analyze subscription metrics"""
        
        if not subscriptions:
            return {"total": 0, "active": 0, "canceled": 0}
        
        active_count = len([s for s in subscriptions if s.get("status") == "active"])
        canceled_count = len([s for s in subscriptions if s.get("status") == "canceled"])
        past_due_count = len([s for s in subscriptions if s.get("status") == "past_due"])
        
        # Calculate MRR (Monthly Recurring Revenue) - placeholder calculation
        mrr = active_count * 29  # Assuming $29 average plan
        
        return {
            "total": len(subscriptions),
            "active": active_count,
            "canceled": canceled_count,
            "past_due": past_due_count,
            "monthly_recurring_revenue": mrr,
            "retention_rate": (active_count / len(subscriptions)) * 100 if subscriptions else 0
        }

    def _calculate_repeat_rate(self, customers: List[Dict], transactions: List[Dict]) -> float:
        """Calculate repeat customer rate"""
        
        customer_transaction_counts = {}
        
        for transaction in transactions:
            if transaction.get("status") == "succeeded":
                customer_id = transaction.get("customer_id")
                customer_transaction_counts[customer_id] = customer_transaction_counts.get(customer_id, 0) + 1
        
        repeat_customers = len([count for count in customer_transaction_counts.values() if count > 1])
        total_customers = len(customer_transaction_counts)
        
        return (repeat_customers / total_customers) * 100 if total_customers > 0 else 0

    def _identify_churn_risk_factors(self, customers: List[Dict], subscriptions: List[Dict]) -> List[str]:
        """Identify factors that contribute to churn"""
        
        risk_factors = []
        
        # Analyze canceled subscriptions for patterns
        canceled_subs = [s for s in subscriptions if s.get("status") == "canceled"]
        
        if len(canceled_subs) > 0:
            # Check for common cancellation reasons (would analyze actual data)
            risk_factors.append("Payment failures leading to cancellation")
            risk_factors.append("Lack of product engagement after trial")
            risk_factors.append("Price sensitivity in certain customer segments")
        
        return risk_factors

    def _identify_at_risk_customers(self, customers: List[Dict], subscriptions: List[Dict]) -> List[Dict]:
        """Identify customers at risk of churning"""
        
        at_risk = []
        
        for subscription in subscriptions:
            if subscription.get("status") == "past_due":
                at_risk.append({
                    "customer_id": subscription.get("customer"),
                    "subscription_id": subscription.get("id"),
                    "risk_reason": "Payment past due",
                    "risk_score": 0.8
                })
        
        # Add more sophisticated risk scoring in real implementation
        
        return sorted(at_risk, key=lambda x: x["risk_score"], reverse=True)

    def _generate_churn_prevention_tips(self, risk_factors: List[str]) -> List[str]:
        """Generate churn prevention recommendations"""
        
        tips = [
            "Implement proactive customer success outreach",
            "Set up automated dunning management for failed payments",
            "Create onboarding sequence to improve early engagement",
            "Offer flexible pricing options for price-sensitive segments",
            "Monitor usage patterns and reach out to inactive users"
        ]
        
        return tips

    def _calculate_seasonal_factors(self, revenue_analysis: Dict[str, Any]) -> Dict[str, float]:
        """Calculate seasonal adjustment factors"""
        
        # Placeholder for seasonal analysis
        return {
            "january": 0.9,
            "february": 0.95,
            "march": 1.0,
            "december": 1.2  # Holiday boost
        }

    def get_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        # Get LLM config schema from mixin
        llm_schema = self._get_llm_schema_section()
        
        return {
            "type": "object",
            "properties": {
                **llm_schema,  # Include LLM provider configuration
                "stripe_api_key": {
                    "type": "string",
                    "title": "Stripe API Key",
                    "description": "Stripe secret API key for data access",
                    "format": "password"
                },
                "analysis_period": {
                    "type": "string",
                    "title": "Analysis Period", 
                    "description": "Time period for revenue analysis",
                    "enum": ["7_days", "30_days", "90_days", "1_year"],
                    "default": "30_days"
                },
                "currency": {
                    "type": "string",
                    "title": "Currency",
                    "description": "Currency for revenue calculations",
                    "enum": ["USD", "EUR", "GBP", "CAD"],
                    "default": "USD"
                },
                "include_forecasting": {
                    "type": "boolean",
                    "title": "Include Revenue Forecasting",
                    "description": "Generate revenue forecasts based on trends",
                    "default": True
                },
                "include_churn_analysis": {
                    "type": "boolean",
                    "title": "Include Churn Analysis",
                    "description": "Analyze customer churn patterns and risks",
                    "default": True
                }
            },
            "required": []
        }

    def get_input_schema(self) -> Dict[str, Any]:
        """Define expected inputs"""
        return {
            "stripe_data": {
                "type": "object",
                "title": "Stripe Data",
                "description": "Pre-fetched Stripe data (optional if API key provided)",
                "required": False
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Define expected outputs"""
        return {
            "revenue_analysis": {
                "type": "object",
                "description": "Comprehensive revenue trend analysis"
            },
            "customer_analysis": {
                "type": "object", 
                "description": "Customer metrics and lifetime value analysis"
            },
            "churn_analysis": {
                "type": "object",
                "description": "Churn patterns and risk assessment"
            },
            "forecasting": {
                "type": "object",
                "description": "Revenue forecasts and projections"
            },
            "business_insights": {
                "type": "array",
                "description": "AI-generated actionable business insights"
            }
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        """Estimate cost based on data volume and analysis complexity"""
        
        # Base cost for Stripe API calls and analysis
        base_cost = 0.01
        
        # Additional cost based on analysis period
        period = config.get("analysis_period", "30_days")
        period_costs = {
            "7_days": 0.005,
            "30_days": 0.010,
            "90_days": 0.020,
            "1_year": 0.050
        }
        
        period_cost = period_costs.get(period, 0.010)
        
        # Additional costs for advanced features
        feature_cost = 0
        if config.get("include_forecasting", True):
            feature_cost += 0.005
        if config.get("include_churn_analysis", True):
            feature_cost += 0.005
            
        return base_cost + period_cost + feature_cost


# Register the node
NodeRegistry.register(
    "stripe_analytics",
    StripeAnalyticsNode,
    StripeAnalyticsNode().get_metadata(),
)