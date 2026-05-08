class DomainException(Exception):
    """Base class for all domain-specific exceptions."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class EntityNotFoundError(DomainException):
    """Raised when a requested entity is not found."""
    def __init__(self, entity_name: str, entity_id: str):
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} with ID {entity_id} not found.")

class ValidationError(DomainException):
    """Raised when domain validation fails."""
    def __init__(self, message: str):
        super().__init__(message)

class ComplianceError(DomainException):
    """Base class for compliance-related errors."""
    def __init__(self, message: str):
        super().__init__(message)

class AuditDataInconsistencyError(ComplianceError):
    """Raised when records cannot be reconciled due to data format or missing critical keys."""
    def __init__(self, detail: str):
        super().__init__(f"Audit data inconsistency: {detail}")

class MappingError(ComplianceError):
    """Raised when required mappings are missing for an audit."""
    def __init__(self, missing_fields: list[str]):
        self.missing_fields = missing_fields
        super().__init__(f"Missing required fields for audit: {', '.join(missing_fields)}")
