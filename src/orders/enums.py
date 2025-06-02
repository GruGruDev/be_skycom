from utils.enums import EnumBase


class OrderStatus(EnumBase):
    COMPLETED = "completed"
    CANCEL = "cancel"
    DRAFT = "draft"


class OrderPaymentType(EnumBase):
    COD = "COD"
    DIRECT_TRANSFER = "DIRECT_TRANSFER"
    CASH = "CASH"


class OrderItemDataFlowType(EnumBase):
    SIMPLE = "SIMPLE"
    COMBO = "COMBO"
    PROMOTION = "PROMOTION"


class WarehouseSheetType(EnumBase):
    """`Import`: Nhập kho
    `Export`: Xuất kho
    `Transfer`: Chuyển kho
    `Inventory`: Kiểm kho
    """

    Import = "IP"
    Export = "EP"
    Transfer = "TF"
    Inventory = "IV"


class TransportationCareStatus(EnumBase):
    NEW = "new"
    PENDING = "pending"
    PROCESSING = "processing"
    HANDLED = "handled"
    COMPLETED = "completed"


class TransportationCareCreationReason(EnumBase):
    LATE = "late"  # Giao muộn
    WAIT_RETURN = "wait_return"  # Chờ giao lại
    RETURNING = "returning"  # Đang hoàn hàng
    RETURNED = "returned"  # Đã hoàn thành công
