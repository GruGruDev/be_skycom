from utils.enums import EnumBase


class WarehouseBaseType(EnumBase):
    """
    `Import`: Nhập kho
    `Export`: Xuất kho
    `Transfer`: Chuyển kho
    `CHECK`: Kiểm kho
    """

    IMPORT = "IP"
    EXPORT = "EP"
    TRANSFER = "TF"
    CHECK = "CK"


class SheetImportExportType(EnumBase):
    """
    `Import`: Nhập kho
    `Export`: Xuất kho
    """

    IMPORT = "IP"
    EXPORT = "EP"


class SheetTransferType(EnumBase):
    """
    `Transfer`: Chuyển kho
    """

    TRANSFER = "TF"


class SheetCheckType(EnumBase):
    """
    `CHECK`: Chuyển kho
    """

    CHECK = "CK"
