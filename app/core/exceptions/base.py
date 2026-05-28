class CustomException(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code

class EntityNotFoundError(CustomException):
    def __init__(self, message: str = "Entity not found"):
        super().__init__(message, code="NOT_FOUND")

class BusinessRuleViolationError(CustomException):
    def __init__(self, message: str):
        super().__init__(message, code="BUSINESS_RULE_VIOLATION")

class ExternalAPIError(CustomException):
    def __init__(self, message: str, service: str):
        super().__init__(f"Error in {service}: {message}", code="EXTERNAL_API_ERROR")
        self.service = service

class TranscriptionError(CustomException):
    def __init__(self, message: str):
        super().__init__(message, code="TRANSCRIPTION_ERROR")
