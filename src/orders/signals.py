from datetime import datetime

from django.db.models.signals import pre_save
from django.dispatch import receiver

from orders.enums import OrderStatus
from orders.models import Orders
from orders.models import OrdersItems
from orders.models import OrdersItemsCombo
from orders.models import OrdersItemsPromotion
from orders.models import OrderVariantsPromotion
from products.enums import ProductVariantType
from promotions.enums import PromotionVariantType
from warehouses.models import WarehouseInventoryAvailable


def calculate_warehouse_inventory(instance, created_by, confirm_exp=None, non_confirm_exp=None, order_key=None, is_export=False):
    def transform_quantity(quantity: int = 0, exp: str = None) -> (int):
        # exp: `+`, `-`, `None`
        # Code cũ
        # return int(exp + str(quantity)) if exp else 0
        try:
            return int(float(exp + str(quantity))) if exp else 0
        except ValueError as e:
            # Log error or handle it
            print(f"Error converting quantity: {e}")
            return 0

    if any([confirm_exp, non_confirm_exp]):
        line_items: list[OrdersItems] = instance.line_items.all()
        for line_item in line_items:
            if line_item.variant.type == ProductVariantType.SIMPLE:
                WarehouseInventoryAvailable.create_or_update(
                    user=created_by,
                    variant_id=line_item.variant.id,
                    quantity_confirm_up=transform_quantity(line_item.quantity, confirm_exp),
                    quantity_non_confirm_up=transform_quantity(line_item.quantity, non_confirm_exp),
                    code=order_key,
                    is_export=is_export,
                )
            else:
                items_combo: list[OrdersItemsCombo] = line_item.items_combo.all()
                for item in items_combo:
                    WarehouseInventoryAvailable.create_or_update(
                        user=created_by,
                        variant_id=item.variant.id,
                        quantity_confirm_up=transform_quantity(item.quantity * line_item.quantity, confirm_exp),
                        quantity_non_confirm_up=transform_quantity(item.quantity * line_item.quantity, non_confirm_exp),
                        code=order_key,
                        is_export=is_export,
                    )

            variant_promotions: list[OrderVariantsPromotion] = line_item.variant_promotions_used.filter(
                promotion_variant__type=PromotionVariantType.OTHER_VARIANT
            )
            for promotion in variant_promotions:
                items_gift: list[OrdersItemsPromotion] = promotion.items_promotion.all()
                for item in items_gift:
                    WarehouseInventoryAvailable.create_or_update(
                        user=created_by,
                        variant_id=item.variant.id,
                        quantity_confirm_up=transform_quantity(item.quantity, confirm_exp),
                        quantity_non_confirm_up=transform_quantity(item.quantity, non_confirm_exp),
                        code=order_key,
                        is_export=is_export,
                    )


# pylint: disable=R0912
@receiver(pre_save, sender=Orders)
def update_inventory_available(sender, instance, **kwargs):
    old_instance = Orders.objects.filter(id=instance.id).first()
    user = None
    confirm_exp = None
    non_confirm_exp = None
    if not old_instance:
        if instance.status == OrderStatus.DRAFT:
            non_confirm_exp = "+"
        if instance.status == OrderStatus.COMPLETED:
            confirm_exp = "+"
            # update complete time and completed by
            instance.complete_time = datetime.now()
            instance.completed_by = instance.created_by
        user = instance.created_by
    else:
        if old_instance.status == OrderStatus.DRAFT and instance.status == OrderStatus.COMPLETED:
            non_confirm_exp = "-"
            confirm_exp = "+"
            # update complete time and completed by
            instance.complete_time = datetime.now()
            instance.completed_by = instance.modified_by
        elif old_instance.status == OrderStatus.DRAFT and instance.status == OrderStatus.CANCEL:
            non_confirm_exp = "-"
        elif old_instance.status == OrderStatus.COMPLETED and instance.status == OrderStatus.CANCEL:
            if instance.warehouse_sheet_import_export_order.exists() and instance.warehouse_sheet_import_export_order.first().is_confirm:
                confirm_exp = None
            else:
                confirm_exp = "-"
        user = instance.modified_by

    calculate_warehouse_inventory(instance, user, confirm_exp, non_confirm_exp, instance.order_key)
    print("Signal update inventory available done.")
