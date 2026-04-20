"""
Extended configuration utilities for EndureIT API.
"""
from functools import lru_cache

from app.core.settings import Settings


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Returns:
        Cached settings instance
    """
    return Settings()


# Convenience alias
settings = get_settings()

