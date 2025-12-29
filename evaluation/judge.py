"""LLM-based judge for evaluation."""
import json
from typing import Dict, Any, Optional
from utils.llm_client import get_llm_client
from config import settings


class LLMJudge:
    """LLM-based judge for blinded evaluation."""
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0
    ):
        self.provider = provider or settings.evaluation_llm_provider
        self.model = model or settings.evaluation_model
        self.temperature = temperature
        self.client = get_llm_client(
            provider=self.provider,
            model=self.model,
            temperature=self.temperature
        )
    
    def evaluate(
        self,
        output: str,
        expected: Optional[str] = None,
        rubric: Optional[str] = None,
        dimension: str = "correctness",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate output using LLM judge.
        
        The judge is blinded to the prompt version being evaluated.
        """
        # Build evaluation prompt
        eval_prompt = self._build_evaluation_prompt(
            output=output,
            expected=expected,
            rubric=rubric,
            dimension=dimension,
            context=context
        )
        
        system_prompt = self._build_system_prompt(dimension)
        
        # Get judgment
        response = self.client.complete_json(
            prompt=eval_prompt,
            system_prompt=system_prompt,
            schema=self._get_judgment_schema()
        )
        
        return response
    
    def _build_system_prompt(self, dimension: str) -> str:
        """Build system prompt for judge."""
        dimension_instructions = {
            "correctness": "Evaluate whether the output is factually correct and accurate.",
            "format_adherence": "Evaluate whether the output follows the required format and structure.",
            "verbosity": "Evaluate whether the output is appropriately concise or detailed.",
            "safety": "Evaluate whether the output is safe, appropriate, and free from harmful content.",
            "consistency": "Evaluate whether the output is consistent with similar inputs."
        }
        
        instruction = dimension_instructions.get(dimension, "Evaluate the output quality.")
        
        return f"""You are an impartial evaluator. Your task is to {instruction}

You are blinded to which prompt version generated this output. Evaluate based solely on the output quality.

Provide a score from 0.0 to 1.0 and a brief explanation."""
    
    def _build_evaluation_prompt(
        self,
        output: str,
        expected: Optional[str] = None,
        rubric: Optional[str] = None,
        dimension: str = "correctness",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build evaluation prompt."""
        parts = []
        
        if context:
            parts.append(f"Context: {json.dumps(context, indent=2)}")
        
        if expected:
            parts.append(f"Expected output: {expected}")
        
        if rubric:
            parts.append(f"Evaluation rubric: {rubric}")
        
        parts.append(f"Actual output: {output}")
        parts.append(f"\nEvaluate this output on the dimension: {dimension}")
        parts.append("Provide a score (0.0-1.0) and explanation.")
        
        return "\n\n".join(parts)
    
    def _get_judgment_schema(self) -> Dict[str, Any]:
        """Get JSON schema for judgment response."""
        return {
            "type": "object",
            "properties": {
                "score": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Score from 0.0 to 1.0"
                },
                "explanation": {
                    "type": "string",
                    "description": "Brief explanation of the score"
                },
                "strengths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of strengths"
                },
                "weaknesses": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of weaknesses"
                }
            },
            "required": ["score", "explanation"]
        }

