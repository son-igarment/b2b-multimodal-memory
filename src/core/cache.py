import json
import hashlib
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from .logging import get_logger

logger = get_logger(__name__)


class MemoryCache:
    """Simple in-memory cache implementation"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self._cache:
            return None
        
        cache_entry = self._cache[key]
        if datetime.now() > cache_entry["expires_at"]:
            del self._cache[key]
            return None
        
        logger.debug(f"Cache hit for key: {key}")
        return cache_entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.now()
        }
        
        logger.debug(f"Cache set for key: {key}, TTL: {ttl}s")
    
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted for key: {key}")
    
    def clear(self) -> None:
        """Clear all cache"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = datetime.now()
        active_keys = [
            key for key, entry in self._cache.items()
            if now <= entry["expires_at"]
        ]
        
        return {
            "total_keys": len(self._cache),
            "active_keys": len(active_keys),
            "expired_keys": len(self._cache) - len(active_keys),
            "default_ttl": self.default_ttl
        }


# Global cache instance
cache = MemoryCache()


def cached(ttl: Optional[int] = None):
    """Decorator để cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache._generate_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate cache key with prefix"""
    key_data = {
        "prefix": prefix,
        "args": args,
        "kwargs": sorted(kwargs.items())
    }
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()
