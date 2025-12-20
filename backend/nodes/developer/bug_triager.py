"""
Bug Triager Node - GitHub issues → priority scores and assignments
"""

from typing import Any, Dict, List
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeValidationError, NodeExecutionError
from backend.core.node_registry import NodeRegistry


class BugTriagerNode(BaseNode, LLMConfigMixin):
    node_type = "bug_triager"
    name = "Bug Triager"
    description = "Analyzes GitHub issues and assigns priority scores and team assignments"
    category = "developer"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute bug triaging with LLM support"""
        try:
            # Get inputs - accept multiple field names
            issues_raw = (
                inputs.get("issues") or
                inputs.get("data") or
                inputs.get("text") or
                inputs.get("content") or
                []
            )
            
            # Parse if it's a string (JSON)
            if isinstance(issues_raw, str):
                import json
                try:
                    issues = json.loads(issues_raw)
                    if not isinstance(issues, list):
                        issues = [issues]
                except json.JSONDecodeError:
                    raise NodeValidationError("Issues must be valid JSON array")
            elif isinstance(issues_raw, list):
                issues = issues_raw
            elif isinstance(issues_raw, dict):
                issues = [issues_raw]  # Single issue
            else:
                issues = []
            
            if not issues:
                raise NodeValidationError("GitHub issues data is required. Connect a data source or provide issues in config.")

            # Try to use LLM if available
            use_llm = False
            llm_config = None
            
            try:
                llm_config = self._resolve_llm_config(config)
                if llm_config.get("api_key"):
                    use_llm = True
            except Exception:
                use_llm = False

            triaged_issues = []
            for issue in issues:
                if use_llm and llm_config:
                    try:
                        triage_result = await self._triage_issue_with_llm(issue, llm_config)
                        triaged_issues.append(triage_result)
                    except Exception as e:
                        # Fallback to pattern-based if LLM fails
                        await self.stream_log("bug_triager", f"LLM triaging failed for issue {issue.get('id', 'unknown')}, using pattern matching: {e}", "warning")
                        priority = self._calculate_priority(issue)
                        assignment = self._suggest_assignment(issue, priority)
                        triaged_issues.append({
                            "issue_id": issue.get("id"),
                            "title": issue.get("title"),
                            "priority": priority,
                            "suggested_assignee": assignment,
                            "estimated_effort": self._estimate_effort(issue),
                            "labels": self._suggest_labels(issue, priority)
                        })
                else:
                    # Use pattern-based fallback
                    priority = self._calculate_priority(issue)
                    assignment = self._suggest_assignment(issue, priority)
                    triaged_issues.append({
                        "issue_id": issue.get("id"),
                        "title": issue.get("title"),
                        "priority": priority,
                        "suggested_assignee": assignment,
                        "estimated_effort": self._estimate_effort(issue),
                        "labels": self._suggest_labels(issue, priority)
                    })

            return {
                "triaged_issues": triaged_issues,
                "summary": {
                    "total_issues": len(issues),
                    "high_priority": len([i for i in triaged_issues if i["priority"] == "high"]),
                    "critical_issues": len([i for i in triaged_issues if i["priority"] == "critical"])
                }
            }
        except Exception as e:
            raise NodeExecutionError(f"Bug triaging failed: {str(e)}")

    def _calculate_priority(self, issue: Dict) -> str:
        """Calculate issue priority based on content analysis"""
        title = issue.get("title", "").lower()
        body = issue.get("body", "").lower()
        
        critical_keywords = ["crash", "security", "data loss", "production"]
        high_keywords = ["error", "bug", "broken", "urgent"]
        
        if any(keyword in title or keyword in body for keyword in critical_keywords):
            return "critical"
        elif any(keyword in title or keyword in body for keyword in high_keywords):
            return "high"
        else:
            return "medium"

    def _suggest_assignment(self, issue: Dict, priority: str) -> str:
        """Suggest team assignment based on issue content"""
        title = issue.get("title", "").lower()
        
        if "frontend" in title or "ui" in title:
            return "frontend-team"
        elif "api" in title or "backend" in title:
            return "backend-team"
        elif "security" in title:
            return "security-team"
        else:
            return "general-dev-team"

    def _estimate_effort(self, issue: Dict) -> str:
        """Estimate development effort"""
        body_length = len(issue.get("body", ""))
        
        if body_length > 1000:  # Detailed issue
            return "large"
        elif body_length > 300:
            return "medium"
        else:
            return "small"

    def _suggest_labels(self, issue: Dict, priority: str) -> list:
        """Suggest labels for the issue"""
        labels = [f"priority-{priority}"]
        
        title = issue.get("title", "").lower()
        if "bug" in title:
            labels.append("bug")
        if "feature" in title:
            labels.append("enhancement")
        
        return labels

    async def _triage_issue_with_llm(self, issue: Dict[str, Any], llm_config: Dict[str, Any]) -> Dict[str, Any]:
        """Triage a single issue using LLM for better understanding"""
        
        issue_title = issue.get("title", "")
        issue_body = issue.get("body", "")[:3000]  # Limit body length
        issue_labels = issue.get("labels", [])
        issue_author = issue.get("user", {}).get("login", "unknown")
        
        prompt = f"""Analyze this GitHub issue and provide triage information.

