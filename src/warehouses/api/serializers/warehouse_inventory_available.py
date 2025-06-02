from rest_framework import serializers

from products.api.serializers import ProductVariantsSerializer
from warehouses import models


class WarehouseInventoryAvailableReadListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WarehouseInventoryAvailable
        fields = "__all__"


class WarehouseInventoryAvailableReadOneSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantsSerializer()

    class Meta:
        model = models.WarehouseInventoryAvailable
        fields = "__all__"


class WarehouseInventoryAvailableHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WarehouseInventoryAvailable.history.model
        exclude = ("history_id", "history_change_reason", "history_type")
