from django.urls import path
from rest_framework.routers import DefaultRouter

from warehouses.api import views

router = DefaultRouter()
router.register("inventory-reasons", views.WarehouseInventoryReasonViewSet, basename="inventory-reasons")
router.register("inventory-logs", views.WarehouseInventoryLogsViewSet, basename="inventory-logs")
router.register("inventory-available", views.WarehouseInventoryAvailableViewSet, basename="inventory-available")
router.register("sheet-import-export", views.WarehouseSheetImportExportViewSet, basename="sheet-import-export")
router.register("sheet-check", views.WarehouseSheetCheckViewSet, basename="sheet-check")
router.register("sheet-transfer", views.WarehouseSheetTransferViewSet, basename="sheet-transfer")
router.register("", views.WarehouseViewSet, basename="warehouse")

urlpatterns = [
    path("inventory/", views.WarehouseInventoryListAPIView.as_view(), name="inventory"),
    path("inventory-with-variant/", views.WarehouseInventoryVariantListAPIView.as_view(), name="inventory-with-variant"),
    path(
        "sheet-import-export/bulk-update-is-confirm/",
        views.WarehouseSheetImportExportBulkUpdateView.as_view(),
        name="sheet-import-export-bulk-update-is-confirm",
    ),
    path(
        "sheet-check/bulk-update-is-confirm/", views.WarehouseSheetCheckBulkUpdateView.as_view(), name="sheet-check-bulk-update-is-confirm"
    ),
    path(
        "sheet-transfer/bulk-update-is-confirm/",
        views.WarehouseSheetTransferBulkUpdateView.as_view(),
        name="sheet-transfer-bulk-update-is-confirm",
    ),
    path(
        "inventory-available/<uuid:id>/history/",
        views.WarehouseInventoryAvailableHistoryAPIView.as_view(),
        name="inventory-available-history",
    ),
    path("inventory/report/", views.ReportWarehouseView.as_view(), name="warehouse-inventory-report"),
    path("inventory/category/report/", views.ReportWarehouseCategoryView.as_view(), name="warehouse-inventory-category-report"),
] + router.urls
