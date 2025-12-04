# app/repositories/resume_repository.py
"""
Repository for resume data access.
"""
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.logging_config import LogConfig
from app.repositories.base import BaseRepository

logger = LogConfig.get_logger()


class ResumeRepository(BaseRepository[Dict[str, Any]]):
    """
    Repository for resume CRUD operations.

    Provides domain-specific methods for resume data access
    while inheriting common operations from BaseRepository.
    """

    def __init__(self, collection: AsyncIOMotorCollection):
        """
        Initialize resume repository.

        Args:
            collection: MongoDB resumes collection
        """
        super().__init__(collection)

    async def get_by_user_id(
        self, user_id: int, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get resume by user ID.

        Args:
            user_id: User's ID
            version: Optional version filter

        Returns:
            Resume document if found
        """
        query = {"user_id": user_id}
        if version:
            query["version"] = version

        result = await self.find_one(query)

        if result:
            logger.info(
                "Resume retrieved",
                extra={
                    "event_type": "resume_retrieved",
                    "user_id": user_id,
                    "version": version,
                },
            )
        else:
            logger.warning(
                "Resume not found",
                extra={
                    "event_type": "resume_not_found",
                    "user_id": user_id,
                    "version": version,
                },
            )

        return result

    async def create(self, user_id: int, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new resume for a user.

        If a resume already exists for the user, it will be replaced.

        Args:
            user_id: User's ID
            resume_data: Resume data to insert

        Returns:
            Created resume document
        """
        # Check for existing resume
        existing = await self.find_one({"user_id": user_id})
        if existing:
            logger.warning(
                "Existing resume found, deleting before creating new",
                extra={"event_type": "resume_replace", "user_id": user_id},
            )
            await self.delete_one({"user_id": user_id})

        # Add user_id to resume data
        resume_data["user_id"] = user_id

        # Insert new resume
        inserted_id = await self.insert_one(resume_data)

        # Retrieve and return the created resume
        created_resume = await self.find_one({"_id": inserted_id})

        logger.info(
            "Resume created successfully",
            extra={"event_type": "resume_created", "user_id": user_id},
        )

        return created_resume

    async def update(
        self, user_id: int, update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing resume.

        Args:
            user_id: User's ID
            update_data: Fields to update

        Returns:
            Updated resume document if found
        """
        # Remove None values and user_id from update
        filtered_data = {
            k: v for k, v in update_data.items() if v is not None and k != "user_id"
        }

        if not filtered_data:
            logger.info(
                "No changes to apply",
                extra={"event_type": "no_changes_detected", "user_id": user_id},
            )
            return None

        result = await self.find_one_and_update(
            {"user_id": user_id},
            {"$set": filtered_data},
        )

        if result:
            logger.info(
                "Resume updated",
                extra={"event_type": "resume_updated", "user_id": user_id},
            )

        return result

    async def delete_by_user_id(self, user_id: int) -> bool:
        """
        Delete a user's resume.

        Args:
            user_id: User's ID

        Returns:
            True if resume was deleted
        """
        deleted = await self.delete_one({"user_id": user_id})

        if deleted:
            logger.info(
                "Resume deleted",
                extra={"event_type": "resume_deleted", "user_id": user_id},
            )
        else:
            logger.warning(
                "Resume not found for deletion",
                extra={"event_type": "resume_not_found", "user_id": user_id},
            )

        return deleted

    async def user_has_resume(self, user_id: int) -> bool:
        """
        Check if user has a resume.

        Args:
            user_id: User's ID

        Returns:
            True if resume exists
        """
        return await self.exists({"user_id": user_id})
