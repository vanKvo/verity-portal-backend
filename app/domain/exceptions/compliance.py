from .base import DomainException

class ComplianceException(DomainException):
    """Base for all compliance-related exceptions."""
    def __init__(self, message: str):
        super().__init__(message)

class AuditDataInconsistencyError(ComplianceException):
    """Raised when records cannot be reconciled due to data format or missing critical keys."""
    def __init__(self, detail: str):
        super().__init__(f"Audit data inconsistency: {detail}")

class MappingError(ComplianceException):
    """Raised when required mappings are missing for an audit."""
    def __init__(self, missing_fields: list[str]):
        self.missing_fields = missing_fields
        super().__init__(f"Missing required fields for audit: {', '.join(missing_fields)}")
