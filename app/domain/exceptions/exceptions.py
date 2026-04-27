class DomainException(Exception):
    """Base class for all domain exceptions"""
    pass

class InvariantViolationError(DomainException):
    """Raised when a business invariant is violated"""
    pass

class EntityNotFoundError(DomainException):
    """Raised when an entity is not found"""
    pass

class EmailAlreadyExistsError(InvariantViolationError):
    """Raised when an email is already in use"""
    pass

class NicknameAlreadyExistsError(InvariantViolationError):
    """Raised when a nickname is already in use"""
    pass

class InvalidEmailError(InvariantViolationError):
    """Raised when an email is invalid"""
    pass
