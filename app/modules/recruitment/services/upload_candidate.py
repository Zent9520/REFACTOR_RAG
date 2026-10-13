from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.bad_request_exception import (
    BadRequestException,
)
from backend.app.repositories.recruitment.recruitment_candidate_repository import (
    RecruitmentCandidateRepository,
)
from app.utils.storage.supabase_storage import (
    SupabaseStorage,
)


class UploadCandidateService:

    MAX_FILE_SIZE = 5 * 1024 * 1024

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".doc",
        ".docx",
    }

    @staticmethod
    async def execute(
        db: AsyncSession,
        campaign_id: UUID,
        file: UploadFile,
    ):
        if not file.filename:
            raise BadRequestException(
                "Tên file không hợp lệ."
            )

        extension = (
            Path(file.filename)
            .suffix
            .lower()
        )

        if extension not in UploadCandidateService.ALLOWED_EXTENSIONS:
            raise BadRequestException(
                "Chỉ hỗ trợ file PDF, DOC hoặc DOCX."
            )

        file_bytes = await file.read()

        if len(file_bytes) > UploadCandidateService.MAX_FILE_SIZE:
            raise BadRequestException(
                "Dung lượng file không được vượt quá 5 MB."
            )

        file_path = await SupabaseStorage.upload_cv(
            file_bytes=file_bytes,
            file_name=file.filename,
            content_type=file.content_type
            or "application/octet-stream",
        )

        return await RecruitmentCandidateRepository.create(
            db=db,
            campaign_id=campaign_id,
            candidate_name=None,
            file_name=file.filename,
            file_path=file_path,
            file_size=len(file_bytes),
            mime_type=file.content_type,
        )