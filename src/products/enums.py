from utils.enums import EnumBase


class ProductType(EnumBase):
    VARIANT = "VR"
    MATERIAL = "MT"


class ProductSupplierStatus(EnumBase):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ProductVariantStatus(EnumBase):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ProductMaterialStatus(EnumBase):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ProductVariantType(EnumBase):
    SIMPLE = "simple"
    BUNDLE = "bundle"
    COMBO = "combo"


class ProductVariantMappingSource(EnumBase):
    LAZADA = "lazada"
    TIKTOK = "tiktok"
    SHOPEE = "shopee"


class ConfirmationLogType(EnumBase):
    Import = "IP"
    Export = "EP"
