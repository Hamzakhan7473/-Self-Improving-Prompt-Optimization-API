"""Enhanced blinded evaluator to prevent evaluation leakage."""
import hashlib
from typing import Dict, Any, Optional, List
from utils.llm_client import LLMClient
from utils.cache import get_cache, cached_llm_call
from config import settings
from evaluation.judge import LLMJudge


class BlindedEvaluator:
    """
    Enhanced evaluator with strict blinding to prevent evaluation leakage.
    
    Features:
    - Separate LLM instances for generation vs evaluation
    - Anonymous output evaluation (no prompt version info)
    - Deterministic evaluation where possible
    - Low-variance evaluation modes
    """
    
    def __init__(
        self,
        generation_provider: Optional[str] = None,
        generation_model: Optional[str] = None,
        evaluation_provider: Optional[str] = None,
        evaluation_model: Optional[str] = None
    ):
        # Separate clients for generation and evaluation
        self.generation_client = LLMClient(
            provider=generation_provider or settings.default_llm_provider,
            model=generation_model or settings.default_model,
            temperature=0.7  # Allow creativity for generation
        )
        
        # Strict evaluation client with low temperature
        self.evaluation_client = LLMClient(
            provider=evaluation_provider or settings.evaluation_llm_provider,
            model=evaluation_model or settings.evaluation_model,
            temperature=0.0  # Deterministic evaluation
        )
        
        self.judge = LLMJudge(
            provider=evaluation_provider or settings.evaluation_llm_provider,
            model=evaluation_model or settings.evaluation_model,
            temperature=0.0
        )
        
        self.cache = get_cache()
    
    def generate_output(
        self,
        prompt: str,
        prompt_version_id: Optional[int] = None
    ) -> str:
        """
        Generate output using generation client.
        
        Note: prompt_version_id is only for tracking, not passed to LLM.
        """
        # Check cache first
        cached = self.cache.get(prompt)
        if cached:
            return cached
        
        # Generate with generation client
        output = self.generation_client.complete(prompt, use_cache=False)
        
        # Cache result
        self.cache.set(prompt, output)
        
        return output
    
    def evaluate_output_blinded(
        self,
        output: str,
        expected: Optional[str] = None,
        rubric: Optional[str] = None,
        dimension: str = "correctness",
        context: Optional[Dict[str, Any]] = None,
        prompt_version_id: Optional[int] = None  # For tracking only, NOT used in evaluation
    ) -> Dict[str, Any]:
        """
        Evaluate output with strict blinding.
        
        The evaluator has NO knowledge of:
        - Which prompt version generated this output
        - The prompt template used
        - Any metadata about the prompt
        
        Only the output itself and evaluation criteria are provided.
        """
        # Create anonymous evaluation context (no prompt info)
        anonymous_context = self._create_anonymous_context(context)
        
        # Use evaluation client (separate from generation)
        judgment = self.judge.evaluate(
            output=output,
            expected=expected,
            rubric=rubric,
            dimension=dimension,
            context=anonymous_context
        )
        
        # Add blinding metadata
        judgment['evaluation_metadata'] = {
            'blinded': True,
            'evaluator_model': self.evaluation_client.model,
            'evaluator_temperature': 0.0,
            'prompt_version_id_known': False  # Explicitly mark as blinded
        }
        
        return judgment
    
    def _create_anonymous_context(self, context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create anonymous context without prompt version information."""
        if not context:
            return None
        
        # Remove any identifiers that could leak prompt version info
        anonymous = {}
        for key, value in context.items():
            # Exclude keys that might identify prompt versions
            if key not in ['prompt_version_id', 'prompt_id', 'version', 'template', 'prompt_template']:
                anonymous[key] = value
        
        return anonymous if anonymous else None
    
    
    def evaluate_with_deterministic_fallback(
        self,
        output: str,
        expected: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        dimension: str = "correctness"
    ) -> Dict[str, Any]:
        """
        Evaluate with deterministic validators first, LLM judge as fallback.
        
        This reduces variance and cost by using deterministic checks where possible.
        """
        from utils.validators import ValidatorRegistry
        
        # Try deterministic validation first
        if dimension == "format_adherence" and schema:
            is_valid, details = ValidatorRegistry.validate("json_schema", output, schema)
            if is_valid:
                return {
                    'score': 1.0,
                    'explanation': 'Format validation passed',
                    'method': 'deterministic',
                    'details': details
                }
            else:
                # Partial credit for format issues
                return {
                    'score': 0.3,
                    'explanation': 'Format validation failed',
                    'method': 'deterministic',
                    'details': details
                }
        
        # Fallback to LLM judge
        return self.evaluate_output_blinded(
            output=output,
            expected=expected,
            dimension=dimension
        )

