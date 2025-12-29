"""LLM client for OpenAI and Anthropic."""
from typing import Optional, Dict, Any, List
import openai
import anthropic
from config import settings


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
        **kwargs
    ) -> str:
        """Generate completion from LLM."""
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
            return response.choices[0].message.content
        
        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_toks,
                temperature=temp,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return response.content[0].text
    
    def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate JSON completion with schema validation."""
        import json
        
        if self.provider == "openai" and schema:
            # Use structured outputs if available
            try:
                response = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt or ""},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_schema", "json_schema": {"schema": schema}},
                    **kwargs
                )
                return json.loads(response.choices[0].message.content)
            except Exception:
                # Fallback to regular completion
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
                return json.loads(response_text[start:end])
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

