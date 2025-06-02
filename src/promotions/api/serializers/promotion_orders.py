from rest_framework import serializers

from promotions import models


class PromotionOrderReadListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PromotionOrder
        fields = "__all__"


class PromotionOrderReadOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PromotionOrder
        fields = "__all__"


class PromotionOrderBaseWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return PromotionOrderReadOneSerializer(instance).data


class PromotionOrderCreateSerializer(PromotionOrderBaseWriteSerializer):
    price_value = serializers.IntegerField(min_value=1, required=False)
    percent_value = serializers.IntegerField(min_value=1, max_value=100, required=False)

    class Meta:
        model = models.PromotionOrder
        exclude = ["modified_by", "created_by"]
        extra_kwargs = {
            "requirement_maximum_value_discount": {"required": True},
            "requirement_min_total_order_apply": {"required": True},
        }


class PromotionOrderUpdateSerializer(PromotionOrderBaseWriteSerializer):
    price_value = serializers.IntegerField(min_value=1, required=False)
    percent_value = serializers.IntegerField(min_value=1, max_value=100, required=False)

    class Meta:
        model = models.PromotionOrder
        exclude = ["modified_by", "created_by"]
