from rest_framework import serializers

from products.api.serializers import ProductVariantBatchSerializer
from warehouses import models
from warehouses.api.serializers.warehouse import WarehouseReadOneSerializer
from warehouses.api.serializers.warehouse_inventory_reason import WarehouseInventoryReasonReadOneSerializer


class WarehouseSheetTransferDetailSerializer(serializers.ModelSerializer):
    quantity = serializers.DecimalField(min_value=1, max_digits=15, decimal_places=4)

    class Meta:
        model = models.WarehouseSheetTransferDetail
        fields = ["id", "quantity", "product_variant_batch"]
        extra_kwargs = {"product_variant_batch": {"required": True}}


class WarehouseSheetTransferDetailReadSerializer(serializers.ModelSerializer):
    product_variant_batch = ProductVariantBatchSerializer()

    class Meta:
        model = models.WarehouseSheetImportExportDetail
        fields = ["id", "product_variant_batch", "quantity"]


class WarehouseSheetTransferReadListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WarehouseSheetTransfer
        fields = "__all__"


class WarehouseSheetTransferReadOneSerializer(serializers.ModelSerializer):
    warehouse_from = WarehouseReadOneSerializer()
    warehouse_to = WarehouseReadOneSerializer()
    change_reason = WarehouseInventoryReasonReadOneSerializer()
    sheet_detail = WarehouseSheetTransferDetailReadSerializer(source="warehouse_sheet_transfer_detail_sheet", many=True)

    class Meta:
        model = models.WarehouseSheetTransfer
        fields = "__all__"


class WarehouseSheetTransferBaseWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return WarehouseSheetTransferReadOneSerializer(instance).data


class WarehouseSheetTransferCreateSerializer(WarehouseSheetTransferBaseWriteSerializer):
    sheet_detail = WarehouseSheetTransferDetailSerializer(many=True)

    class Meta:
        model = models.WarehouseSheetTransfer
        exclude = ["modified_by", "created_by", "code", "type", "confirm_date", "confirm_by"]
        extra_kwargs = {
            "warehouse_from": {"required": True},
            "warehouse_to": {"required": True},
        }


class WarehouseSheetTransferUpdateSerializer(WarehouseSheetTransferBaseWriteSerializer):
    class Meta:
        model = models.WarehouseSheetTransfer
        fields = ["note", "is_delete", "is_confirm"]
