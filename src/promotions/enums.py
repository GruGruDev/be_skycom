from enum import Enum


class PromotionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CANCEL = "cancel"

    @classmethod
    def choices(cls):
        return tuple((i.value, i.name) for i in cls)


class PromotionVoucherType(str, Enum):
    PRICE = "price"
    PERCENT = "percent"

    @classmethod
    def choices(cls):
        return tuple((i.value, i.name) for i in cls)


class PromotionOrderType(str, Enum):
    PRICE = "price"
    PERCENT = "percent"

    @classmethod
    def choices(cls):
        return tuple((i.value, i.name) for i in cls)


class PromotionVariantType(str, Enum):
    PRICE = "price"
    PERCENT = "percent"
    OTHER_VARIANT = "other_variant"

    @classmethod
    def choices(cls):
        return tuple((i.value, i.name) for i in cls)
