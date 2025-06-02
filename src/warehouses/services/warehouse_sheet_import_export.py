from warehouses.api.views import WarehouseSheetImportExportViewSet
from warehouses.models import WarehouseInventoryReason


class WarehouseSheetImportExportService:
    def __init__(self, data: dict, sheet=None):
        self.data = data
        self.sheet = sheet

    def create_new_sheet(self, created_by):
        sheet_import_export_view_set = WarehouseSheetImportExportViewSet()
        sheet_import_export_create_serializer_class = sheet_import_export_view_set.serializer_classes.get("create")
        sheet_import_export_create_serializer = sheet_import_export_create_serializer_class(data=self.data)
        sheet_import_export_create_serializer.is_valid(raise_exception=True)
        new_sheet = sheet_import_export_view_set.perform_create(serializer=sheet_import_export_create_serializer, current_user=created_by)
        return new_sheet

    def update_sheet(self, modified_by):
        sheet_import_export_view_set = WarehouseSheetImportExportViewSet()
        sheet_import_export_update_serializer_class = sheet_import_export_view_set.serializer_classes.get("partial_update")
        sheet_import_export_update_serializer = sheet_import_export_update_serializer_class(
            instance=self.sheet, data=self.data, partial=True
        )
        sheet_import_export_update_serializer.is_valid(raise_exception=True)
        new_sheet = sheet_import_export_view_set.perform_update(serializer=sheet_import_export_update_serializer, current_user=modified_by)
        return new_sheet

    @classmethod
    def from_shipment_to_create_sheet(
        cls, sheet_detail: list[dict], warehouse_id: str, order_code: str, sheet_type: str, change_reason_name: str, is_confirm=False
    ):
        # Tìm hoặc tạo mới lý do tạo phiếu
        change_reason, _ = WarehouseInventoryReason.objects.get_or_create(
            type=sheet_type,
            name=change_reason_name,
        )

        return cls(
            data={
                "sheet_detail": sheet_detail,
                "type": sheet_type,
                "is_confirm": is_confirm,
                "change_reason": change_reason.id,
                "warehouse": warehouse_id,
                "order_code": order_code,
            }
        )

    @classmethod
    def from_shipment_to_update_sheet(cls, sheet, is_confirm: bool, change_reason_name: str):
        # Tìm hoặc tạo mới lý do update phiếu
        change_reason, _ = WarehouseInventoryReason.objects.get_or_create(
            type=sheet.type,
            name=change_reason_name,
        )

        return cls(sheet=sheet, data={"is_confirm": is_confirm, "change_reason": change_reason.id})
