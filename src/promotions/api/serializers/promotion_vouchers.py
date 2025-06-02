from rest_framework import serializers

from promotions import models
from users.api.serializers import UserReadOneSerializer


class PromotionVoucherReadListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PromotionVoucher
        fields = "__all__"


class PromotionVoucherReadOnceSerializer(serializers.ModelSerializer):
    modified_by = UserReadOneSerializer()
    created_by = UserReadOneSerializer()

    class Meta:
        model = models.PromotionVoucher
        fields = "__all__"


class PromotionVoucherBaseWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return PromotionVoucherReadOnceSerializer(instance).data


class PromotionVoucherCreateSerializer(PromotionVoucherBaseWriteSerializer):
    price_value = serializers.IntegerField(min_value=1, required=False)
    percent_value = serializers.IntegerField(min_value=1, max_value=100, required=False)

    class Meta:
        model = models.PromotionVoucher
        exclude = ["modified_by", "created_by"]
        extra_kwargs = {
            "requirement_maximum_value_discount": {"required": True},
            "requirement_min_total_order_apply": {"required": True},
        }


class PromotionVoucherUpdateSerializer(PromotionVoucherBaseWriteSerializer):
    price_value = serializers.IntegerField(min_value=1, required=False)
    percent_value = serializers.IntegerField(min_value=1, max_value=100, required=False)

    class Meta:
        model = models.PromotionVoucher
        exclude = ["modified_by", "created_by"]
