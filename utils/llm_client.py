"""LLM client for OpenAI and Anthropic."""
from typing import Optional, Dict, Any, List
import openai
try:
    import anthropic
except ImportError:
    anthropic = None
from config import settings
from utils.cache import get_cache


class LLMClient:
    """Unified LLM client supporting multiple providers."""
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        self.provider = provider or settings.default_llm_provider
        self.model = model or settings.default_model
        self.temperature = temperature if temperature is not None else settings.evaluation_temperature
        self.max_tokens = max_tokens or settings.evaluation_max_tokens
        
        if self.provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
        elif self.provider == "anthropic":
            if anthropic is None:
                raise ValueError("Anthropic package not installed. Install with: pip install anthropic")
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
        **kwargs
    ) -> str:
        """Generate completion from LLM with optional caching."""
        cache = get_cache()
        
        # Check cache if enabled
        if use_cache and settings.enable_cache:
            cached_response = cache.get(prompt, system_prompt, model=self.model, provider=self.provider)
            if cached_response is not None:
                return cached_response
        
        temp = temperature if temperature is not None else self.temperature
        max_toks = max_tokens if max_tokens is not None else self.max_tokens
        
        if self.provider == "openai":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=max_toks,
                **kwargs
            )
            result = response.choices[0].message.content
            
            # Cache result if enabled
            if use_cache and settings.enable_cache:
                cache.set(prompt, result, system_prompt, model=self.model, provider=self.provider)
            
            return result
        
        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_toks,
                temperature=temp,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            result = response.content[0].text
            
            # Cache result if enabled
            if use_cache and settings.enable_cache:
                cache.set(prompt, result, system_prompt, model=self.model, provider=self.provider)
            
            return result
    
    def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate JSON completion with schema validation."""
        import json
        
        # For OpenAI, use response_format to force JSON output
        if self.provider == "openai":
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                # Add explicit JSON instruction to user message
                json_prompt = prompt + "\n\nIMPORTANT: Respond with ONLY valid JSON. No text before or after."
                messages.append({"role": "user", "content": json_prompt})
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"},  # Force JSON output
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    **kwargs
                )
                result = json.loads(response.choices[0].message.content)
                # Basic validation
                if schema and "required" in schema:
                    for field in schema["required"]:
                        if field not in result:
                            raise ValueError(f"Missing required field: {field}")
                return result
            except Exception as e:
                # Fallback to regular completion with parsing
                pass
        
        # Fallback: regular completion with JSON parsing
        response_text = self.complete(prompt, system_prompt, **kwargs)
        # Try to extract JSON from response
        try:
            # Look for JSON in code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON object in text
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(response_text[start:end])
                except json.JSONDecodeError:
                    pass
            
            # Last resort: try to extract score and explanation from text
            # Look for patterns like "Score: 0.5" or "score: 0.5"
            import re
            score_match = re.search(r'(?:score|Score)[:\s]+([0-9.]+)', response_text, re.IGNORECASE)
            explanation_match = re.search(r'(?:explanation|Explanation)[:\s]+(.+?)(?:\n\n|\nScore|$)', response_text, re.IGNORECASE | re.DOTALL)
            
            if score_match:
                try:
                    score = float(score_match.group(1))
                    score = max(0.0, min(1.0, score))  # Clamp to 0-1
                    explanation = explanation_match.group(1).strip() if explanation_match else "No explanation provided"
                    return {
                        "score": score,
                        "explanation": explanation
                    }
                except (ValueError, AttributeError):
                    pass
            
            raise ValueError(f"Could not parse JSON from response: {response_text[:200]}")


# Global client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> LLMClient:
    """Get or create LLM client instance."""
    global _llm_client
    
    if _llm_client is None or provider or model:
        _llm_client = LLMClient(
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    return _llm_client

