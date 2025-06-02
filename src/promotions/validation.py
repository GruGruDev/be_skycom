from rest_framework.exceptions import ValidationError

from promotions.enums import PromotionStatus


def promotion_status_validate(instance):
    old_instance = instance.__class__.objects.filter(pk=instance.pk).first()
    if old_instance:
        # For update
        new_instance = instance

        if old_instance.status == PromotionStatus.IN_PROGRESS and new_instance.status == PromotionStatus.PENDING:
            raise ValidationError({"status": "Khuyến mãi trạng thái 'đang' không thể quay lại trạng thái 'chờ'."})

        if old_instance.status == PromotionStatus.CANCEL:
            raise ValidationError({"status": "Trạng thái khuyến mãi hiện tại là 'Cancel' nên không thể update được nữa."})


def base_promotion_type_validate(instance, enum_promotion_type):
    if (instance.price_value and instance.type != enum_promotion_type.PRICE) or (
        instance.type == enum_promotion_type.PRICE and not instance.price_value
    ):
        raise ValidationError({"type, price_value": "'type' và 'price_value' phải tương ứng nhau."})

    if (instance.percent_value and instance.type != enum_promotion_type.PERCENT) or (
        instance.type == enum_promotion_type.PERCENT and not instance.percent_value
    ):
        raise ValidationError({"type, percent_value": "'type'và 'percent_value' phải tương ứng nhau."})
