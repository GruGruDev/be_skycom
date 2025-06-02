from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.dispatch import receiver
from rest_framework.exceptions import ValidationError

from orders.signals import calculate_warehouse_inventory
from products.enums import ProductType
from users.models import UserActionLog
from warehouses.enums import SheetImportExportType
from warehouses.models import WarehouseInventory
from warehouses.models import WarehouseInventoryLog
from warehouses.models import WarehouseSheetCheckDetail
from warehouses.models import WarehouseSheetImportExport
from warehouses.models import WarehouseSheetImportExportDetail
from warehouses.models import WarehouseSheetTransferDetail


@receiver(post_save, sender=WarehouseInventoryLog)
def update_warehouse_inventory(sender, instance, **kwargs):
    created_by = instance.created_by
    product_variant_batch = instance.product_variant_batch
    warehouse = instance.warehouse
    quantity = instance.quantity

    warehouse_inventory = WarehouseInventory.objects.filter(warehouse=warehouse, product_variant_batch=product_variant_batch).first()

    if warehouse_inventory:
        # Update warehouse inventory
        warehouse_inventory.modified_by = created_by
        warehouse_inventory.quantity += quantity

        if warehouse_inventory.quantity < 0:
            raise ValidationError(
                {
                    "quantity": f"Lô {product_variant_batch.name}, "
                    f"sản phẩm {product_variant_batch.product_variant.name} không đủ tồn kho."
                }
            )

        warehouse_inventory.save()
    else:
        # Create warehouse inventory
        new_warehouse_inventory = WarehouseInventory.objects.create(
            created_by=created_by, warehouse=warehouse, product_variant_batch=product_variant_batch, quantity=quantity
        )

        if new_warehouse_inventory.quantity < 0:
            raise ValidationError(
                {
                    "quantity": f"Số lượng tồn của lô {product_variant_batch.name}, "
                    f"sản phẩm {product_variant_batch.product_variant.name} - kho không được âm."
                }
            )


@receiver(post_save, sender=WarehouseSheetImportExportDetail)
def create_action_log(sender, instance, **kwargs):
    data = {
        "object_id": instance.sheet.id,
        "user_id": instance.created_by_id,
        "action_type": "Create",
        "action_name": "WAREHOUSES",
        "status": "Success",
    }

    batch_name = str(instance.product_variant_batch.name)
    batch_type = "biến thể" if instance.product_variant_batch.type == ProductType.VARIANT.value else "nguyên liệu"
    product_name = (
        instance.product_variant_batch.product_variant.name
        if instance.product_variant_batch.type == ProductType.VARIANT.value
        else instance.product_variant_batch.product_material.name
    )
    batch_type_message = f"{batch_type} {product_name}, "

    action = "nhập" if instance.sheet.type == SheetImportExportType.IMPORT.value else "xuất"

    #
    data["message"] = (
        f"Tạo phiếu {action} cho lô {batch_name}, " + batch_type_message + f"số lượng {instance.quantity}, mã phiếu {instance.sheet.code}"
    )

    if instance.sheet.type != SheetImportExportType.IMPORT.value and instance.sheet.order:
        data["message"] += f", đơn hàng {instance.sheet.order.order_key}"

    UserActionLog.objects.create(**data)


@receiver(post_save, sender=WarehouseSheetTransferDetail)
def create_action_log_sheet_transfer(sender, instance, **kwargs):
    data = {
        "object_id": instance.sheet.id,
        "user_id": instance.created_by_id,
        "action_name": "WAREHOUSES",
        "status": "Success",
    }
    if instance._state.adding:
        data["action_type"] = "Create"
    else:
        data["action_type"] = "Update"

    batch_name = str(instance.product_variant_batch.name)
    batch_type = "biến thể" if instance.product_variant_batch.type == ProductType.VARIANT.value else "nguyên liệu"
    product_name = (
        instance.product_variant_batch.product_variant.name
        if instance.product_variant_batch.type == ProductType.VARIANT.value
        else instance.product_variant_batch.product_material.name
    )
    batch_type_message = f"{batch_type} {product_name}, "

    #
    data["message"] = (
        f"Tạo phiếu chuyển cho lô {batch_name}, " + batch_type_message + f"số lượng {instance.quantity}, mã phiếu {instance.sheet.code}"
    )

    UserActionLog.objects.create(**data)


@receiver(post_save, sender=WarehouseSheetCheckDetail)
def create_action_log_sheet_check(sender, instance, **kwargs):
    data = {
        "object_id": instance.sheet.id,
        "user_id": instance.created_by_id,
        "action_name": "WAREHOUSES",
        "status": "Success",
    }
    if instance._state.adding:
        data["action_type"] = "Create"
    else:
        data["action_type"] = "Update"

    batch_name = str(instance.product_variant_batch.name)
    batch_type = "biến thể" if instance.product_variant_batch.type == ProductType.VARIANT.value else "nguyên liệu"
    product_name = (
        instance.product_variant_batch.product_variant.name
        if instance.product_variant_batch.type == ProductType.VARIANT.value
        else instance.product_variant_batch.product_material.name
    )
    batch_type_message = f"{batch_type} {product_name}, "

    #
    data["message"] = (
        f"Tạo phiếu kiểm cho lô {batch_name}, {batch_type_message}, "
        f"kho {instance.sheet.warehouse.name}, "
        f"số lượng hệ thống {instance.quantity_system}, "
        f"số lượng thực tế {instance.quantity_actual}, mã phiếu {instance.sheet.code}"
    )

    UserActionLog.objects.create(**data)
