from enum import Enum


class OutBoxEntryStatus(str, Enum):
    PLACED = "placed"
    FAILED = "failed"
