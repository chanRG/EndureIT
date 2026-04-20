"""
Smoke tests for Settings — verifies the settings model parses correctly
without requiring a real database or external services.
"""
import pytest
from unittest.mock import patch


def test_settings_defaults():
    """Settings can be instantiated with required fields mocked."""
    with patch.dict(
        "os.environ",
        {
            "POSTGRES_SERVER": "localhost",
            "POSTGRES_USER": "test",
            "POSTGRES_PASSWORD": "test",
            "POSTGRES_DB": "test",
            "SECRET_KEY": "test-key",
        },
        clear=False,
    ):
        from importlib import reload
        import app.core.settings as settings_module

        reload(settings_module)
        s = settings_module.Settings()
        assert s.CLAUDE_MODEL_DEFAULT == "claude-sonnet-4-6"
        assert s.CLAUDE_MODEL_HEAVY == "claude-opus-4-7"
        assert s.MAX_UPLOAD_SIZE_MB == 10


def test_cors_origins_parsing():
    """cors_origins property splits comma-separated string correctly."""
    with patch.dict(
        "os.environ",
        {
            "POSTGRES_SERVER": "localhost",
            "POSTGRES_USER": "test",
            "POSTGRES_PASSWORD": "test",
            "POSTGRES_DB": "test",
            "SECRET_KEY": "test-key",
            "BACKEND_CORS_ORIGINS": "http://localhost:3000,http://localhost:8080",
        },
        clear=False,
    ):
        from importlib import reload
        import app.core.settings as settings_module

        reload(settings_module)
        s = settings_module.Settings()
        assert "http://localhost:3000" in s.cors_origins
        assert "http://localhost:8080" in s.cors_origins
        assert len(s.cors_origins) == 2
