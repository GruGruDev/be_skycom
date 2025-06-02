import django_filters.rest_framework as django_filters
from django.db import models
from django_filters.conf import settings
from django_filters.filterset import remote_queryset

from products.models import ProductCategory
from products.models import ProductsMaterials
from products.models import ProductsVariants
from products.models import ProductsVariantsBatches
from warehouses.enums import SheetImportExportType
from warehouses.enums import WarehouseBaseType
from warehouses.models import Warehouse
from warehouses.models import WarehouseInventory
from warehouses.models import WarehouseInventoryAvailable
from warehouses.models import WarehouseInventoryLog
from warehouses.models import WarehouseInventoryReason
from warehouses.models import WarehouseSheetCheck
from warehouses.models import WarehouseSheetImportExport
from warehouses.models import WarehouseSheetTransfer


class WarehouseFilterset(django_filters.FilterSet):
    created_from = django_filters.DateFilter(field_name="created__date", lookup_expr="gte")
    created_to = django_filters.DateFilter(field_name="created__date", lookup_expr="lte")

    class Meta:
        model = Warehouse
        fields = ("created", "created_by", "modified_by", "is_default", "is_sales")
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


class WarehouseInventoryFilterSet(django_filters.FilterSet):
    warehouse_id = django_filters.ModelMultipleChoiceFilter(field_name="warehouse", queryset=Warehouse.objects.all())
    created_from = django_filters.DateFilter(field_name="created__date", lookup_expr="gte")
    created_to = django_filters.DateFilter(field_name="created__date", lookup_expr="lte")
    variant_id = django_filters.ModelMultipleChoiceFilter(field_name="product_variant_batch__product_variant", queryset=ProductsVariants.objects.all())
    material_id = django_filters.ModelMultipleChoiceFilter(field_name="product_variant_batch__product_material", queryset=ProductsMaterials.objects.all())

    class Meta:
        model = WarehouseInventory
        fields = ("warehouse_id", "created_from", "created_to", "product_variant_batch", "variant_id", "material_id")
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


class WarehouseInventoryVariantFilterSet(django_filters.FilterSet):
    sku_code = django_filters.CharFilter(field_name="SKU_code")
    batch = django_filters.ModelMultipleChoiceFilter(field_name="batches", queryset=ProductsVariantsBatches.objects.all())
    warehouse = django_filters.ModelMultipleChoiceFilter(
        field_name="batches__warehouse_inventory_product_variant_batch__warehouse", queryset=Warehouse.objects.all()
    )
    variant = django_filters.filters.ModelMultipleChoiceFilter(
        field_name="id",
        to_field_name="id",
        queryset=ProductsVariants.objects.all(),
    )

    class Meta:
        model = ProductsVariants
        fields = ("sku_code", "bar_code", "status", "batch", "warehouse", "variant")
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


class WarehouseInventoryAvailableFilterSet(django_filters.FilterSet):
    class Meta:
        model = WarehouseInventoryAvailable
        fields = ("product_variant",)


class WarehouseInventoryReasonFilterSet(django_filters.FilterSet):
    type = django_filters.MultipleChoiceFilter(choices=WarehouseBaseType.choices())

    class Meta:
        model = WarehouseInventoryReason
        fields = ("type",)


class WarehouseSheetImportExportFilterSet(django_filters.FilterSet):
    type = django_filters.MultipleChoiceFilter(choices=SheetImportExportType.choices())
    created_from = django_filters.DateFilter(field_name="created__date", lookup_expr="gte")
    created_to = django_filters.DateFilter(field_name="created__date", lookup_expr="lte")
    modified_from = django_filters.DateFilter(field_name="modified__date", lookup_expr="gte")
    modified_to = django_filters.DateFilter(field_name="modified__date", lookup_expr="lte")
    confirm_date_from = django_filters.DateFilter(field_name="confirm_date__date", lookup_expr="gte")
    confirm_date_to = django_filters.DateFilter(field_name="confirm_date__date", lookup_expr="lte")
    order_id = django_filters.UUIDFilter(field_name="order_id")

    class Meta:
        model = WarehouseSheetImportExport
        fields = (
            "created_from",
            "created_to",
            "modified_from",
            "modified_to",
            "confirm_date_from",
            "confirm_date_to",
            "is_delete",
            "is_confirm",
            "modified_by",
            "created_by",
            "confirm_by",
            "warehouse",
            "change_reason",
            "type",
        )
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


