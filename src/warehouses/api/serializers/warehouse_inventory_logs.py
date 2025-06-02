from rest_framework import serializers

from products.api.serializers import ProductVariantBatchSerializer
from warehouses import models
from warehouses.api.serializers.warehouse import WarehouseReadOneSerializer
from warehouses.api.serializers.warehouse_inventory_reason import WarehouseInventoryReasonReadOneSerializer
from warehouses.enums import WarehouseBaseType


class WarehouseInventoryLogReadListSerializer(serializers.ModelSerializer):
    product_variant_batch = ProductVariantBatchSerializer(read_only=True)
    sheet = serializers.SerializerMethodField("get_sheet")

    class Meta:
        model = models.WarehouseInventoryLog
        fields = "__all__"

    # TODO: Cân nhắc thêm foreign key cho sheet
    def get_sheet(self, obj):
        if obj.type in [WarehouseBaseType.IMPORT, WarehouseBaseType.EXPORT]:
            return obj.import_export_sheet
        elif obj.type == WarehouseBaseType.TRANSFER:
            return obj.transfer_sheet
        elif obj.type == WarehouseBaseType.CHECK:
            return obj.check_sheet
        return None


class WarehouseInventoryLogReadOneSerializer(serializers.ModelSerializer):
    warehouse = WarehouseReadOneSerializer()
    product_variant_batch = ProductVariantBatchSerializer()
    change_reason = WarehouseInventoryReasonReadOneSerializer()

    class Meta:
        model = models.WarehouseInventoryLog
        fields = "__all__"
