from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel
from model_utils.models import UUIDModel

from orders.enums import OrderStatus
from products.enums import ProductMaterialStatus
from products.enums import ProductSupplierStatus
from products.enums import ProductType
from products.enums import ProductVariantMappingSource
from products.enums import ProductVariantStatus
from products.enums import ProductVariantType
from users.models import User


class ProductCategory(TimeStampedModel, UUIDModel):
    name = models.CharField(blank=True, max_length=64)
    code = models.CharField(null=True, max_length=32, unique=True)

    def __str__(self):
        return self.code

    class Meta:
        db_table = "tbl_Products_Category"
        ordering = ["name"]


class ProductTag(TimeStampedModel, UUIDModel):
    tag = models.CharField(max_length=64, blank=True, unique=True)

    def __str__(self):
        return self.tag

    class Meta:
        db_table = "tbl_Products_Tag"
        ordering = ["tag"]


class ProductSupplier(TimeStampedModel, UUIDModel):
    name = models.CharField(blank=True, max_length=256, unique=True)
    business_code = models.CharField(blank=True, max_length=256, null=True)
    tax_number = models.CharField(blank=True, max_length=256, null=True)
    country = models.CharField(blank=True, max_length=256, null=True)
    address = models.CharField(blank=True, max_length=256, null=True)
    status = models.CharField(choices=ProductSupplierStatus.choices(), max_length=20, default=ProductSupplierStatus.ACTIVE.value)
    legal_representative = models.CharField(blank=True, max_length=256, null=True)
    established_at = models.DateField(blank=True, null=True, max_length=256)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "tbl_Products_Supplier"
        ordering = ["name"]


class Products(TimeStampedModel, UUIDModel):
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="product_create", null=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="product_modify", null=True)
    name = models.CharField(max_length=255, blank=False)
    note = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name="products")
    supplier = models.ForeignKey(ProductSupplier, on_delete=models.SET_NULL, related_name="products", null=True)
    SKU_code = models.CharField(max_length=255, null=True, unique=True)

    class Meta:
        db_table = "tbl_Products"
        ordering = ["-created"]


class ProductsVariants(TimeStampedModel, UUIDModel):
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="product_variants_create",
        blank=True,
        null=True,
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="product_variants_update",
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=255, blank=False)
    note = models.TextField(blank=True, null=True)
    SKU_code = models.CharField(max_length=255, blank=False, unique=True)
    bar_code = models.CharField(max_length=255, blank=True, null=True)

    purchare_price = models.PositiveIntegerField(null=True)
    neo_price = models.BigIntegerField(null=True)
    sale_price = models.BigIntegerField(null=True)
    sales_bonus = models.PositiveIntegerField(null=True)
    status = models.CharField(
        choices=ProductVariantStatus.choices(),
        max_length=8,
        default=ProductVariantStatus.ACTIVE.value,
    )
    is_active = models.BooleanField(default=True)
    type = models.CharField(
        choices=ProductVariantType.choices(),
        max_length=6,
        default=ProductVariantType.SIMPLE.value,
    )
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name="variants")
    tags = models.ManyToManyField(ProductTag, related_name="product_variant_tags", blank=True)
    commission = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):

        if not self.images.exists() and self.product.images.exists():
            product_images = self.product.images.all()
            self.images.set(product_images)

        if not self.bar_code:
            self.bar_code = self.product.SKU_code
        return super().save(*args, **kwargs)

    def inventory_available_confirmed(self):
        if self.type == ProductVariantType.SIMPLE:
            c_quantity_order_items = (
                self.orders_items.filter(order__status=OrderStatus.COMPLETED, order__shipping__isnull=True)
                .aggregate(models.Sum("quantity"))
                .get("quantity__sum")
                or 0
            )
            c_quantity_items_combo = (
                self.order_item_combos.filter(
                    line_item__order__status=OrderStatus.COMPLETED,
                    line_item__order__shipping__isnull=True,
                )
                .aggregate(models.Sum("quantity"))
                .get("quantity__sum")
                or 0
            )
            c_quantity_items_promotion = (
                self.line_items_promotions.filter(
                    order_variant_promotion__line_item__order__status=OrderStatus.COMPLETED,
                    order_variant_promotion__line_item__order__shipping__isnull=True,
                )
                .aggregate(models.Sum("quantity"))
                .get("quantity__sum")
                or 0
            )
            return c_quantity_order_items + c_quantity_items_combo + c_quantity_items_promotion
        return 0

    def inventory_available_non_confirm(self):
        if self.type == ProductVariantType.SIMPLE:
            c_quantity_order_items = (
                self.orders_items.filter(order__status=OrderStatus.DRAFT).aggregate(models.Sum("quantity")).get("quantity__sum") or 0
            )
            c_quantity_items_combo = (
                self.order_item_combos.filter(line_item__order__status=OrderStatus.DRAFT)
                .aggregate(models.Sum("quantity"))
                .get("quantity__sum")
                or 0
            )
            c_quantity_items_promotion = (
                self.line_items_promotions.filter(order_variant_promotion__line_item__order__status=OrderStatus.DRAFT)
                .aggregate(models.Sum("quantity"))
                .get("quantity__sum")
                or 0
            )
            return c_quantity_order_items + c_quantity_items_combo + c_quantity_items_promotion
        return 0

    class Meta:
        db_table = "tbl_Products_Variants"
        ordering = ["-created"]