class WarehouseSheetCheckFilterSet(django_filters.FilterSet):
    created_from = django_filters.DateFilter(field_name="created__date", lookup_expr="gte")
    created_to = django_filters.DateFilter(field_name="created__date", lookup_expr="lte")
    modified_from = django_filters.DateFilter(field_name="modified__date", lookup_expr="gte")
    modified_to = django_filters.DateFilter(field_name="modified__date", lookup_expr="lte")
    confirm_date_from = django_filters.DateFilter(field_name="confirm_date__date", lookup_expr="gte")
    confirm_date_to = django_filters.DateFilter(field_name="confirm_date__date", lookup_expr="lte")

    class Meta:
        model = WarehouseSheetCheck
        fields = (
            "created_from",
            "created_to",
            "modified_from",
            "modified_to",
            "confirm_date_from",
            "confirm_date_to",
            "is_delete",
            "is_confirm",
            "modified_by",
            "created_by",
            "confirm_by",
            "warehouse",
            "change_reason",
        )
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


class WarehouseSheetTransferFilterSet(django_filters.FilterSet):
    created_from = django_filters.DateFilter(field_name="created__date", lookup_expr="gte")
    created_to = django_filters.DateFilter(field_name="created__date", lookup_expr="lte")
    modified_from = django_filters.DateFilter(field_name="modified__date", lookup_expr="gte")
    modified_to = django_filters.DateFilter(field_name="modified__date", lookup_expr="lte")
    confirm_date_from = django_filters.DateFilter(field_name="confirm_date__date", lookup_expr="gte")
    confirm_date_to = django_filters.DateFilter(field_name="confirm_date__date", lookup_expr="lte")

    class Meta:
        model = WarehouseSheetTransfer
        fields = (
            "created_from",
            "created_to",
            "modified_from",
            "modified_to",
            "confirm_date_from",
            "confirm_date_to",
            "is_delete",
            "is_confirm",
            "modified_by",
            "created_by",
            "confirm_by",
            "change_reason",
            "warehouse_from",
            "warehouse_to",
        )
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


class WarehouseInventoryLogFilterSet(django_filters.FilterSet):
    type = django_filters.MultipleChoiceFilter(choices=WarehouseBaseType.choices())
    created_from = django_filters.DateFilter(field_name="created__date", lookup_expr="gte")
    created_to = django_filters.DateFilter(field_name="created__date", lookup_expr="lte")
    variant = django_filters.ModelMultipleChoiceFilter(
        field_name="product_variant_batch__product_variant", queryset=ProductsVariants.objects.all()
    )
    category = django_filters.ModelMultipleChoiceFilter(
        field_name="product_variant_batch__product_variant__product__category", queryset=ProductCategory.objects.all()
    )

    class Meta:
        model = WarehouseInventoryLog
        fields = ("warehouse", "product_variant_batch", "created_from", "created_to", "type", "variant", "category")
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


class ProductWarehouseReportFilter(django_filters.FilterSet):
    date_from = django_filters.filters.DateFilter()
    date_to = django_filters.filters.DateFilter()
    warehouse_id = django_filters.CharFilter()

class ReportWarehouseCategoryFilterset(django_filters.FilterSet):
    date_from = django_filters.filters.DateFilter()
    date_to = django_filters.filters.DateFilter()
    warehouse_id = django_filters.CharFilter()
    category_id = django_filters.CharFilter()