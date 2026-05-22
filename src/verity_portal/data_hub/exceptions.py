"""Custom domain-specific exceptions for the Data Hub feature layer.

All exceptions inherit from the base DomainException class defined in core,
allowing features to stop execution instantly when secure structural contracts
or formatting rules are violated.
"""

from src.verity_portal.core.exceptions import DomainException


class DataHubRetrievalError(DomainException):
    """Raised when data retrieval from an integration source (like S3 or Uploads) fails."""
    def __init__(self, source_type: str, source_identifier: str, detail: str) -> None:
        self.source_type: str = source_type
        self.source_identifier: str = source_identifier
        self.detail: str = detail
        super().__init__(f"Failed to retrieve data from {source_type} '{source_identifier}': {detail}")


class IngestionRoutingError(DomainException):
    """Raised when an ingested file cannot be mapped or routed to a target service."""
    def __init__(self, filename: str, detail: str) -> None:
        self.filename: str = filename
        self.detail: str = detail
        super().__init__(f"Failed to route ingested file '{filename}': {detail}")


class MappingParseError(DomainException):
    """Raised when the column mapping configuration payload is not valid JSON."""
    def __init__(self, detail: str) -> None:
        self.detail: str = detail
        super().__init__(f"Invalid CSV mapping configuration: {detail}")