Issue Title: {issue_title}

Issue Body:
{issue_body}

Existing Labels: {', '.join(issue_labels) if issue_labels else 'None'}
Author: {issue_author}

Provide triage analysis in JSON format with:
- "priority": "critical" | "high" | "medium" | "low"
- "suggested_assignee": Team or person to assign (e.g., "frontend-team", "backend-team", "security-team")
- "estimated_effort": "small" | "medium" | "large"
- "labels": Array of suggested labels (e.g., ["bug", "priority-high", "frontend"])
- "reasoning": Brief explanation of priority and assignment decision

Consider:
1. Severity and impact (security, data loss, production issues = critical)
2. User impact (affects many users = high priority)
3. Technical complexity (affects effort estimation)
4. Team expertise needed (affects assignment)

Return only valid JSON."""
        
        try:
            import json
            import re
            llm_response = await self._call_llm(prompt, llm_config, max_tokens=500)
            
            # Try to parse JSON
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                triage_data = json.loads(json_match.group())
                return {
                    "issue_id": issue.get("id"),
                    "title": issue_title,
                    "priority": triage_data.get("priority", "medium"),
                    "suggested_assignee": triage_data.get("suggested_assignee", "general-dev-team"),
                    "estimated_effort": triage_data.get("estimated_effort", "medium"),
                    "labels": triage_data.get("labels", []),
                    "reasoning": triage_data.get("reasoning", "")
                }
            else:
                # Fallback to pattern-based
                priority = self._calculate_priority(issue)
                assignment = self._suggest_assignment(issue, priority)
                return {
                    "issue_id": issue.get("id"),
                    "title": issue_title,
                    "priority": priority,
                    "suggested_assignee": assignment,
                    "estimated_effort": self._estimate_effort(issue),
                    "labels": self._suggest_labels(issue, priority)
                }
        except Exception:
            # Fallback to pattern-based
            priority = self._calculate_priority(issue)
            assignment = self._suggest_assignment(issue, priority)
            return {
                "issue_id": issue.get("id"),
                "title": issue.get("title"),
                "priority": priority,
                "suggested_assignee": assignment,
                "estimated_effort": self._estimate_effort(issue),
                "labels": self._suggest_labels(issue, priority)
            }

    def get_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        # Get LLM config schema from mixin
        llm_schema = self._get_llm_schema_section()
        
        return {
            "type": "object",
            "properties": {
                **llm_schema  # Include LLM provider configuration
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "issues": {
                "type": "array",
                "title": "GitHub Issues",
                "description": "Array of GitHub issue objects",
                "required": True
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "triaged_issues": {"type": "array", "description": "Issues with priority and assignment"},
            "summary": {"type": "object", "description": "Triage summary statistics"}
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        issues = inputs.get("issues", [])
        return 0.01 + (len(issues) * 0.002)


# Register the node
NodeRegistry.register(
    "bug_triager",
    BugTriagerNode,
    BugTriagerNode().get_metadata(),
)
