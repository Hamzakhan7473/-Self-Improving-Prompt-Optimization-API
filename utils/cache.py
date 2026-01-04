"""Caching system to reduce redundant LLM calls."""
import hashlib
import json
import time
from typing import Optional, Any, Dict
from functools import wraps
from config import settings


class LLMCache:
    """Cache for LLM responses to reduce redundant API calls."""
    
    def __init__(self, ttl_seconds: Optional[int] = None):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds or settings.cache_ttl_seconds
        self.enabled = settings.enable_cache
    
    def _generate_key(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate cache key from prompt and parameters."""
        key_data = {
            "prompt": prompt,
            "system_prompt": system_prompt or "",
            **{k: v for k, v in kwargs.items() if k not in ['temperature', 'max_tokens']}  # Exclude variable params
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def get(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[Any]:
        """Get cached response if available and not expired."""
        if not self.enabled:
            return None
        
        key = self._generate_key(prompt, system_prompt, **kwargs)
        
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl:
                return entry['response']
            else:
                # Expired, remove it
                del self.cache[key]
        
        return None
    
    def set(self, prompt: str, response: Any, system_prompt: Optional[str] = None, **kwargs) -> None:
        """Cache a response."""
        if not self.enabled:
            return
        
        key = self._generate_key(prompt, system_prompt, **kwargs)
        self.cache[key] = {
            'response': response,
            'timestamp': time.time()
        }
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self.cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = time.time()
        active = sum(1 for entry in self.cache.values() if now - entry['timestamp'] < self.ttl)
        expired = len(self.cache) - active
        
        return {
            'total_entries': len(self.cache),
            'active_entries': active,
            'expired_entries': expired,
            'enabled': self.enabled,
            'ttl_seconds': self.ttl
        }


# Global cache instance
_llm_cache: Optional[LLMCache] = None


def get_cache() -> LLMCache:
    """Get or create cache instance."""
    global _llm_cache
    if _llm_cache is None:
        _llm_cache = LLMCache()
    return _llm_cache


def cached_llm_call(func):
    """Decorator to cache LLM function calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        cache = get_cache()
        
        # Generate cache key from function arguments
        prompt = kwargs.get('prompt') or (args[0] if args else '')
        system_prompt = kwargs.get('system_prompt')
        
        # Check cache
        cached_response = cache.get(prompt, system_prompt, **kwargs)
        if cached_response is not None:
            return cached_response
        
        # Call function and cache result
        response = func(*args, **kwargs)
        cache.set(prompt, response, system_prompt, **kwargs)
        
        return response
    
    return wrapper



