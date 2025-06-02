from rest_framework import serializers

from warehouses import models


class WarehouseInventoryReasonReadListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WarehouseInventoryReason
        fields = "__all__"


class WarehouseInventoryReasonReadOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WarehouseInventoryReason
        fields = "__all__"


class WarehouseInventoryReasonBaseWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return WarehouseInventoryReasonReadOneSerializer(instance).data


class WarehouseInventoryReasonCreateSerializer(WarehouseInventoryReasonBaseWriteSerializer):
    class Meta:
        model = models.WarehouseInventoryReason
        exclude = ["modified_by", "created_by"]


class WarehouseInventoryReasonUpdateSerializer(WarehouseInventoryReasonBaseWriteSerializer):
    class Meta:
        model = models.WarehouseInventoryReason
        exclude = ["modified_by", "created_by"]
