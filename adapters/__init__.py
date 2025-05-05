"""
Adapter modules for compatibility between components.

These adapters provide interfaces to ensure compatibility between
new infrastructure components and existing application code.
"""

from adapters.repository_adapter import article_repository

__all__ = ["article_repository"]
