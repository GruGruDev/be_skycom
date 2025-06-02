from rest_framework import serializers

from products.api.serializers import ProductVariantBatchSerializer
from warehouses import models
from warehouses.api.serializers.warehouse import WarehouseReadOneSerializer
from warehouses.api.serializers.warehouse_inventory_reason import WarehouseInventoryReasonReadOneSerializer


class WarehouseSheetCheckDetailSerializer(serializers.ModelSerializer):
    quantity_actual = serializers.DecimalField(min_value=0, max_digits=15, decimal_places=4)

    class Meta:
        model = models.WarehouseSheetCheckDetail
        fields = ["id", "quantity_actual", "product_variant_batch"]
        extra_kwargs = {"product_variant_batch": {"required": True}}


class WarehouseSheetCheckDetailReadSerializer(serializers.ModelSerializer):
    product_variant_batch = ProductVariantBatchSerializer()
    quantity_system = serializers.DecimalField(
        max_digits=15, decimal_places=4, required=False, help_text="Số lượng tồn kho của hệ thống tại thời điểm tạo phiếu kiểm"
    )
    quantity_actual = serializers.DecimalField(
        max_digits=15, decimal_places=4, required=False, help_text="Số lượng tồn kho thực người dùng nhập vào"
    )

    class Meta:
        model = models.WarehouseSheetCheckDetail
        fields = ["id", "product_variant_batch", "quantity_system", "quantity_actual"]


class WarehouseSheetCheckReadListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WarehouseSheetCheck
        fields = "__all__"


class WarehouseSheetCheckReadOneSerializer(serializers.ModelSerializer):
    warehouse = WarehouseReadOneSerializer()
    change_reason = WarehouseInventoryReasonReadOneSerializer()
    sheet_detail = WarehouseSheetCheckDetailReadSerializer(source="warehouse_sheet_check_detail_sheet", many=True)

    class Meta:
        model = models.WarehouseSheetCheck
        fields = "__all__"


class WarehouseSheetCheckBaseWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return WarehouseSheetCheckReadOneSerializer(instance).data


class WarehouseSheetCheckCreateSerializer(WarehouseSheetCheckBaseWriteSerializer):
    sheet_detail = WarehouseSheetCheckDetailSerializer(many=True)
    is_confirm = serializers.BooleanField(default=False)

    class Meta:
        model = models.WarehouseSheetCheck
        exclude = ["modified_by", "created_by", "code", "type", "confirm_date", "confirm_by"]
        extra_kwargs = {"warehouse": {"required": True}}


class WarehouseSheetCheckUpdateSerializer(WarehouseSheetCheckBaseWriteSerializer):
    class Meta:
        model = models.WarehouseSheetCheck
        fields = ["note", "is_delete", "is_confirm"]
