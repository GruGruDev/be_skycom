from utils.enums import EnumBase


class ProvinceType(EnumBase):
    CITY = "thanh-pho"
    PROVINCE = "tinh"


class DistrictType(EnumBase):
    DISTRICT = "quan"
    COUNTY = "huyen"
    TOWN = "thi-xa"
    CITY = "thanh-pho"


class WardType(EnumBase):
    WARD = "phuong"
    COMMUNE = "xa"
    TOWN = "thi-tran"
