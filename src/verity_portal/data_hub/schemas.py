"""Presentation schemas and DTOs for the Data Hub.

This module defines standard Pydantic models for incoming and outgoing HTTP request 
and response payloads at the presentation boundaries of the Data Hub.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class HeaderParsingResponse(BaseModel):
    """Payload representing extracted file headers returned to the frontend."""

    headers: List[str] = Field(
        ..., 
        description="List of raw column headers extracted from the parsed document sheet."
    )


class IngestionErrorDetail(BaseModel):
    """Details of a single row validation or database error during bulk ingestion."""

    row: int = Field(
        ..., 
        description="The 1-based row index in the spreadsheet where the failure occurred."
    )
    error: str = Field(
        ..., 
        description="Human-readable and structural error detail message explaining the failure."
    )


class IngestionResponse(BaseModel):
    """Summary payload of manual CSV/spreadsheet master data ingestion runs."""

    success_count: int = Field(
        ..., 
        description="Total number of successfully validated and upserted database rows."
    )
    error_count: int = Field(
        ..., 
        description="Total number of spreadsheet rows that failed validation or insertion."
    )
    errors: List[IngestionErrorDetail] = Field(
        default_factory=list, 
        description="A list containing up to the first 20 errors encountered during processing."
    )


class S3SyncTriggeredResponse(BaseModel):
    """Response returned upon successfully queueing a background webhook S3 sync event."""

    message: str = Field(
        ..., 
        description="Status message confirming the S3 synchronization task was successfully queued."
    )
    bucket: str = Field(
        ..., 
        description="The target S3 bucket name source."
    )
    key: str = Field(
        ..., 
        description="The target S3 object key identifier."
    )


class SyncStatusResponse(BaseModel):
    """Timestamps of the latest synchronization events for master data profiles."""

    personnel_last_sync: Optional[str] = Field(
        None, 
        description="ISO 8601 formatted date-time string of the last updated personnel profile, or None."
    )
    projects_last_sync: Optional[str] = Field(
        None, 
        description="ISO 8601 formatted date-time string of the last updated projects master record, or None."
    )
    procurement_last_sync: Optional[str] = Field(
        None, 
        description="ISO 8601 formatted date-time string of the last updated procurement record, or None."
    )
    inventory_last_sync: Optional[str] = Field(
        None, 
        description="ISO 8601 formatted date-time string of the last updated inventory master record, or None."
    )
