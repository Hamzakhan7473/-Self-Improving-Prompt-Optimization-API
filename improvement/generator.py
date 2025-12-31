"""Generates improved prompt candidates."""
from typing import List, Dict, Any
from utils.llm_client import get_llm_client
from config import settings


class ImprovementGenerator:
    """Generates candidate prompt improvements."""
    
    def __init__(self):
        self.llm_client = get_llm_client()
    
    def generate_candidates(
        self,
        current_template: str,
        failure_analysis: Dict[str, Any],
        max_candidates: int = None
    ) -> List[Dict[str, Any]]:
        """
        Generate candidate prompt improvements based on failure analysis.
        
        Returns list of candidates with templates and rationales.
        """
        max_candidates = max_candidates or settings.max_candidates_per_iteration
        
        # Build prompt for improvement generation
        improvement_prompt = self._build_improvement_prompt(
            current_template=current_template,
            failure_analysis=failure_analysis
        )
        
        system_prompt = """You are an expert prompt engineer. Your task is to improve prompts based on failure analysis.

Generate improved prompt candidates that address the identified issues. Provide clear rationales for each improvement."""
        
        # Generate candidates
        response = self.llm_client.complete_json(
            prompt=improvement_prompt,
            system_prompt=system_prompt,
            schema=self._get_candidate_schema(max_candidates)
        )
        
        candidates = response.get("candidates", [])
        
        # Ensure we don't exceed max
        return candidates[:max_candidates]
    
    def _build_improvement_prompt(
        self,
        current_template: str,
        failure_analysis: Dict[str, Any]
    ) -> str:
        """Build prompt for improvement generation."""
        import json
        
        parts = [
            "Current prompt template:",
            f"```\n{current_template}\n```",
            "",
            "Failure analysis:",
            json.dumps(failure_analysis, indent=2),
            "",
            "Generate improved prompt candidates that address the identified issues.",
            "For each candidate, provide:",
            "1. The improved template",
            "2. A clear rationale explaining what was changed and why",
            "3. Expected improvements (which dimensions should improve)"
        ]
        
        return "\n".join(parts)
    
    def _get_candidate_schema(self, max_candidates: int) -> Dict[str, Any]:
        """Get JSON schema for candidate generation response."""
        return {
            "type": "object",
            "properties": {
                "candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "template": {
                                "type": "string",
                                "description": "Improved prompt template"
                            },
                            "rationale": {
                                "type": "string",
                                "description": "Explanation of changes and why they should help"
                            },
                            "expected_improvements": {
                                "type": "object",
                                "description": "Expected improvements per dimension",
                                "additionalProperties": {
                                    "type": "number",
                                    "minimum": 0.0,
                                    "maximum": 1.0
                                }
                            },
                            "changes_summary": {
                                "type": "string",
                                "description": "Brief summary of what changed"
                            }
                        },
                        "required": ["template", "rationale"]
                    },
                    "maxItems": max_candidates
                }
            },
            "required": ["candidates"]
        }


