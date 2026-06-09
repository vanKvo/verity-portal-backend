from src.verity_portal.core.exceptions import DomainException

class ComplianceError(DomainException):
    """Base class for compliance-related errors."""
    def __init__(self, message: str):
        super().__init__(message)

class AuditDataInconsistencyError(ComplianceError):
    """Raised when records cannot be reconciled due to data format or missing critical keys."""
    def __init__(self, detail: str):
        super().__init__(f"Audit data inconsistency: {detail}")
