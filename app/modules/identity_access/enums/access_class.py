from enum import Enum


class AccessClass(str, Enum):

    PUBLIC = "PUBLIC"

    STAFF = "STAFF"

    SPECIALIST = "SPECIALIST"

    MANAGEMENT = "MANAGEMENT"   

    EXECUTIVE = "EXECUTIVE"

    OWNER_ONLY = "OWNER_ONLY"