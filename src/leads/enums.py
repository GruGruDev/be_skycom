from enum import Enum


class LeadStatus(str, Enum):
    SPAM = 0
    NEW = 1
    WAITING = 2
    PROCESS = 3
    YES = 4
    NO = 5
    CONSIDER = 6
    BAD_DATA = 7

    @classmethod
    def choices(cls):
        return tuple((i.value, i.name) for i in cls)
