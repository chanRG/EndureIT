"""
Pytest configuration: set required environment variables before any app imports.
"""

import sys
from unittest.mock import MagicMock

# Stub optional heavy dependencies so unit tests work without a full install.
# Real integration tests that need these must install the actual packages.
for _mod in ("anthropic", "pywebpush", "pdfplumber", "magic"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

import os

os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-only")
os.environ.setdefault("ANTHROPIC_API_KEY", "")
