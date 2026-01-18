import logging

logging.basicConfig(level=logging.ERROR)

class BaseError(Exception):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

    def to_dict(self):
        return {"message": self.message, "status_code": self.status_code}
    
    def log_error(self):
        # This method can be overridden to log the error details
        logging.error(f"Error {self.status_code}: {self.message}")

class DatabaseError(BaseError):
    def __init__(self, error_func=None):
        message = "Database Query Failed" if not error_func else f"Database Query Failed At {error_func}"
        super().__init__(message=message, status_code=500)

class ValidationError(BaseError):
    def __init__(self, specific_reason=None):
        message = "Validation Failed"
        if specific_reason:
            message += f": {specific_reason}"
        super().__init__(message=message, status_code=400)

class FileuploadError(BaseError):
    def __init__(self, message="File Upload Failed"):
        super().__init__(message=message, status_code=400)
        # incase there is specificity (file too large, invalid file type) I want to add it to the message

class AuthenticationError(BaseError):
    def __init__(self, specific_reason=None):
        message = "Authentication Failed"
        if specific_reason:
            message += f": {specific_reason}"
        super().__init__(message=message, status_code=401)
    # Error code and message should stay the same, but message should be expanded upon for specificity.
    # Authentication errors should also include specific reasons for the failure,
    # like incorrect username/password, account locked, etc.

class RestrictedError(BaseError):
    def __init__(self, specific_reason=None):
        message = "Method Not Allowed"
        if specific_reason:
            message += f": {specific_reason}"
        super().__init__(message=message, status_code=403)

class RateLimitError(BaseError):
    """Raised when rate limit is exceeded"""
    def __init__(self, message="Rate limit exceeded"):
        super().__init__(message, status_code=429)

    
class NotFoundError(BaseError):
    def __init__(self, item=None):
        message = "Resource Not Found" if not item else f"{item} Not Found"
        super().__init__(message=message, status_code=404)


class UserNotFound(BaseError):
    def __init__(self, username):
        self.message = f"User '{username}' not found"
        self.status_code = 404
        super().__init__(message=self.message, status_code=self.status_code)


