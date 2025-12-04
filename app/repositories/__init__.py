# app/repositories/__init__.py
"""Repository layer for data access abstraction."""
from app.repositories.base import BaseRepository
from app.repositories.resume_repository import ResumeRepository

__all__ = ["BaseRepository", "ResumeRepository"]
