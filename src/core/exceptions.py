"""Custom exceptions for the habit tracker application."""


class HabitTrackerException(Exception):
    """Base exception for all habit tracker errors."""

    pass


class RepositoryException(HabitTrackerException):
    """Base exception for repository layer errors."""

    pass


class UserRepositoryException(RepositoryException):
    """Exception for user repository operations."""

    pass


class UserAlreadyExistsException(UserRepositoryException):
    """Raised when attempting to create a user that already exists."""

    pass


class UserNotFoundException(UserRepositoryException):
    """Raised when a user cannot be found."""

    pass


class HabitRepositoryException(RepositoryException):
    """Exception for habit repository operations."""

    pass


class HabitAlreadyExistsException(HabitRepositoryException):
    """Raised when attempting to create a habit that already exists."""

    pass


class HabitNotFoundException(HabitRepositoryException):
    """Raised when a habit cannot be found."""

    pass


class DatabaseException(RepositoryException):
    """Raised when a database operation fails."""

    pass
