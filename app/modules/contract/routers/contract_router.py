from uuid import UUID
from pathlib import Path
import json

import shutil
import tempfile
from time import perf_counter

from fastapi import (
    APIRouter,
    Form,
    UploadFile,
    File,
    Depends,
    HTTPException,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import (
    get_db
)
from fastapi.responses import StreamingResponse
from backend.app.modules.contract.contract_advanced_logging import (
    contract_split_logger,
)
from backend.app.modules.contract.services.contract_service import (
    ContractService,
)
from backend.app.modules.contract.services.contract_advanced_service import (
    ContractAdvancedService,
)
from backend.app.modules.contract.services.legal_chat_service import LegalChatService
from backend.app.modules.contract.services.legal_contract_analysis_service import (
    LegalContractAnalysisService,
)
from backend.app.modules.contract.schemas.contract_chat_request import ( ContractChatRequest)
from backend.app.modules.contract.schemas.contract_advanced_request import (
    ContractLegalReviewRequest,
    LegalChatRequest,
)

router = APIRouter(

    prefix="/contracts",

    tags=["Contracts"],

)



@router.post("/analyze")

async def analyze_contract(

    file: UploadFile = File(...),

    model_id: UUID = Form(...),

    db: AsyncSession = Depends(
        get_db,
    ),

):

    suffix = (
        ".pdf"
        if file.filename.lower().endswith(".pdf")
        else ".docx"
    )

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as tmp:

        shutil.copyfileobj(
            file.file,
            tmp,
        )

        file_path = tmp.name

    return await (

        ContractService()

        .analyze(

            db=db,

            file_path=file_path,

            model_id=model_id,

        )

    )
    
    

@router.post("/analyze-advanced")
async def analyze_contract_advanced(
    file: UploadFile = File(...),
    model_id: UUID = Form(...),
    db: AsyncSession = Depends(get_db),
):

    suffix = Path(
        file.filename or ""
    ).suffix.lower()

    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported.",
        )

    file_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as tmp:
            file_path = tmp.name
            shutil.copyfileobj(
                file.file,
                tmp,
            )

        return await (
            ContractAdvancedService()
            .analyze(
                db=db,
                file_path=file_path,
                model_id=model_id,
            )
        )
    finally:
        if file_path:
            Path(file_path).unlink(
                missing_ok=True
            )


@router.post("/analyze-advanced/company-rule")
async def analyze_contract_advanced_company_rule(
    file: UploadFile = File(...),
    model_id: UUID = Form(...),
    db: AsyncSession = Depends(get_db),
):
    request_started_at = perf_counter()
    suffix = Path(file.filename or "").suffix.lower()

    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported.",
        )

    file_path = None

    try:
        upload_started_at = perf_counter()
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as tmp:
            file_path = tmp.name
            shutil.copyfileobj(file.file, tmp)

        contract_split_logger.info(
            "[CONTRACT_COMPANY_RULE][TIMING] upload=%.3fs "
            "filename=%s",
            perf_counter() - upload_started_at,
            file.filename,
        )
        response = await ContractAdvancedService().analyze_company_rule(
            db=db,
            file_path=file_path,
            model_id=model_id,
        )
        contract_split_logger.info(
            "[CONTRACT_COMPANY_RULE][TIMING] api_total=%.3fs",
            perf_counter() - request_started_at,
        )
        return response
    except Exception:
        contract_split_logger.exception(
            "[CONTRACT_COMPANY_RULE] failed after %.3fs",
            perf_counter() - request_started_at,
        )
        raise
    finally:
        if file_path:
            Path(file_path).unlink(missing_ok=True)


@router.post("/analyze-advanced/legal")
async def analyze_contract_advanced_legal(
    request: ContractLegalReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    service = LegalContractAnalysisService()

    async def stream_response():
        async for item in service.analyze(
            db=db,
            model_id=request.model_id,
            output_extract=request.output_extract,
        ):
            yield (
                f"event: {item['event']}\n"
                f"data: {json.dumps(item['data'], ensure_ascii=False)}\n\n"
            )

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/legal-chat")
async def legal_chat(
    request: LegalChatRequest,
    db: AsyncSession = Depends(get_db),
):
    return await LegalChatService().chat(
        db=db,
        model_id=request.model_id,
        question=request.question,
        extracted_contract=request.extracted_contract,
    )


@router.post(
    "/chat",
)
async def contract_chat(

    request: ContractChatRequest,

    db: AsyncSession = Depends(
        get_db,
    ),

):

    return await (

        ContractService
        .chat(

            db=db,

            question=request.question,

            model_id=request.model_id,
            
            contract_id=request.contract_id,

        )

    )
    
    
@router.get("")
async def get_contracts(

    db: AsyncSession = Depends(
        get_db,
    ),

):

    return await (

        ContractService
        .get_contracts(

            db=db,

        )

    )
    
@router.get("/{contract_id}")
async def get_contract(

    contract_id: UUID,

    db: AsyncSession = Depends(
        get_db,
    ),

):

    return await (

        ContractService
        .get_contract(

            db=db,

            contract_id=contract_id,

        )

    )
