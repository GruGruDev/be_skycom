from bulk_update_or_create import BulkUpdateOrCreateQuerySet
from django.db import models
from model_utils.models import TimeStampedModel
from model_utils.models import UUIDModel

from locations.enums import DistrictType
from locations.enums import ProvinceType
from locations.enums import WardType
from utils.enums import EnumBase


# Create your models here.
class LocationBase(models.Model):
    name = models.CharField(max_length=64, blank=True)
    slug = models.CharField(max_length=64)
    label = models.CharField(max_length=256, blank=True)
    code = models.CharField(primary_key=True, max_length=36, unique=True, db_index=True)
    ghn_province_id = models.IntegerField(null=True)
    bd_province_id = models.CharField(max_length=256, null=True, blank=False)
    vtpost_province_id = models.CharField(max_length=256, null=True, blank=False)

    class Meta:
        abstract = True

    def __str__(self):
        return self.label


class Provinces(LocationBase):
    objects = BulkUpdateOrCreateQuerySet.as_manager()
    type = models.CharField(choices=ProvinceType.choices(), max_length=64, default=ProvinceType.PROVINCE.value)

    def __str__(self):
        return self.label

    class Meta:
        db_table = "tbl_Provinces"
        ordering = ["name"]


class Districts(LocationBase):
    objects = BulkUpdateOrCreateQuerySet.as_manager()
    type = models.CharField(choices=DistrictType.choices(), max_length=64, default=ProvinceType.PROVINCE.value)
    province = models.ForeignKey(Provinces, on_delete=models.CASCADE, related_name="province_districts", null=True)
    ghn_district_id = models.IntegerField(null=True)
    bd_district_id = models.CharField(max_length=256, null=True, blank=False)
    vtpost_district_id = models.CharField(max_length=256, null=True, blank=False)

    def __str__(self):
        return self.label

    class Meta:
        db_table = "tbl_Districts"
        ordering = ["name"]


class Wards(LocationBase):
    objects = BulkUpdateOrCreateQuerySet.as_manager()
    type = models.CharField(choices=WardType.choices(), max_length=64, default=ProvinceType.PROVINCE.value)
    district = models.ForeignKey(Districts, on_delete=models.CASCADE, related_name="district_wards", null=True)
    province = models.ForeignKey(Provinces, on_delete=models.CASCADE, related_name="province_wards", null=True)
    ghn_district_id = models.IntegerField(null=True)
    ghn_ward_id = models.CharField(max_length=16, null=True)
    bd_district_id = models.CharField(max_length=256, null=True, blank=False)
    bd_ward_id = models.CharField(max_length=256, null=True, blank=False)
    vtpost_district_id = models.CharField(max_length=256, null=True, blank=False)
    vtpost_ward_id = models.CharField(max_length=256, null=True, blank=False)

    class Meta:
        db_table = "tbl_Wards"
        ordering = ["name"]


class AddressType(EnumBase):
    CUSTOMER = "CT"
    WAREHOUSE = "WH"
    OTHER = "OT"


class Address(UUIDModel, TimeStampedModel):
    customer = models.ForeignKey(to="customers.Customer", on_delete=models.SET_NULL, related_name="addresses", null=True)
    warehouse = models.ForeignKey(to="warehouses.Warehouse", on_delete=models.SET_NULL, related_name="addresses", null=True)
    type = models.CharField(choices=AddressType.choices(), max_length=2, default=AddressType.OTHER)
    note = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=1024, blank=False, null=False)
    ward = models.ForeignKey(Wards, on_delete=models.DO_NOTHING, related_name="addresses")
    is_default = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_default is True:
            # set is_default other customer addresses to False
            if self.type == AddressType.CUSTOMER:
                Address.objects.filter(customer=self.customer, is_default=True).exclude(id=self.id).update(is_default=False)
            elif self.type == AddressType.WAREHOUSE:
                Address.objects.filter(warehouse=self.warehouse, is_default=True).exclude(id=self.id).update(is_default=False)
        return super().save(*args, **kwargs)

    def delete(self, using=None):
        self.customer = None
        self.warehouse = None
        self.save(using=using)

    class Meta:
        db_table = "tbl_Addresses"
        ordering = ["-created"]
