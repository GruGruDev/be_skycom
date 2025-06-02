import uuid

from django.db import models
from django.db import transaction
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from orders.models import Orders
from products.models import ProductsVariants
from products.models import ProductsVariantsBatches
from users.models import User
from utils.enums import SequenceType
from warehouses.enums import SheetCheckType
from warehouses.enums import SheetImportExportType
from warehouses.enums import SheetTransferType
from warehouses.enums import WarehouseBaseType


class SequenceIdentity(models.Model):
    type = models.CharField(choices=SequenceType.choices(), max_length=10, unique=True)
    value = models.PositiveIntegerField(default=0, blank=True, null=True)

    def __str__(self):
        return self.last_code()

    def last_code(self):
        return "%s%06d" % (str(self.type), self.value)

    def next_code(self):
        return "%s%06d" % (str(self.type), self.value + 1)

    @classmethod
    def get_code_by_type(cls, type):
        try:
            seq: cls = cls.objects.select_for_update().get(type=f"#{type}")
        except cls.DoesNotExist:
            seq: cls = cls.objects.create(type=f"#{type}")
        return seq

    class Meta:
        db_table = "tbl_Sequence_Identity"
        ordering = ["-value"]


class Warehouse(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    name = models.CharField(max_length=255, unique=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_modified")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_created")
    manager_name = models.CharField(max_length=255, null=True, blank=True)
    manager_phone = models.CharField(max_length=255, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    is_sales = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        db_table = "tbl_Warehouse"


class WarehouseInventory(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_inventory_modified")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_inventory_created")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_inventory_warehouse")
    product_variant_batch = models.ForeignKey(
        ProductsVariantsBatches, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_inventory_product_variant_batch"
    )
    quantity = models.DecimalField(max_digits=15, decimal_places=4, default=0.0)
    history = HistoricalRecords(
        history_id_field=models.UUIDField(default=uuid.uuid4),
        table_name="tbl_Warehouse_Inventory_Historical",
    )

    class Meta:
        ordering = ["-created"]
        db_table = "tbl_Warehouse_Inventory"
        unique_together = ["warehouse", "product_variant_batch"]


class WarehouseInventoryReason(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    modified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_inventory_reason_modified"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_inventory_reason_created"
    )

    type = models.CharField(max_length=2, choices=WarehouseBaseType.choices())
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["-created"]
        db_table = "tbl_Warehouse_Inventory_Reason"
        unique_together = ("type", "name")


class WarehouseInventoryAvailable(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    modified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_inventory_available_modified"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_inventory_available_created"
    )

    product_variant = models.OneToOneField(
        ProductsVariants, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_inventory_available_product_variant"
    )
    note = models.TextField(blank=True, null=True)
    quantity_confirm = models.DecimalField(max_digits=15, decimal_places=4, default=0.0)  # đơn đã xác nhận
    quantity_non_confirm = models.DecimalField(max_digits=15, decimal_places=4, default=0.0)  # đơn chưa xác nhận
    quantity_export = models.DecimalField(max_digits=15, decimal_places=4, default=0.0, null=True)  # đơn đã xuất
    history = HistoricalRecords(
        history_id_field=models.UUIDField(default=uuid.uuid4),
        table_name="tbl_Warehouse_Inventory_Available_Historical",
    )

    class Meta:
        ordering = ["-created"]
        db_table = "tbl_Warehouse_Inventory_Available"

    @classmethod
    def create_or_update(cls, user, variant_id, quantity_confirm_up, quantity_non_confirm_up, code, is_export=False):
        try:
            inst = cls.objects.get(product_variant_id=variant_id)
            inst.quantity_confirm = inst.quantity_confirm + quantity_confirm_up
            inst.quantity_non_confirm = inst.quantity_non_confirm + quantity_non_confirm_up
            inst.note = code
            if is_export:
                inst.quantity_export = inst.quantity_export - quantity_confirm_up
            inst.save()
        except cls.DoesNotExist:
            inst = cls.objects.create(
                created_by=user,
                product_variant_id=variant_id,
                quantity_confirm=quantity_confirm_up,
                quantity_non_confirm=quantity_non_confirm_up,
                note=code,
            )
        return inst


class WarehouseInventoryLog(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_inventory_log_modified")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_inventory_log_created")

    product_variant_batch = models.ForeignKey(
        ProductsVariantsBatches,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="warehouse_inventory_log_product_variant_batch",
    )

    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_inventory_log_warehouse"
    )

    quantity = models.DecimalField(max_digits=15, decimal_places=4, default=0.0)

    change_reason = models.ForeignKey(
        WarehouseInventoryReason, null=True, on_delete=models.CASCADE, related_name="warehouse_inventory_log_change_reason"
    )

    type = models.CharField(max_length=2, choices=WarehouseBaseType.choices())

    sheet_code = models.CharField(max_length=255)

    class Meta:
        ordering = ["-created"]
        db_table = "tbl_Warehouse_Inventory_Logs"

    # Mục đích để cho các logic signal liên quan model này
    # đảm bảo tính nhất quán của dữ liệu
    @transaction.atomic()
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class WarehouseSheetImportExport(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    code = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=2, choices=SheetImportExportType.choices())
    modified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_import_export_modified"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_import_export_created"
    )

    confirm_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_import_export_confirm_by"
    )
    confirm_date = models.DateTimeField(blank=True, null=True)

    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_import_export_warehouse"
    )

    change_reason = models.ForeignKey(
        WarehouseInventoryReason, null=True, on_delete=models.CASCADE, related_name="warehouse_sheet_import_export_change_reason"
    )

    order = models.ForeignKey(Orders, on_delete=models.SET_NULL, related_name="warehouse_sheet_import_export_order", blank=True, null=True)

    note = models.TextField(blank=True, null=True)
    is_delete = models.BooleanField(default=False)
    is_confirm = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created"]
        db_table = "tbl_Warehouse_Sheet_Import_Export"


