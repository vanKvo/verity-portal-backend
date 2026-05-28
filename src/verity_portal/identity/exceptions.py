from src.verity_portal.core.exceptions import ValidationError, DomainException

class InvalidDomainError(ValidationError):
    """Raised when a user email domain is not authorized."""
    def __init__(self, domain: str):
        super().__init__(f"Domain {domain} is not authorized.")

class UserAlreadyExistsError(DomainException):
    """Raised when a user with the given email is already registered."""
    def __init__(self, email: str):
        super().__init__(f"Email {email} is already registered.")

class IncorrectCredentialsError(DomainException):
    """Raised when login password or username is incorrect."""
    def __init__(self):
        super().__init__("Incorrect email or password.")

class InactiveUserError(DomainException):
    """Raised when a disabled or inactive user tries to authenticate."""
    def __init__(self, email: str):
        super().__init__(f"User account {email} is inactive or disabled.")

class TokenValidationError(DomainException):
    """Raised when refresh token validation fails."""
    def __init__(self, message: str, error_code: str):
        super().__init__(message)
        self.error_code = error_code
