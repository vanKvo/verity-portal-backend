"""Presentation router layer for the Data Hub feature slice.

This module acts strictly as a thin coordination traffic controller that receives
HTTP requests, validates inbound multipart/payload schemas, delegates all business
orchestrations and transactional evaluations to the DataHubOrchestrationService, and
standardizes exception handling to present clean, structured response payloads.
"""
import logging
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status

from src.verity_portal.core.security.roles import require_role
from src.verity_portal.data_hub.core.ingestion import DataHubOrchestrationService, get_orchestration_service
from src.verity_portal.data_hub.core.retrieval import RetrievalStrategyFactory
from src.verity_portal.data_hub.exceptions import DataHubRetrievalError, IngestionRoutingError, MappingParseError
from src.verity_portal.data_hub.schemas import (
    HeaderParsingResponse,
    IngestionResponse,
    S3SyncTriggeredResponse,
    SyncStatusResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data-hub", tags=["Data Hub"])


@router.post("/parse-headers", response_model=HeaderParsingResponse, status_code=status.HTTP_200_OK)
async def parse_headers(
    file: UploadFile = File(...),
    orchestration_service: DataHubOrchestrationService = Depends(get_orchestration_service),
) -> HeaderParsingResponse:
    """Extracts column headers from CSV, Excel, or Numbers files for frontend mapping.

    Args:
        file: The uploaded multipart file wrapper object.
        orchestration_service: The injected orchestration coordination service.

    Returns:
        A HeaderParsingResponse DTO listing the string headers.

    Raises:
        HTTPException: If parsing fails or the document format is invalid.
    """
    strategy = RetrievalStrategyFactory.get_manual_strategy(file)
    try:
        headers = await orchestration_service.extract_headers(strategy)
        return HeaderParsingResponse(headers=headers)
    except DataHubRetrievalError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "RETRIEVAL_FAILED",
                "message": f"Failed to retrieve document stream: {exc.detail}",
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_FILE_STRUCTURE",
                "message": f"The document is empty or lacks clear header columns: {str(exc)}",
            },
        ) from exc
    except Exception as exc:
        logger.exception("Failed in parsing hearders")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred during header extraction.",
            },
        ) from exc


@router.post(
    "/personnel/upload",
    response_model=IngestionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("ROLE_HR"))],
)
async def upload_hr_data(
    file: UploadFile = File(...),
    mapping: Optional[str] = Form(None),
    orchestration_service: DataHubOrchestrationService = Depends(get_orchestration_service),
) -> IngestionResponse:
    """Manual upload endpoint for HR Master Data (Citizenship, Termination).

    Enforces strict ROLE_HR role authorization before processing.

    Args:
        file: The uploaded multipart spreadsheet file.
        mapping: Optional stringified JSON mapping object for header mapping.
        orchestration_service: The injected orchestration coordination service.

    Returns:
        An IngestionResponse DTO showing counts of success/failed rows and details.

    Raises:
        HTTPException: If ingestion, parsing, or column mapping fails.
    """
    strategy = RetrievalStrategyFactory.get_manual_strategy(file)
    try:
        result = await orchestration_service.process_manual_upload(
            strategy=strategy, mapping_str=mapping, target_service_type="personnel"
        )
        return IngestionResponse(**result)
    except MappingParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_MAPPING_FORMAT",
                "message": f"The column mapping JSON payload is invalid: {exc.detail}",
            },
        ) from exc
    except DataHubRetrievalError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "RETRIEVAL_FAILED",
                "message": f"Failed to retrieve upload file details: {exc.detail}",
            },
        ) from exc
    except Exception as exc:
        logger.exception("Failed in uploading HR data")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred during HR data upload.",
            },
        ) from exc


@router.post(
    "/projects/upload",
    response_model=IngestionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("ROLE_ECO"))],
)
async def upload_project_data(
    file: UploadFile = File(...),
    mapping: Optional[str] = Form(None),
    orchestration_service: DataHubOrchestrationService = Depends(get_orchestration_service),
) -> IngestionResponse:
    """Manual upload endpoint for Project Master Data (Sensitivity).

    Enforces strict ROLE_ECO role authorization before processing.

    Args:
        file: The uploaded multipart spreadsheet file.
        mapping: Optional stringified JSON mapping object for header mapping.
        orchestration_service: The injected orchestration coordination service.

    Returns:
        An IngestionResponse DTO showing counts of success/failed rows and details.

    Raises:
        HTTPException: If ingestion, parsing, or column mapping fails.
    """
    strategy = RetrievalStrategyFactory.get_manual_strategy(file)
    try:
        result = await orchestration_service.process_manual_upload(
            strategy=strategy, mapping_str=mapping, target_service_type="projects"
        )
        return IngestionResponse(**result)
    except MappingParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_MAPPING_FORMAT",
                "message": f"The column mapping JSON payload is invalid: {exc.detail}",
            },
        ) from exc
    except DataHubRetrievalError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "RETRIEVAL_FAILED",
                "message": f"Failed to retrieve upload file details: {exc.detail}",
            },
        ) from exc
    except Exception as exc:
        logger.exception("Failed in uploading project data")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred during Project data upload.",
            },
        ) from exc