class WarehouseSheetImportExportDetail(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    modified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_import_export_detail_modified"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_import_export_detail_created"
    )

    sheet = models.ForeignKey(
        WarehouseSheetImportExport,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="warehouse_sheet_import_export_detail_sheet",
    )

    product_variant_batch = models.ForeignKey(
        ProductsVariantsBatches,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="warehouse_sheet_import_export_detail_product_variant_batch",
    )

    quantity = models.DecimalField(max_digits=15, decimal_places=4, default=0.0)

    class Meta:
        ordering = ["-created"]
        db_table = "tbl_Warehouse_Sheet_Import_Export_Detail"


class WarehouseSheetTransfer(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    code = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=2, choices=SheetTransferType.choices())
    modified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_transfer_modified"
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_transfer_created")

    confirm_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_transfer_confirm_by"
    )
    confirm_date = models.DateTimeField(blank=True, null=True)

    change_reason = models.ForeignKey(
        WarehouseInventoryReason, on_delete=models.CASCADE, related_name="warehouse_sheet_transfer_change_reason"
    )

    note = models.TextField(blank=True, null=True)
    is_delete = models.BooleanField(default=False)
    is_confirm = models.BooleanField(default=False)

    warehouse_from = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_transfer_warehouse_from"
    )

    warehouse_to = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_transfer_warehouse_to"
    )

    class Meta:
        ordering = ["-created"]
        db_table = "tbl_Warehouse_Sheet_Transfer"


class WarehouseSheetTransferDetail(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    modified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_transfer_detail_modified"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_transfer_detail_created"
    )

    sheet = models.ForeignKey(
        WarehouseSheetTransfer, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_transfer_detail_sheet"
    )

    product_variant_batch = models.ForeignKey(
        ProductsVariantsBatches,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="warehouse_sheet_transfer_detail_product_variant_batch",
    )

    quantity = models.DecimalField(max_digits=15, decimal_places=4, default=0.0)

    class Meta:
        ordering = ["-created"]
        db_table = "tbl_Warehouse_Sheet_Transfer_Detail"


class WarehouseSheetCheck(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    code = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=2, choices=SheetCheckType.choices())
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_check_modified")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_check_created")

    confirm_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_check_confirm_by")
    confirm_date = models.DateTimeField(blank=True, null=True)

    change_reason = models.ForeignKey(
        WarehouseInventoryReason, on_delete=models.CASCADE, related_name="warehouse_sheet_check_change_reason"
    )

    note = models.TextField(blank=True, null=True)
    is_delete = models.BooleanField(default=False)
    is_confirm = models.BooleanField(default=False)

    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_check_warehouse"
    )

    class Meta:
        ordering = ["-created"]
        db_table = "tbl_Warehouse_Sheet_Check"


class WarehouseSheetCheckDetail(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    modified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_check_detail_modified"
    )

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_check_detail_created"
    )

    sheet = models.ForeignKey(
        WarehouseSheetCheck, on_delete=models.SET_NULL, blank=True, null=True, related_name="warehouse_sheet_check_detail_sheet"
    )

    product_variant_batch = models.ForeignKey(
        ProductsVariantsBatches,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="warehouse_sheet_check_detail_product_variant_batch",
    )

    quantity_system = models.DecimalField(max_digits=15, decimal_places=4, null=True)
    quantity_actual = models.DecimalField(max_digits=15, decimal_places=4, default=0.0)

    class Meta:
        ordering = ["-created"]
        db_table = "tbl_Warehouse_Sheet_Check_Detail"
