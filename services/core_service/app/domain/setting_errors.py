from typing import Optional


class SettingError(Exception):
    """
    Base class for all Setting domain errors
    """
    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code
        super().__init__(message)


class SettingNotFound(SettingError):
    """
    Raised when:
    - Survey not found
    - Settings not found for a survey
    """
    def __init__(self, message: str = "Settings not found"):
        super().__init__(
            message=message,
            code="SETTING_NOT_FOUND"
        )


class SettingForbidden(SettingError):
    """
    Raised when user tries to access or modify
    settings of a survey he does not own
    """
    def __init__(self, message: str = "You are not allowed to access these settings"):
        super().__init__(
            message=message,
            code="SETTING_FORBIDDEN"
        )


class SettingValidationError(SettingError):
    """
    Raised when business rules are violated
    """
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="SETTING_VALIDATION_ERROR"
        )


class SettingActivationError(SettingValidationError):
    """
    Raised specifically when activation rules fail
    (dates, questions count, etc.)
    """
    def __init__(self, message: str):
        super().__init__(message)
        self.code = "SETTING_ACTIVATION_ERROR"
