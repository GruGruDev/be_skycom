from enum import Enum


class EnumBase(str, Enum):
    @classmethod
    def choices(cls):
        return tuple((i.value, i.name) for i in cls)

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class SequenceType(EnumBase):
    IMPORT = "IP"
    EXPORT = "EP"
    TRANSFER = "TF"
    CHECK = "CK"
    ORDER = "OD"
    TURN = "TURN"
