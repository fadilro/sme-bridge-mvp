from enum import Enum

class UtilityBillStatus(str, Enum):
    pending = "pending"
    success = "success"
    flagged_low_confidence = "flagged_low_confidence"
    flagged_unreadable = "flagged_unreadable"
    resolved_by_client = "resolved_by_client"
