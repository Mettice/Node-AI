"""
Security Scanner Node - Code → vulnerability reports
"""

from typing import Any, Dict, List
from backend.nodes.base import BaseNode
from backend.core.exceptions import NodeValidationError
from backend.core.node_registry import NodeRegistry


class SecurityScannerNode(BaseNode):
    node_type = "security_scanner"
    name = "Security Scanner"  
    description = "Scans code for security vulnerabilities and provides reports"
    category = "developer"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        code_input = inputs.get("code", "")
        scan_depth = config.get("scan_depth", "standard")
        
        if not code_input:
            raise NodeValidationError("Code input is required")

        vulnerabilities = self._scan_for_vulnerabilities(code_input, scan_depth)
        security_score = self._calculate_security_score(vulnerabilities)
        recommendations = self._generate_security_recommendations(vulnerabilities)

        return {
            "vulnerabilities": vulnerabilities,
            "security_score": security_score,
            "recommendations": recommendations,
            "scan_summary": {
                "total_issues": len(vulnerabilities),
                "critical": len([v for v in vulnerabilities if v.get("severity") == "critical"]),
                "high": len([v for v in vulnerabilities if v.get("severity") == "high"])
            }
        }

    def _scan_for_vulnerabilities(self, code: str, depth: str) -> List[Dict]:
        """Scan code for security vulnerabilities"""
        vulnerabilities = []
        
        # SQL Injection check
        if "SELECT * FROM" in code and "WHERE" in code and "=" in code:
            vulnerabilities.append({
                "type": "sql_injection",
                "severity": "high",
                "line": 1,
                "description": "Potential SQL injection vulnerability detected",
                "recommendation": "Use parameterized queries"
            })
        
        # XSS check
        if "innerHTML" in code or "document.write" in code:
            vulnerabilities.append({
                "type": "xss",
                "severity": "medium",
                "line": 1,
                "description": "Potential XSS vulnerability detected",
                "recommendation": "Sanitize user input before rendering"
            })
        
        # Hard-coded secrets
        if "password" in code.lower() or "api_key" in code.lower():
            vulnerabilities.append({
                "type": "secrets",
                "severity": "critical",
                "line": 1,
                "description": "Potential hard-coded credentials detected",
                "recommendation": "Use environment variables for secrets"
            })
        
        return vulnerabilities

    def _calculate_security_score(self, vulnerabilities: List[Dict]) -> int:
        """Calculate overall security score (0-100)"""
        if not vulnerabilities:
            return 100
        
        penalty = 0
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "low")
            if severity == "critical":
                penalty += 30
            elif severity == "high":
                penalty += 20
            elif severity == "medium":
                penalty += 10
            else:
                penalty += 5
        
        return max(0, 100 - penalty)

    def _generate_security_recommendations(self, vulnerabilities: List[Dict]) -> List[str]:
        """Generate security improvement recommendations"""
        recommendations = []
        
        vuln_types = {v.get("type") for v in vulnerabilities}
        
        if "sql_injection" in vuln_types:
            recommendations.append("Implement parameterized queries and input validation")
        if "xss" in vuln_types:
            recommendations.append("Add output encoding and content security policies")
        if "secrets" in vuln_types:
            recommendations.append("Move secrets to environment variables or secret management")
        
        recommendations.append("Conduct regular security code reviews")
        recommendations.append("Implement automated security testing in CI/CD")
        
        return recommendations

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scan_depth": {
                    "type": "string",
                    "enum": ["basic", "standard", "comprehensive"],
                    "default": "standard"
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "code": {
                "type": "string",
                "title": "Source Code",
                "description": "Code to scan for security vulnerabilities",
                "required": True
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "vulnerabilities": {"type": "array", "description": "Found security vulnerabilities"},
            "security_score": {"type": "integer", "description": "Overall security score (0-100)"},
            "recommendations": {"type": "array", "description": "Security improvement recommendations"}
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        code_input = inputs.get("code", "")
        scan_depth = config.get("scan_depth", "standard")
        
        base_cost = {"basic": 0.005, "standard": 0.01, "comprehensive": 0.02}
        return base_cost.get(scan_depth, 0.01) + (len(code_input) / 1000 * 0.001)


# Register the node
NodeRegistry.register(
    "security_scanner",
    SecurityScannerNode,
    SecurityScannerNode().get_metadata(),
)