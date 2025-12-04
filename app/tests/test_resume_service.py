# app/tests/test_resume_service.py
"""
Unit tests for the resume_service module.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymongo.errors import ConnectionFailure, OperationFailure

from app.core.exceptions import DatabaseOperationError
from app.services.resume_service import (
    add_resume,
    delete_resume,
    generate_resume_json_from_pdf,
    get_resume_by_user_id,
    update_resume,
    user_has_resume,
)


class TestGetResumeByUserId:
    """Tests for get_resume_by_user_id function."""

    @pytest.mark.asyncio
    async def test_get_resume_success(self, mongo_mock, valid_resume_data):
        """Test successful resume retrieval."""
        expected_resume = {
            "_id": "507f1f77bcf86cd799439011",
            "user_id": 1,
            **valid_resume_data,
        }
        mongo_mock.find_one.return_value = expected_resume

        result = await get_resume_by_user_id(user_id=1)

        assert result["user_id"] == 1
        assert result["_id"] == "507f1f77bcf86cd799439011"
        mongo_mock.find_one.assert_called_once_with({"user_id": 1})

    @pytest.mark.asyncio
    async def test_get_resume_with_version(self, mongo_mock, valid_resume_data):
        """Test resume retrieval with version filter."""
        expected_resume = {
            "_id": "507f1f77bcf86cd799439011",
            "user_id": 1,
            "version": "v2",
            **valid_resume_data,
        }
        mongo_mock.find_one.return_value = expected_resume

        result = await get_resume_by_user_id(user_id=1, version="v2")

        mongo_mock.find_one.assert_called_once_with({"user_id": 1, "version": "v2"})

    @pytest.mark.asyncio
    async def test_get_resume_not_found(self, mongo_mock):
        """Test resume retrieval when not found."""
        mongo_mock.find_one.return_value = None

        result = await get_resume_by_user_id(user_id=999)

        assert "error" in result
        assert "Resume not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_resume_connection_failure(self, mongo_mock):
        """Test handling of database connection failure."""
        mongo_mock.find_one.side_effect = ConnectionFailure("Connection failed")

        with pytest.raises(DatabaseOperationError) as exc_info:
            await get_resume_by_user_id(user_id=1)

        assert "Database connection failed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_resume_operation_failure(self, mongo_mock):
        """Test handling of database operation failure."""
        mongo_mock.find_one.side_effect = OperationFailure("Query failed")

        with pytest.raises(DatabaseOperationError) as exc_info:
            await get_resume_by_user_id(user_id=1)

        assert "Database query failed" in str(exc_info.value.detail)


class TestAddResume:
    """Tests for add_resume function."""

    @pytest.mark.asyncio
    async def test_add_resume_success_no_existing(self, mongo_mock, valid_resume_data):
        """Test successful resume creation when no existing resume."""
        # First call: check existing (None), Second call: get inserted
        mongo_mock.find_one.side_effect = [
            None,  # No existing resume
            {"_id": "new_id", "user_id": 1, **valid_resume_data},
        ]
        mongo_mock.insert_one.return_value = MagicMock(inserted_id="new_id")

        mock_resume = MagicMock()
        mock_resume.model_dump.return_value = valid_resume_data

        result = await add_resume(resume=mock_resume, current_user=1)

        assert result["_id"] == "new_id"
        assert result["user_id"] == 1

    @pytest.mark.asyncio
    async def test_add_resume_replaces_existing(self, mongo_mock, valid_resume_data):
        """Test resume creation replaces existing resume."""
        # First call: existing resume found, Second call: get new resume
        mongo_mock.find_one.side_effect = [
            {"_id": "old_id", "user_id": 1},  # Existing resume
            {"_id": "new_id", "user_id": 1, **valid_resume_data},
        ]
        mongo_mock.delete_one.return_value = MagicMock(deleted_count=1)
        mongo_mock.insert_one.return_value = MagicMock(inserted_id="new_id")

        mock_resume = MagicMock()
        mock_resume.model_dump.return_value = valid_resume_data

        result = await add_resume(resume=mock_resume, current_user=1)

        mongo_mock.delete_one.assert_called_once_with({"user_id": 1})
        assert result["_id"] == "new_id"

    @pytest.mark.asyncio
    async def test_add_resume_connection_failure(self, mongo_mock, valid_resume_data):
        """Test handling of connection failure during add."""
        mongo_mock.find_one.side_effect = ConnectionFailure("Connection failed")

        mock_resume = MagicMock()
        mock_resume.model_dump.return_value = valid_resume_data

        with pytest.raises(DatabaseOperationError):
            await add_resume(resume=mock_resume, current_user=1)


class TestUpdateResume:
    """Tests for update_resume function."""

    @pytest.mark.asyncio
    async def test_update_resume_success(self, mongo_mock, valid_resume_data):
        """Test successful resume update."""
        existing_resume = {"_id": "test_id", "user_id": 1, **valid_resume_data}
        updated_resume = {
            **existing_resume,
            "personal_information": {
                **valid_resume_data["personal_information"],
                "city": "Los Angeles",
            },
        }

        mongo_mock.find_one.return_value = existing_resume
        mongo_mock.find_one_and_update.return_value = updated_resume

        mock_resume = MagicMock()
        mock_resume.model_dump.return_value = {
            **valid_resume_data,
            "personal_information": {
                **valid_resume_data["personal_information"],
                "city": "Los Angeles",
            },
        }

        result = await update_resume(resume=mock_resume, user_id=1)

        assert result["_id"] == "test_id"
        mongo_mock.find_one_and_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_resume_not_found(self, mongo_mock, valid_resume_data):
        """Test update when resume doesn't exist."""
        mongo_mock.find_one.return_value = None

        mock_resume = MagicMock()
        mock_resume.model_dump.return_value = valid_resume_data

        result = await update_resume(resume=mock_resume, user_id=999)

        assert "error" in result
        assert "Resume not found" in result["error"]

    @pytest.mark.asyncio
    async def test_update_resume_no_changes(self, mongo_mock, valid_resume_data):
        """Test update when no changes detected."""
        existing_resume = {"_id": "test_id", "user_id": 1, **valid_resume_data}
        mongo_mock.find_one.return_value = existing_resume

        mock_resume = MagicMock()
        mock_resume.model_dump.return_value = valid_resume_data

        result = await update_resume(resume=mock_resume, user_id=1)

        assert result == {"message": "No changes detected"}
        mongo_mock.find_one_and_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_resume_connection_failure(self, mongo_mock, valid_resume_data):
        """Test handling of connection failure during update."""
        mongo_mock.find_one.side_effect = ConnectionFailure("Connection failed")

        mock_resume = MagicMock()
        mock_resume.model_dump.return_value = valid_resume_data

        with pytest.raises(DatabaseOperationError):
            await update_resume(resume=mock_resume, user_id=1)