class ProductsMaterials(TimeStampedModel, UUIDModel):
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="product_materials_create", blank=True, null=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="product_materials_update", blank=True, null=True)
    name = models.CharField(max_length=255, blank=False)
    note = models.TextField(blank=True, null=True)
    SKU_code = models.CharField(max_length=255, blank=False, unique=True)
    bar_code = models.CharField(max_length=255, blank=True, null=True, unique=True)
    weight = models.DecimalField(max_digits=15, decimal_places=4, default=0.0)
    length = models.DecimalField(max_digits=15, decimal_places=4, default=0.0)
    height = models.DecimalField(max_digits=15, decimal_places=4, default=0.0)
    width = models.DecimalField(max_digits=15, decimal_places=4, default=0.0)
    neo_price = models.BigIntegerField(null=True)
    sale_price = models.BigIntegerField(null=True)
    status = models.CharField(choices=ProductMaterialStatus.choices(), max_length=8, default=ProductMaterialStatus.ACTIVE.value)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "tbl_Products_Materials"
        ordering = ["-created"]


class ProductsVariantsMaterials(TimeStampedModel, UUIDModel):
    product_variant = models.ForeignKey(ProductsVariants, on_delete=models.CASCADE, related_name="materials")
    product_material = models.ForeignKey(ProductsMaterials, on_delete=models.CASCADE, related_name="variants")
    quantity = models.PositiveIntegerField(blank=True, null=True)
    weight = models.DecimalField(max_digits=15, decimal_places=4, default=0.0)

    class Meta:
        db_table = "tbl_Products_Variants_Materials"
        ordering = ["-created"]


class ProductsVariantsBatches(TimeStampedModel, UUIDModel):
    name = models.CharField(max_length=255, blank=False, null=False)
    type = models.CharField(choices=ProductType.choices(), max_length=2, default=ProductType.VARIANT.value)
    product_variant = models.ForeignKey(ProductsVariants, on_delete=models.CASCADE, related_name="batches", null=True)
    product_material = models.ForeignKey(ProductsMaterials, on_delete=models.CASCADE, related_name="batches", null=True)
    expire_date = models.DateField(blank=True, null=True)
    is_default = models.BooleanField(default=False) # Unique every obj

    def clean(self):
        if self.type == ProductType.VARIANT.value and self.product_variant is None:
            raise ValidationError({"product_variant": "Product variant must not be null when type is VARIANT"})
        if self.type == ProductType.MATERIAL.value and self.product_material is None:
            raise ValidationError({"product_material": "Product material must not be null when type is MATERIAL"})

    class Meta:
        db_table = "tbl_Products_Variants_Batches"
        unique_together = ["product_variant", "name"]
        ordering = ["-created"]


class ProductsVariantsMapping(TimeStampedModel, UUIDModel):
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="product_mapping_create", blank=True, null=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="product_mapping_update", blank=True, null=True)
    source = models.CharField(choices=ProductVariantMappingSource.choices(), max_length=6)
    third_product_id = models.CharField(max_length=50, blank=False, null=False)
    product_variant = models.ForeignKey(ProductsVariants, on_delete=models.SET_NULL, related_name="mappings", null=True)
    third_purchare_price = models.PositiveIntegerField(blank=True, null=True)
    third_neo_price = models.PositiveIntegerField(blank=True, null=True)
    third_sale_price = models.PositiveIntegerField(blank=True, null=True)
    third_image = models.URLField(blank=True, null=True)

    class Meta:
        db_table = "tbl_Products_Variants_Mapping"
        unique_together = ["third_product_id", "product_variant"]
        ordering = ["-created"]


class ProductsVariantsComboDetail(TimeStampedModel, UUIDModel):
    origin_variant = models.ForeignKey(ProductsVariants, on_delete=models.CASCADE, related_name="combo_variants")
    detail_variant = models.ForeignKey(ProductsVariants, on_delete=models.CASCADE, related_name="combos")
    price_detail_variant = models.PositiveIntegerField(blank=True, null=True)
    quantity = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        db_table = "tbl_Products_Variants_Combo_Detail"
        ordering = ["-created"]
