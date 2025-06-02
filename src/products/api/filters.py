import django_filters.rest_framework as django_filters
from django.db import models
from django_filters.conf import settings
from django_filters.filterset import remote_queryset

from products.enums import ProductMaterialStatus
from products.enums import ProductVariantStatus
from products.enums import ProductVariantType
from products.models import ProductCategory
from products.models import Products
from products.models import ProductsMaterials
from products.models import ProductsVariants
from products.models import ProductsVariantsBatches
from products.models import ProductsVariantsMaterials


class ProductFilterset(django_filters.FilterSet):

    total_inventory_min = django_filters.NumberFilter(field_name="total_inventory", lookup_expr="gte")

    total_inventory_max = django_filters.NumberFilter(field_name="total_inventory", lookup_expr="lte")

    total_variants_min = django_filters.NumberFilter(field_name="total_variants", lookup_expr="gte")

    total_variants_max = django_filters.NumberFilter(field_name="total_variants", lookup_expr="lte")

    class Meta:
        model = Products
        fields = [
            "created_by",
            "modified_by",
            "category",
            "supplier",
            "is_active",
            "total_inventory_min",
            "total_inventory_max",
            "total_variants_min",
            "total_variants_max",
        ]
        filter_overrides = {
            models.ForeignKey: {
                "filter_class": django_filters.filters.ModelMultipleChoiceFilter,
                "extra": lambda f: {
                    "queryset": remote_queryset(f),
                    "to_field_name": f.remote_field.field_name,
                    "null_label": settings.NULL_CHOICE_LABEL if f.null else None,
                },
            },
        }


class ProductVariantFilterset(django_filters.FilterSet):
    created_by = django_filters.UUIDFilter(field_name="created_by__id")
    modified_by = django_filters.UUIDFilter(field_name="modified_by__id")
    product = django_filters.UUIDFilter(field_name="product__id")
    category = django_filters.ModelMultipleChoiceFilter(
        field_name='product__category_id',
        queryset=ProductCategory.objects.all(),
        to_field_name='id'
    )
    status = django_filters.ChoiceFilter(choices=ProductVariantStatus.choices())
    type = django_filters.ChoiceFilter(choices=ProductVariantType.choices())
    exist_in_warehouse = django_filters.UUIDFilter(
        field_name="batches__warehouse_inventory_product_variant_batch__warehouse__id", label="Lọc sản phẩm có tồn trong kho"
    )

    total_inventory_min = django_filters.NumberFilter(field_name="total_inventory", lookup_expr="gte")

    total_inventory_max = django_filters.NumberFilter(field_name="total_inventory", lookup_expr="lte")

    # total_weight_min = django_filters.NumberFilter(field_name="total_weight", lookup_expr="gte")
    #
    # total_weight_max = django_filters.NumberFilter(field_name="total_weight", lookup_expr="lte")

    class Meta:
        model = ProductsVariants
        fields = (
            "created_by",
            "modified_by",
            "product",
            "category",
            "status",
            "type",
            "is_active",
            "total_inventory_min",
            "total_inventory_max",
            # "total_weight_min",
            # "total_weight_max",
        )


class ProductMaterialFilterset(django_filters.FilterSet):
    created_by = django_filters.UUIDFilter(field_name="created_by__id")
    modified_by = django_filters.UUIDFilter(field_name="modified_by__id")
    variant = django_filters.UUIDFilter(field_name="variants__product_variant__id")
    status = django_filters.ChoiceFilter(choices=ProductMaterialStatus.choices())
    exist_in_warehouse = django_filters.UUIDFilter(
        field_name="batches__warehouse_inventory_product_variant_batch__warehouse__id", label="Lọc sản phẩm có tồn trong kho"
    )

    class Meta:
        model = ProductsMaterials
        fields = ("created_by", "modified_by", "variant", "status", "is_active")

    # def filter_variant_id(self, queryset, name, value):
    #     return queryset.filter(variants__id=value)


class ProductVariantMaterialFilterset(django_filters.FilterSet):
    product_variant = django_filters.UUIDFilter(field_name="product_variant__id")
    product_material = django_filters.UUIDFilter(field_name="product_material__id")

    class Meta:
        model = ProductsVariantsMaterials
        fields = (
            "product_variant",
            "product_material",
        )


class ProductVariantBatchFilterset(django_filters.FilterSet):
    product_variant = django_filters.UUIDFilter(field_name="product_variant__id")
    product_material = django_filters.UUIDFilter(field_name="product_material__id")

    class Meta:
        model = ProductsVariantsBatches
        fields = (
            "product_variant",
            "product_material",
        )


class ProductReportsFilterset(django_filters.FilterSet):

    created_from = django_filters.DateFilter(field_name="created__date", lookup_expr="gte")
    created_to = django_filters.DateFilter(field_name="created__date", lookup_expr="lte")
    # products = django_filters.ModelMultipleChoiceFilter(
    #     field_name="line_items__variant__SKU_code", queryset=ProductsVariants.objects.all(), label="product"
    # )

    class Meta:
        model = ProductsVariants
        fields = "created_from", "created_to"


class ProductCategoryFilterset(django_filters.FilterSet):

    total_inventory_min = django_filters.NumberFilter(field_name="total_inventory", lookup_expr="gte")
    total_inventory_max = django_filters.NumberFilter(field_name="total_inventory", lookup_expr="lte")

    class Meta:
        model = ProductCategory
        fields = ["total_inventory_min", "total_inventory_max"]


class ProductVariantRevenueFilterset(django_filters.FilterSet):
    inventory_quantity_from = django_filters.NumberFilter(field_name="inventory_quantity", lookup_expr="gte")
    inventory_quantity_to = django_filters.NumberFilter(field_name="inventory_quantity", lookup_expr="lte")

    sold_quantity_from = django_filters.NumberFilter(field_name="sold_quantity", lookup_expr="gte")
    sold_quantity_to = django_filters.NumberFilter(field_name="sold_quantity", lookup_expr="lte")

    revenue_from = django_filters.NumberFilter(field_name="revenue", lookup_expr="gte")
    revenue_to = django_filters.NumberFilter(field_name="revenue", lookup_expr="lte")
    
    class Meta:
        model = ProductsVariants
        fields = ("inventory_quantity_from", "inventory_quantity_to", "sold_quantity_from", "sold_quantity_to", "revenue_from", "revenue_to")