class TestDeleteResume:
    """Tests for delete_resume function."""

    @pytest.mark.asyncio
    async def test_delete_resume_success(self, mongo_mock):
        """Test successful resume deletion."""
        mongo_mock.find_one.return_value = {"_id": "test_id", "user_id": 1}
        mongo_mock.delete_one.return_value = MagicMock(deleted_count=1)

        result = await delete_resume(user_id=1)

        assert "message" in result
        assert "deleted successfully" in result["message"]
        mongo_mock.delete_one.assert_called_once_with({"user_id": 1})

    @pytest.mark.asyncio
    async def test_delete_resume_not_found(self, mongo_mock):
        """Test deletion when resume doesn't exist."""
        mongo_mock.find_one.return_value = None

        result = await delete_resume(user_id=999)

        assert "error" in result
        assert "Resume not found" in result["error"]

    @pytest.mark.asyncio
    async def test_delete_resume_failed(self, mongo_mock):
        """Test deletion failure (resume exists but delete fails)."""
        mongo_mock.find_one.return_value = {"_id": "test_id", "user_id": 1}
        mongo_mock.delete_one.return_value = MagicMock(deleted_count=0)

        result = await delete_resume(user_id=1)

        assert "error" in result
        assert "Failed to delete" in result["error"]

    @pytest.mark.asyncio
    async def test_delete_resume_connection_failure(self, mongo_mock):
        """Test handling of connection failure during delete."""
        mongo_mock.find_one.side_effect = ConnectionFailure("Connection failed")

        with pytest.raises(DatabaseOperationError):
            await delete_resume(user_id=1)


class TestUserHasResume:
    """Tests for user_has_resume function."""

    @pytest.mark.asyncio
    async def test_user_has_resume_true(self, mongo_mock):
        """Test when user has a resume."""
        mongo_mock.find_one.return_value = {"_id": "test_id"}

        result = await user_has_resume(user_id=1)

        assert result is True
        mongo_mock.find_one.assert_called_once_with(
            {"user_id": 1}, projection={"_id": 1}
        )

    @pytest.mark.asyncio
    async def test_user_has_resume_false(self, mongo_mock):
        """Test when user doesn't have a resume."""
        mongo_mock.find_one.return_value = None

        result = await user_has_resume(user_id=999)

        assert result is False

    @pytest.mark.asyncio
    async def test_user_has_resume_connection_failure(self, mongo_mock):
        """Test handling of connection failure."""
        mongo_mock.find_one.side_effect = ConnectionFailure("Connection failed")

        with pytest.raises(DatabaseOperationError):
            await user_has_resume(user_id=1)


class TestGenerateResumeJsonFromPdf:
    """Tests for generate_resume_json_from_pdf function."""

    @pytest.mark.asyncio
    async def test_generate_resume_json_success(self, sample_pdf_bytes):
        """Test successful resume JSON generation from PDF."""
        expected_result = {"name": "John Doe", "email": "john@example.com"}

        with patch(
            "app.services.resume_service.resume_parser.generate_resume_from_pdf_bytes",
            new_callable=AsyncMock,
            return_value=expected_result,
        ):
            result = await generate_resume_json_from_pdf(sample_pdf_bytes)

            assert result == expected_result
