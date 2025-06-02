from rest_framework import serializers

from promotions import models
from promotions.enums import PromotionVariantType


class PromotionVariantsOtherVariantWriteSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.IntegerField(min_value=0)
    requirement_max_quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = models.PromotionVariantsOtherVariant
        fields = ["quantity", "requirement_max_quantity", "price", "note", "variant"]
        extra_kwargs = {"variant": {"required": True}}


class PromotionVariantReadListSerializer(serializers.ModelSerializer):
    other_variants = PromotionVariantsOtherVariantWriteSerializer(source="promotion_variant_other_variant", many=True)

    class Meta:
        model = models.PromotionVariant
        fields = "__all__"


class PromotionVariantReadOnceSerializer(serializers.ModelSerializer):

    other_variants = PromotionVariantsOtherVariantWriteSerializer(source="promotion_variant_other_variant", many=True)

    class Meta:
        model = models.PromotionVariant
        fields = "__all__"


class PromotionVariantBaseWriteOnceSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return PromotionVariantReadOnceSerializer(instance).data


class PromotionVariantUpdateSerializer(PromotionVariantBaseWriteOnceSerializer):
    price_value = serializers.IntegerField(min_value=1, required=False)
    percent_value = serializers.IntegerField(min_value=1, max_value=100, required=False)

    class Meta:
        model = models.PromotionVariant
        exclude = ["modified_by", "created_by"]


class PromotionVariantCreateSerializer(PromotionVariantBaseWriteOnceSerializer):
    other_variants = serializers.ListSerializer(child=PromotionVariantsOtherVariantWriteSerializer(), required=False)
    price_value = serializers.IntegerField(min_value=1, required=False)
    percent_value = serializers.IntegerField(min_value=1, max_value=100, required=False)

    class Meta:
        model = models.PromotionVariant
        exclude = ["modified_by", "created_by"]
        extra_kwargs = {"variant": {"required": True}}

    def validate(self, data):
        promotion_type = data["type"]
        other_variants = data.get("other_variants")

        if (other_variants and promotion_type != PromotionVariantType.OTHER_VARIANT) or (
            promotion_type == PromotionVariantType.OTHER_VARIANT and not other_variants
        ):
            raise serializers.ValidationError({"type, other_variants": "'type' và 'other_variants' phải tương ứng nhau."})

        return data
