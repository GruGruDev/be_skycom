from rest_framework import serializers

from products.api.serializers import ProductVariantBatchSerializer
from warehouses import models
from warehouses.api.serializers.warehouse import WarehouseReadOneSerializer


class WarehouseInventoryReadListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WarehouseInventory
        fields = "__all__"


class WarehouseInventoryReadDetailSerializer(serializers.ModelSerializer):
    warehouse = WarehouseReadOneSerializer()
    product_variant_batch = ProductVariantBatchSerializer()

    class Meta:
        model = models.WarehouseInventory
        fields = "__all__"


class WarehouseInventoryVariantBatchesSerializer(serializers.Serializer):
    batch_id = serializers.UUIDField()
    batch_name = serializers.CharField()
    batch_expire_date = serializers.CharField()
    warehouse_id = serializers.UUIDField(allow_null=True)
    warehouse_name = serializers.CharField(allow_null=True)
    inventory = serializers.DecimalField(max_digits=15, decimal_places=4)


class WarehouseInventoryVariantSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    sku_code = serializers.CharField()
    bar_code = serializers.CharField()
    status = serializers.CharField()
    sale_price = serializers.IntegerField(allow_null=True)
    neo_price = serializers.IntegerField(allow_null=True)
    total_inventory = serializers.DecimalField(max_digits=15, decimal_places=4)
    batches = serializers.ListSerializer(child=WarehouseInventoryVariantBatchesSerializer(), allow_empty=True)
