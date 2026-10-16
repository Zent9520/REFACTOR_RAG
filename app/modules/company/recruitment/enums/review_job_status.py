from enum import Enum

class ReviewJobStatus:
    QUEUED = "QUEUED"

    PROCESSING = "PROCESSING"

    COMPLETED = "COMPLETED"

    FAILED = "FAILED"

    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"