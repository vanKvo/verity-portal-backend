from src.verity_portal.core.exceptions import ValidationError

class ITARMappingError(ValidationError):
    """Raised when data mapping fails for ITAR roster."""
    def __init__(self, message: str):
        super().__init__(message)
