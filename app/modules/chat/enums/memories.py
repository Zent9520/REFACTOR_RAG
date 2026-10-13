from enum import Enum


class MemoryType(str, Enum):
    PROFILE = "PROFILE"
    PROJECT = "PROJECT"
    RESPONSIBILITY = "RESPONSIBILITY"
    PREFERENCE = "PREFERENCE"