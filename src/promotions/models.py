import uuid

from django.db import models
from model_utils.models import TimeStampedModel
from rest_framework.exceptions import ValidationError

from products.enums import ProductVariantType
from products.models import ProductsVariants
from promotions.enums import PromotionOrderType
from promotions.enums import PromotionStatus
from promotions.enums import PromotionVariantType
from promotions.enums import PromotionVoucherType
from promotions.validation import base_promotion_type_validate
from promotions.validation import promotion_status_validate
from users.models import User


class PromotionOrder(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="promotion_order_modified")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="promotion_order_created")
    name = models.CharField(max_length=255, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=11, choices=PromotionStatus.choices(), default=PromotionStatus.PENDING)
    type = models.CharField(max_length=11, choices=PromotionOrderType.choices())
    price_value = models.IntegerField(blank=True, null=True)
    percent_value = models.IntegerField(blank=True, null=True)
    requirement_min_total_order_apply = models.IntegerField(blank=True, null=True)
    requirement_maximum_value_discount = models.IntegerField(blank=True, null=True)
    requirement_time_expire = models.DateTimeField(blank=True, null=True)
    is_soft_delete = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created"]
        db_table = "tbl_Promotions_Orders"

    def clean(self):
        promotion_status_validate(self)
        base_promotion_type_validate(self, PromotionOrderType)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class PromotionVoucher(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="promotion_voucher_modified")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="promotion_voucher_created")
    status = models.CharField(max_length=11, choices=PromotionStatus.choices(), default=PromotionStatus.PENDING)
    type = models.CharField(max_length=11, choices=PromotionVoucherType.choices())
    name = models.CharField(max_length=255, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    price_value = models.IntegerField(blank=True, null=True)
    percent_value = models.IntegerField(blank=True, null=True)
    requirement_min_total_order_apply = models.IntegerField(blank=True, null=True)
    requirement_maximum_value_discount = models.IntegerField(blank=True, null=True)
    requirement_number_used = models.IntegerField(blank=True, null=True, default=999999)
    requirement_time_expire = models.DateTimeField(blank=True, null=True)
    number_used = models.DateTimeField(blank=True, null=True)
    is_soft_delete = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created"]
        db_table = "tbl_Promotions_Vouchers"

    def clean(self, *args, **kwargs):
        promotion_status_validate(self)
        base_promotion_type_validate(self, PromotionVoucherType)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class PromotionVariant(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="promotion_variant_modified")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="promotion_variant_created")
    status = models.CharField(max_length=11, choices=PromotionStatus.choices(), default=PromotionStatus.PENDING)
    type = models.CharField(max_length=13, choices=PromotionVariantType.choices())
    variant = models.ForeignKey(
        ProductsVariants, on_delete=models.SET_NULL, blank=True, null=True, related_name="product_variant_promotion_variant"
    )
    name = models.CharField(max_length=255, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    price_value = models.IntegerField(blank=True, null=True)
    percent_value = models.IntegerField(blank=True, null=True)
    requirement_min_total_quantity_variant_apply = models.IntegerField(blank=True, null=True)
    requirement_max_total_quantity_variant = models.IntegerField(blank=True, null=True)
    requirement_maximum_value_discount = models.IntegerField(blank=True, null=True)
    requirement_time_expire = models.DateTimeField(blank=True, null=True)
    is_soft_delete = models.BooleanField(default=False)
    note = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created"]
        db_table = "tbl_Promotions_Variants"

    def clean(self, *args, **kwargs):
        promotion_status_validate(self)
        base_promotion_type_validate(self, PromotionVariantType)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class PromotionVariantsOtherVariant(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    modified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="promotion_variants_other_variant_modified"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="promotion_variants_other_variant_created"
    )
    promotion_variant = models.ForeignKey(
        PromotionVariant, on_delete=models.SET_NULL, blank=True, null=True, related_name="promotion_variant_other_variant"
    )
    variant = models.ForeignKey(
        ProductsVariants, on_delete=models.SET_NULL, blank=True, null=True, related_name="product_variant_promotion_other_variant"
    )
    quantity = models.IntegerField(blank=True, null=True)
    requirement_max_quantity = models.IntegerField(blank=True, null=True)
    price = models.IntegerField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created"]
        db_table = "tbl_Promotions_Variants_OtherVariant"

    def clean(self, *args, **kwargs):
        if self.promotion_variant.type != PromotionVariantType.OTHER_VARIANT:
            raise ValidationError({"type, other_variant": "'type'và 'other_variant' phải tương ứng nhau."})

        if self.variant.type != ProductVariantType.SIMPLE:
            raise ValidationError({"variant_type": "Phải là sản phẩm loại 'simple'."})

        return super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
