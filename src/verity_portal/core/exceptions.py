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

class MappingError(DomainException):
    """Raised when required mappings are missing for an audit."""
    def __init__(self, missing_fields: list[str]):
        self.missing_fields = missing_fields
        super().__init__(f"Missing required fields for audit: {', '.join(missing_fields)}")

class FileTooLargeError(DomainException):
    """Raised when an uploaded file exceeds the allowed size limit."""
    def __init__(self, max_size_mb: int, actual_size_bytes: int):
        self.max_size_mb = max_size_mb
        self.actual_size_mb = actual_size_bytes / (1024 * 1024)
        super().__init__(f"File size exceeds {max_size_mb}MB limit")
