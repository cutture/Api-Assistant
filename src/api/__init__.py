"""
FastAPI REST API for API Assistant.

Exposes all search and document management capabilities via REST API.
"""

from src.api.app import create_app

__all__ = ["create_app"]