@router.post(
    "/procurement/upload",
    response_model=IngestionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("ROLE_FINANCE"))],
)
async def upload_procurement_data(
    file: UploadFile = File(...),
    mapping: Optional[str] = Form(None),
    orchestration_service: DataHubOrchestrationService = Depends(get_orchestration_service),
) -> IngestionResponse:
    """Manual upload endpoint for Procurement PO Data.

    Enforces strict ROLE_FINANCE role authorization before processing.

    Args:
        file: The uploaded multipart spreadsheet file.
        mapping: Optional stringified JSON mapping object for header mapping.
        orchestration_service: The injected orchestration coordination service.

    Returns:
        An IngestionResponse DTO showing counts of success/failed rows and details.

    Raises:
        HTTPException: If ingestion, parsing, or column mapping fails.
    """
    strategy = RetrievalStrategyFactory.get_manual_strategy(file)
    try:
        result = await orchestration_service.process_manual_upload(
            strategy=strategy, mapping_str=mapping, target_service_type="procurement"
        )
        return IngestionResponse(**result)
    except MappingParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_MAPPING_FORMAT",
                "message": f"The column mapping JSON payload is invalid: {exc.detail}",
            },
        ) from exc
    except DataHubRetrievalError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "RETRIEVAL_FAILED",
                "message": f"Failed to retrieve upload file details: {exc.detail}",
            },
        ) from exc
    except Exception as exc:
        logger.exception("Failed in uploading procurement data")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred during Procurement data upload.",
            },
        ) from exc


@router.post(
    "/inventory/upload",
    response_model=IngestionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("ROLE_IT"))],
)
async def upload_inventory_data(
    file: UploadFile = File(...),
    mapping: Optional[str] = Form(None),
    orchestration_service: DataHubOrchestrationService = Depends(get_orchestration_service),
) -> IngestionResponse:
    """Manual upload endpoint for IT Inventory Data.

    Enforces strict ROLE_IT role authorization before processing.

    Args:
        file: The uploaded multipart spreadsheet file.
        mapping: Optional stringified JSON mapping object for header mapping.
        orchestration_service: The injected orchestration coordination service.

    Returns:
        An IngestionResponse DTO showing counts of success/failed rows and details.

    Raises:
        HTTPException: If ingestion, parsing, or column mapping fails.
    """
    strategy = RetrievalStrategyFactory.get_manual_strategy(file)
    try:
        result = await orchestration_service.process_manual_upload(
            strategy=strategy, mapping_str=mapping, target_service_type="inventory"
        )
        return IngestionResponse(**result)
    except MappingParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_MAPPING_FORMAT",
                "message": f"The column mapping JSON payload is invalid: {exc.detail}",
            },
        ) from exc
    except DataHubRetrievalError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "RETRIEVAL_FAILED",
                "message": f"Failed to retrieve upload file details: {exc.detail}",
            },
        ) from exc
    except Exception as exc:
        logger.exception("Failed in uploading inventory data")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred during IT Inventory data upload.",
            },
        ) from exc


@router.post("/webhooks/s3-ingest", response_model=S3SyncTriggeredResponse, status_code=status.HTTP_200_OK)
async def s3_webhook_ingest(
    payload: dict,
    background_tasks: BackgroundTasks,
    orchestration_service: DataHubOrchestrationService = Depends(get_orchestration_service),
) -> S3SyncTriggeredResponse:
    """Webhook triggered by an S3 notification event to sync HR or Project master records.

    Asynchronously queues a background task to fetch and process the file from S3.

    Args:
        payload: The raw JSON dictionary containing the S3 event notification payload.
        background_tasks: The FastAPI BackgroundTasks manager to queue downstream processing.
        orchestration_service: The injected orchestration coordination service.

    Returns:
        An S3SyncTriggeredResponse DTO confirming bucket and key names.

    Raises:
        HTTPException: If the payload is malformed or invalid.
    """
    records = payload.get("Records", [])
    if not records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "MALFORMED_PAYLOAD",
                "message": "Malformed S3 event payload: 'Records' list is missing or empty.",
            },
        )
    
    s3_data = records[0].get("s3", {})
    bucket_name = s3_data.get("bucket", {}).get("name")
    object_key = s3_data.get("object", {}).get("key")
    
    if not bucket_name or not object_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "MALFORMED_PAYLOAD",
                "message": "Malformed S3 event payload: bucket name or object key is missing.",
            },
        )
    
    try:
        background_tasks.add_task(orchestration_service.perform_s3_ingestion, bucket_name, object_key)
        return S3SyncTriggeredResponse(
            message="S3 Sync Triggered",
            bucket=bucket_name,
            key=object_key,
        )
    except IngestionRoutingError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "ROUTING_FAILED",
                "message": f"S3 event could not be dynamically routed: {exc.detail}",
            },
        ) from exc
    except Exception as exc:
        logger.exception("Failed in ingesting data from S3")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred queueing the S3 webhook task.",
            },
        ) from exc


@router.get("/sync-status", response_model=SyncStatusResponse, status_code=status.HTTP_200_OK)
async def get_sync_status(
    orchestration_service: DataHubOrchestrationService = Depends(get_orchestration_service),
) -> SyncStatusResponse:
    """Retrieves the last sync/update timestamps for both personnel and project master profiles.

    Args:
        orchestration_service: The injected orchestration coordination service.

    Returns:
        A SyncStatusResponse containing ISO formatting string synchronization dates or None.

    Raises:
        HTTPException: If query execution fails.
    """
    try:
        status_data = orchestration_service.get_sync_status()
        return SyncStatusResponse(**status_data)
    except Exception as exc:
        logger.exception("Failed in getting sync status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected database error occurred retrieving synchronization statuses.",
            },
        ) from exc