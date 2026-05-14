from src.verity_portal.core.exceptions import ValidationError

class InvalidDomainError(ValidationError):
    """Raised when a user email domain is not authorized."""
    def __init__(self, domain: str):
        super().__init__(f"Domain {domain} is not authorized.")
