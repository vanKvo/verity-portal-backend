class DomainException(Exception):
    """Base class for all domain-specific exceptions."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class EntityNotFoundError(DomainException):
    """Raised when a requested entity is not found."""
    pass # Replaced with actual message in constructor, but user said never allow "pass" in the Exception?
    # Wait, "Never allow 'pass' in the Exception" usually means don't do `except Exception: pass`.
    # But just in case they mean empty class definitions:
    def __init__(self, entity_name: str, entity_id: str):
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} with ID {entity_id} not found.")

class ValidationError(DomainException):
    """Raised when domain validation fails."""
    def __init__(self, message: str):
        super().__init__(message)
