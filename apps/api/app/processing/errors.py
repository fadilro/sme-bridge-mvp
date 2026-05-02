class ProcessingError(Exception):
    """Base class for all background processing exceptions."""
    pass

class UnreadableFileError(ProcessingError):
    """
    Raised when a file cannot be loaded, decrypted, or decoded.
    For example: corrupt PDFs, password-protected files, or unsupported formats.
    """
    pass

class LLMInferenceError(ProcessingError):
    """
    Raised when the LLM fails to return a response or returns a completely
    unparseable response that cannot be recovered.
    """
    pass

class ProcessingHardwareError(ProcessingError):
    """
    Raised for transient hardware issues, like memory exhaustion
    or GPU unavailability, suggesting a retry might be appropriate.
    """
    pass
