from rest_framework import serializers

from locations.api.serializers import AddressSerializer
from warehouses import models


class WarehouseReadListSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = models.Warehouse
        fields = "__all__"


class WarehouseReadOneSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = models.Warehouse
        fields = "__all__"


class WarehouseBaseWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return WarehouseReadOneSerializer(instance).data


class WarehouseCreateSerializer(WarehouseBaseWriteSerializer):
    class Meta:
        model = models.Warehouse
        exclude = ["modified_by", "created_by"]


class WarehouseUpdateSerializer(WarehouseBaseWriteSerializer):
    class Meta:
        model = models.Warehouse
        exclude = ["modified_by", "created_by"]


class WarehouseSheetDataBulkUpdateSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    is_confirm = serializers.BooleanField()


class WarehouseSheetBulkUpdateSerializer(serializers.Serializer):
    sheets = serializers.ListSerializer(child=WarehouseSheetDataBulkUpdateSerializer(), max_length=100, min_length=1)
