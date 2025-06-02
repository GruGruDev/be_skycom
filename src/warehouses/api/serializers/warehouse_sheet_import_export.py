from rest_framework import serializers

from orders.models import Orders
from products.api.serializers import ProductVariantBatchSerializer
from warehouses import models
from warehouses.api.serializers.warehouse import WarehouseReadOneSerializer
from warehouses.api.serializers.warehouse_inventory_reason import WarehouseInventoryReasonReadOneSerializer
from warehouses.enums import SheetImportExportType


class WarehouseSheetImportExportDetailSerializer(serializers.ModelSerializer):
    quantity = serializers.DecimalField(min_value=1, max_digits=15, decimal_places=4)

    class Meta:
        model = models.WarehouseSheetImportExportDetail
        fields = ["id", "product_variant_batch", "quantity"]
        extra_kwargs = {"product_variant_batch": {"required": True}}


class WarehouseSheetImportExportDetailReadSerializer(serializers.ModelSerializer):
    product_variant_batch = ProductVariantBatchSerializer()

    class Meta:
        model = models.WarehouseSheetImportExportDetail
        fields = ["id", "product_variant_batch", "quantity"]


class WarehouseSheetImportExportReadListSerializer(serializers.ModelSerializer):
    order_key = serializers.ReadOnlyField(source="order.order_key")

    class Meta:
        model = models.WarehouseSheetImportExport
        fields = "__all__"


class OrderReadDetailSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        fields = ["id", "order_key", "status"]


class WarehouseSheetImportExportReadOneSerializer(serializers.ModelSerializer):
    warehouse = WarehouseReadOneSerializer()
    change_reason = WarehouseInventoryReasonReadOneSerializer()
    sheet_detail = WarehouseSheetImportExportDetailReadSerializer(source="warehouse_sheet_import_export_detail_sheet", many=True)
    order_key = serializers.ReadOnlyField(source="order.order_key")
    order = OrderReadDetailSheetSerializer()

    class Meta:
        model = models.WarehouseSheetImportExport
        fields = "__all__"


class WarehouseSheetImportExportBaseWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return WarehouseSheetImportExportReadOneSerializer(instance).data


class WarehouseSheetImportExportCreateSerializer(WarehouseSheetImportExportBaseWriteSerializer):
    sheet_detail = WarehouseSheetImportExportDetailSerializer(many=True)
    order_key = serializers.CharField(max_length=255, allow_null=True, required=False)

    class Meta:
        model = models.WarehouseSheetImportExport
        exclude = ["modified_by", "created_by", "code", "confirm_date", "confirm_by"]
        extra_kwargs = {"warehouse": {"required": True}, "is_confirm": {"required": True}}

    def validate(self, data):
        sheet_type = data["type"]
        sheet_detail = data["sheet_detail"]

        for idx, element in enumerate(sheet_detail):
            quantity = element["quantity"]

            if sheet_type == SheetImportExportType.EXPORT:
                data["sheet_detail"][idx]["quantity"] = -quantity

        return data


class WarehouseSheetImportExportUpdateSerializer(WarehouseSheetImportExportBaseWriteSerializer):
    order_key = serializers.CharField(max_length=255, allow_null=True, required=False)

    class Meta:
        model = models.WarehouseSheetImportExport
        fields = ["note", "is_delete", "is_confirm", "change_reason", "order_key"]
