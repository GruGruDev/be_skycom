# pylint: disable=C0302
from collections import defaultdict
from decimal import Decimal

import pandas as pd
import pytz
from dateutil import parser
from django.db import transaction
from django.db.models import JSONField
from django.db.models import OuterRef
from django.db.models import Subquery
from django.db.models import Value
from django.db.models.expressions import Func
from django.db.models.functions import Cast
from django.utils import timezone
from django_filters import rest_framework as django_filters
from rest_framework import filters
from rest_framework import generics
from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.views import CustomModelViewSet
from orders.enums import OrderStatus
from orders.models import Orders
from products.enums import ProductVariantType
from products.models import ProductsVariants
from users.activity_log import ActivityLogMixin
from utils.basic import data_sortby
from utils.serializers import PassSerializer
from warehouses import models
from warehouses.api.filters import ProductWarehouseReportFilter
from warehouses.api.filters import ReportWarehouseCategoryFilterset
from warehouses.api.filters import WarehouseFilterset
from warehouses.api.filters import WarehouseInventoryAvailableFilterSet
from warehouses.api.filters import WarehouseInventoryFilterSet
from warehouses.api.filters import WarehouseInventoryLogFilterSet
from warehouses.api.filters import WarehouseInventoryReasonFilterSet
from warehouses.api.filters import WarehouseInventoryVariantFilterSet
from warehouses.api.filters import WarehouseSheetCheckFilterSet
from warehouses.api.filters import WarehouseSheetImportExportFilterSet
from warehouses.api.filters import WarehouseSheetTransferFilterSet
from warehouses.api.serializers import warehouse
from warehouses.api.serializers import warehouse_inventory
from warehouses.api.serializers import warehouse_inventory_available
from warehouses.api.serializers import warehouse_inventory_logs
from warehouses.api.serializers import warehouse_inventory_reason
from warehouses.api.serializers import warehouse_sheet_check
from warehouses.api.serializers import warehouse_sheet_import_export
from warehouses.api.serializers import warehouse_sheet_transfer
from warehouses.api.serializers.report import ReportWarehouseSerializer
from warehouses.api.serializers.warehouse_inventory_available import WarehouseInventoryAvailableHistorySerializer
from warehouses.enums import SheetCheckType
from warehouses.enums import SheetImportExportType
from warehouses.enums import SheetTransferType
from warehouses.models import SequenceIdentity
from warehouses.models import WarehouseInventory
from warehouses.models import WarehouseInventoryAvailable
from warehouses.models import WarehouseInventoryLog
from warehouses.models import WarehouseSheetCheck
from warehouses.models import WarehouseSheetImportExport
from warehouses.models import WarehouseSheetTransfer
from warehouses.reports import process_images
from warehouses.reports import ReportWarehouse
from warehouses.reports import get_report_category_inventory


class WarehouseViewSet(CustomModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    queryset = models.Warehouse.objects.prefetch_related(
        "addresses", "addresses__ward", "addresses__ward__district", "addresses__ward__province"
    ).all()
    default_serializer_class = warehouse.WarehouseReadOneSerializer
    filter_backends = (filters.OrderingFilter, filters.SearchFilter, django_filters.DjangoFilterBackend)
    filterset_class = WarehouseFilterset
    search_fields = ("name", "manager_name", "manager_phone", "addresses__address")
    ordering_fields = "__all__"
    serializer_classes = {
        "create": warehouse.WarehouseCreateSerializer,
        "partial_update": warehouse.WarehouseUpdateSerializer,
        "list": warehouse.WarehouseReadListSerializer,
        "retrieve": warehouse.WarehouseReadOneSerializer,
    }

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.default_serializer_class)

    def perform_create(self, serializer):
        serializer.validated_data["created_by"] = self.request.user
        return super().perform_create(serializer)

    def perform_update(self, serializer):
        serializer.validated_data["modified_by"] = self.request.user
        return super().perform_update(serializer)


class WarehouseInventoryReasonViewSet(CustomModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.WarehouseInventoryReason.objects.all()
    default_serializer_class = warehouse_inventory_reason.WarehouseInventoryReasonReadOneSerializer

    serializer_classes = {
        "create": warehouse_inventory_reason.WarehouseInventoryReasonCreateSerializer,
        "partial_update": warehouse_inventory_reason.WarehouseInventoryReasonUpdateSerializer,
        "list": warehouse_inventory_reason.WarehouseInventoryReasonReadListSerializer,
        "retrieve": warehouse_inventory_reason.WarehouseInventoryReasonReadOneSerializer,
    }
    filter_backends = (
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    )
    ordering_fields = "__all__"
    filterset_class = WarehouseInventoryReasonFilterSet

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.default_serializer_class)

    def perform_create(self, serializer):
        serializer.validated_data["created_by"] = self.request.user
        return super().perform_create(serializer)

    def perform_update(self, serializer):
        serializer.validated_data["modified_by"] = self.request.user
        return super().perform_update(serializer)


class WarehouseInventoryListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.WarehouseInventory.objects.all()
    serializer_class = warehouse_inventory.WarehouseInventoryReadDetailSerializer
    filter_backends = (
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    )
    ordering_fields = "__all__"
    filterset_class = WarehouseInventoryFilterSet


class WarehouseInventoryLogsViewSet(CustomModelViewSet):
    http_method_names = ["get"]
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.WarehouseInventoryLog.objects.prefetch_related(
        "product_variant_batch__product_variant__images",
        "product_variant_batch__product_material__images",
        "warehouse",
        "change_reason",
    ).all()
    default_serializer_class = warehouse_inventory_logs.WarehouseInventoryLogReadOneSerializer

    serializer_classes = {
        "list": warehouse_inventory_logs.WarehouseInventoryLogReadListSerializer,
        "retrieve": warehouse_inventory_logs.WarehouseInventoryLogReadOneSerializer,
    }

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, django_filters.DjangoFilterBackend)
    search_fields = (
        "sheet_code",
        "product_variant_batch__product_variant__name",
        "product_variant_batch__product_variant__SKU_code",
        "product_variant_batch__product_material__name",
        "product_variant_batch__product_material__SKU_code",
        "product_variant_batch__name",
        "warehouse__name",
        "change_reason__name",
    )
    filterset_class = WarehouseInventoryLogFilterSet
    ordering_fields = "__all__"

    def build_sheet_subquery(self, sheet_model):
        return (
            sheet_model.objects.filter(code=OuterRef("sheet_code"))
            .annotate(
                sheet_data=Cast(
                    Func(
                        Value("id"),
                        "id",
                        Value("is_confirm"),
                        "is_confirm",
                        Value("created_by"),
                        "created_by",
                        Value("confirm_by"),
                        "confirm_by",
                        Value("confirm_date"),
                        "confirm_date",
                        Value("note"),
                        "note",
                        function="json_build_object",
                    ),
                    output_field=JSONField(),
                )
            )
            .values("sheet_data")[:1]
        )

    def get_queryset_sheet(self, queryset):
        import_export_sheet_subquery = self.build_sheet_subquery(WarehouseSheetImportExport)
        transfer_sheet_subquery = self.build_sheet_subquery(WarehouseSheetTransfer)
        check_sheet_subquery = self.build_sheet_subquery(WarehouseSheetCheck)

        queryset = queryset.annotate(
            import_export_sheet=Subquery(import_export_sheet_subquery),
            check_sheet=Subquery(check_sheet_subquery),
            transfer_sheet=Subquery(transfer_sheet_subquery),
        )
        return queryset

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.default_serializer_class)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        queryset = self.get_queryset_sheet(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class WarehouseInventoryAvailableViewSet(CustomModelViewSet):
    http_method_names = ["get"]
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.WarehouseInventoryAvailable.objects.prefetch_related(
        "product_variant",
    ).all()
    default_serializer_class = warehouse_inventory_available.WarehouseInventoryAvailableReadOneSerializer

    serializer_classes = {
        "list": warehouse_inventory_available.WarehouseInventoryAvailableReadListSerializer,
        "retrieve": warehouse_inventory_available.WarehouseInventoryAvailableReadOneSerializer,
    }
    filter_backends = (
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    )
    ordering_fields = "__all__"
    filterset_class = WarehouseInventoryAvailableFilterSet

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.default_serializer_class)


class WarehouseSheetImportExportViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    permission_classes = [permissions.IsAuthenticated]
    queryset = (
        models.WarehouseSheetImportExport.objects.select_related(
            "order",
            "warehouse",
            "change_reason",
        )
        .prefetch_related(
            "warehouse_sheet_import_export_detail_sheet__product_variant_batch__product_variant__images",
            "warehouse_sheet_import_export_detail_sheet__product_variant_batch__product_material",
            "warehouse__addresses",
        )
        .all()
    )
    default_serializer_class = warehouse_sheet_import_export.WarehouseSheetImportExportReadOneSerializer

    serializer_classes = {
        "create": warehouse_sheet_import_export.WarehouseSheetImportExportCreateSerializer,
        "partial_update": warehouse_sheet_import_export.WarehouseSheetImportExportUpdateSerializer,
        "list": warehouse_sheet_import_export.WarehouseSheetImportExportReadListSerializer,
        "retrieve": warehouse_sheet_import_export.WarehouseSheetImportExportReadOneSerializer,
    }
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, django_filters.DjangoFilterBackend)
    search_fields = (
        "code",
        "order__order_key",
        "note",
        "warehouse__name",
        "warehouse_sheet_import_export_detail_sheet__product_variant_batch__product_variant__SKU_code",
        "warehouse_sheet_import_export_detail_sheet__product_variant_batch__product_material__SKU_code",
        "warehouse_sheet_import_export_detail_sheet__product_variant_batch__name",
    )
    ordering_fields = "__all__"
    filterset_class = WarehouseSheetImportExportFilterSet

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.default_serializer_class)

    def perform_create(self, serializer, current_user=None):
        current_user = current_user or self.request.user
        validated_data = serializer.validated_data
        validated_data["created_by"] = current_user

        sheet_type = validated_data["type"]
        sheet_is_confirm = validated_data["is_confirm"]
        sheet_warehouse = validated_data["warehouse"]
        sheet_change_reason = validated_data.get("change_reason")
        sheet_order_key = validated_data.pop("order_key", None)
        list_sheet_detail = validated_data.pop("sheet_detail", [])

        with transaction.atomic():
            sheet_code = self._generate_sheet_code(sheet_type)
            validated_data["code"] = sheet_code

            if sheet_is_confirm:
                self._set_confirmation_data(validated_data, current_user)

            if sheet_order_key:
                order = self._get_order(sheet_order_key, sheet_type)
                validated_data["order"] = order
                self._validate_sheet_details(list_sheet_detail, order, sheet_order_key)

            new_sheet = serializer.save()
            self._create_sheet_details(new_sheet, list_sheet_detail, current_user)

            if sheet_is_confirm:
                if sheet_type == SheetImportExportType.EXPORT.value:
                    self._update_warehouse_inventory_available(list_sheet_detail, sheet_code, current_user)
                self._create_inventory_logs(new_sheet, list_sheet_detail, current_user, sheet_warehouse, sheet_change_reason, sheet_type)

            return new_sheet

    def perform_update(self, serializer, current_user=None):
        current_user = current_user or self.request.user
        validated_data = serializer.validated_data
        validated_data["modified_by"] = current_user
        new_sheet_is_confirm = validated_data.get("is_confirm")
        sheet_order_key = validated_data.pop("order_key", None)

        with transaction.atomic():
            old_sheet = serializer.instance
            old_sheet_code = old_sheet.code
            old_sheet_is_confirm = old_sheet.is_confirm
            old_list_sheet_detail = old_sheet.warehouse_sheet_import_export_detail_sheet.all()

            if new_sheet_is_confirm is False and old_sheet_is_confirm is True:
                raise ValidationError({"is_confirm": "Không thể cập nhật trạng thái xác nhận từ True -> False."})

            if sheet_order_key:
                order = self._get_order(sheet_order_key, old_sheet.type)
                validated_data["order"] = order
                self._validate_sheet_details(old_list_sheet_detail, order, sheet_order_key)

            if old_sheet_is_confirm is False and new_sheet_is_confirm is True:
                if not sheet_order_key and old_sheet.order:
                    if old_sheet.order.status == OrderStatus.CANCEL.value:
                        raise ValidationError({"order": f"Đơn hàng {order.order_key} đã bị hủy."})
                self._set_confirmation_data(validated_data, current_user)
                if old_sheet.type == SheetImportExportType.EXPORT.value:
                    self._update_warehouse_inventory_available(old_list_sheet_detail, old_sheet_code, current_user)
                self._create_inventory_logs(old_sheet, old_list_sheet_detail, current_user)

            return serializer.save()

    @staticmethod
    def _generate_sheet_code(sheet_type):
        seq = SequenceIdentity.get_code_by_type(sheet_type)
        code = seq.next_code()
        seq.value += 1
        seq.save()
        return code

    @staticmethod
    def _set_confirmation_data(data, user):
        data["confirm_date"] = timezone.now()
        data["confirm_by"] = user

    @staticmethod
    def _get_order(order_key, sheet_type):
        order = Orders.objects.filter(order_key=order_key).first()
        if not order:
            raise ValidationError({"order_code": "Không tìm thấy đơn hàng tương ứng."})
        if order.warehouse_sheet_import_export_order.filter(type=sheet_type).exists():
            raise ValidationError({"order": f"Đơn hàng {order_key} đã tồn tại phiếu."})
        if order.status == OrderStatus.CANCEL.value:
            raise ValidationError({"order": f"Đơn hàng {order_key} đã bị hủy."})
        return order

    @staticmethod
    def _validate_sheet_details(sheet_details, order, order_key):
        length_order_items, order_items = order.items_list()
        if len(sheet_details) != length_order_items:
            raise ValidationError({"product_variant": "Số sản phẩm của sheet detail không bằng số sản phẩm có trong order tương ứng."})

        order_variants = {item["code"]: item["quantity"] for item in order_items}

        item_details = {}
        for detail in sheet_details:
            if isinstance(detail, dict):
                product_variant_batch = detail.get("product_variant_batch", None)
                quantity = abs(detail.get("quantity", 0))
            else:
                product_variant_batch = getattr(detail, "product_variant_batch", None)
                quantity = abs(getattr(detail, "quantity", 0))
            product_variant = product_variant_batch.product_variant
            product_id = str(product_variant.id)
            product_name = product_variant.name

            if product_id not in order_variants:
                raise ValidationError({"product_variant": f"Sản phẩm {product_name} không có trong đơn hàng {order_key}."})

            if item_details.get(product_id):
                item_details[product_id].update({"quantity": item_details[product_id]["quantity"] + quantity})
            else:
                item_details[product_id] = {"quantity": quantity, "name": product_name}

        for product_id, values in item_details.items():
            quantity = values["quantity"]
            product_name = values["name"]
            if quantity != order_variants[product_id]:
                raise ValidationError(
                    {
                        "quantity": f"Số lượng sản phẩm {product_name} không tương ứng với số lượng trong đơn hàng {order_key}. "
                        f"Số lượng trong đơn hàng: {order_variants[product_id]}, "
                        f"Số lượng trong phiếu: {quantity}."
                    }
                )

    @staticmethod
    def _create_sheet_details(sheet, sheet_details, user):
        for detail in sheet_details:
            sheet.warehouse_sheet_import_export_detail_sheet.create(created_by=user, **detail)

    @staticmethod
    def _update_warehouse_inventory_available(sheet_details, sheet_code, user):
        for detail in sheet_details:
            if isinstance(detail, dict):
                product_variant_batch = detail.get("product_variant_batch", None)
                quantity = detail.get("quantity", 0)
            else:
                product_variant_batch = getattr(detail, "product_variant_batch", None)
                quantity = getattr(detail, "quantity", 0)
            product_variant = product_variant_batch.product_variant
            product_variant_id = str(product_variant.id)

            # caculator inventory
            WarehouseInventoryAvailable.create_or_update(
                user=user, variant_id=product_variant_id, quantity_confirm_up=quantity, quantity_non_confirm_up=0, code=sheet_code
            )

    @staticmethod
    def _create_inventory_logs(sheet, sheet_details, user, sheet_warehouse=None, change_reason=None, sheet_type=None):
        for detail in sheet_details:
            if isinstance(detail, dict):
                product_variant_batch = detail.get("product_variant_batch", None)
                quantity = detail.get("quantity", 0)
            else:
                product_variant_batch = getattr(detail, "product_variant_batch", None)
                quantity = getattr(detail, "quantity", 0)
            WarehouseInventoryLog.objects.create(
                created_by=user,
                product_variant_batch=product_variant_batch,
                warehouse=sheet_warehouse or sheet.warehouse,
                quantity=quantity,
                change_reason=change_reason or sheet.change_reason,
                type=sheet_type or sheet.type,
                sheet_code=sheet.code,
            )


class WarehouseSheetCheckViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    permission_classes = [permissions.IsAuthenticated]
    queryset = (
        models.WarehouseSheetCheck.objects.select_related(
            "warehouse",
            "change_reason",
        )
        .prefetch_related(
            "warehouse_sheet_check_detail_sheet__product_variant_batch__product_variant__images",
            "warehouse_sheet_check_detail_sheet__product_variant_batch__product_material",
            "warehouse__addresses",
        )
        .all()
    )
    default_serializer_class = warehouse_sheet_check.WarehouseSheetCheckReadOneSerializer

    serializer_classes = {
        "create": warehouse_sheet_check.WarehouseSheetCheckCreateSerializer,
        "partial_update": warehouse_sheet_check.WarehouseSheetCheckUpdateSerializer,
        "list": warehouse_sheet_check.WarehouseSheetCheckReadListSerializer,
        "retrieve": warehouse_sheet_check.WarehouseSheetCheckReadOneSerializer,
    }
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, django_filters.DjangoFilterBackend)
    search_fields = (
        "code",
        "note",
        "warehouse_sheet_check_detail_sheet__product_variant_batch__product_variant__SKU_code",
        "warehouse_sheet_check_detail_sheet__product_variant_batch__product_material__SKU_code",
        "warehouse_sheet_check_detail_sheet__product_variant_batch__name",
    )
    ordering_fields = "__all__"
    filterset_class = WarehouseSheetCheckFilterSet

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.default_serializer_class)

    def perform_create(self, serializer):
        current_user = self.request.user
        validated_data = serializer.validated_data
        sheet_type = SheetCheckType.CHECK
        validated_data["created_by"] = current_user
        validated_data["type"] = sheet_type

        sheet_is_confirm = validated_data["is_confirm"]
        sheet_warehouse = validated_data["warehouse"]
        sheet_change_reason = validated_data["change_reason"]

        list_sheet_detail = validated_data.pop("sheet_detail")

        with transaction.atomic():
            seq = SequenceIdentity.get_code_by_type(sheet_type)
            validated_data["code"] = seq.next_code()
            seq.value += 1
            seq.save()

            if sheet_is_confirm:
                validated_data["confirm_date"] = timezone.now()
                validated_data["confirm_by"] = current_user

            # Tạo phiếu check.
            new_sheet = serializer.save()

            for sheet_detail in list_sheet_detail:
                product_variant_batch = sheet_detail["product_variant_batch"]
                quantity_actual = sheet_detail["quantity_actual"]

                # Tìm số lượng tồn của lô - kho tại thời điểm hiện tại.
                warehouses_inventory = WarehouseInventory.objects.filter(
                    warehouse=sheet_warehouse, product_variant_batch=product_variant_batch
                ).first()
                if not warehouses_inventory:
                    raise ValidationError({"warehouses - product_variant_batch": "Không tìm thấy lô - kho tương ứng."})
                current_quantity_system = warehouses_inventory.quantity

                # Lưu thông tin chi tiết của phiếu
                new_sheet.warehouse_sheet_check_detail_sheet.create(
                    created_by=current_user, quantity_system=current_quantity_system, **sheet_detail
                )

                # Nếu phiếu được xác nhận
                if sheet_is_confirm:
                    # Tính số lượng chênh lệch tồn kho
                    quantity_change = int(quantity_actual) - int(current_quantity_system)

                    # Tạo một record lưu thông tin của phiếu trong bảng WarehouseInventoryLog
                    WarehouseInventoryLog.objects.create(
                        created_by=current_user,
                        product_variant_batch=product_variant_batch,
                        warehouse=sheet_warehouse,
                        quantity=quantity_change,
                        change_reason=sheet_change_reason,
                        type=sheet_type,
                        sheet_code=new_sheet.code,
                    )

    def perform_update(self, serializer, current_user=None):
        if current_user is None:
            current_user = self.request.user

        validated_data = serializer.validated_data

        validated_data["modified_by"] = current_user
        new_sheet_is_confirm = validated_data.get("is_confirm")

        with transaction.atomic():
            old_sheet = serializer.instance
            old_sheet_is_confirm = old_sheet.is_confirm

            if new_sheet_is_confirm is False and old_sheet_is_confirm is True:
                raise ValidationError({"is_confirm": "Không thể cập nhật trạng thái xác nhận từ True -> False."})

            # Nếu cập nhật trạng thái xác nhận của phiếu từ False sang True
            if old_sheet_is_confirm is False and new_sheet_is_confirm is True:
                old_list_sheet_detail = old_sheet.warehouse_sheet_check_detail_sheet.all()
                validated_data["confirm_date"] = timezone.now()
                validated_data["confirm_by"] = current_user

                for sheet_detail in old_list_sheet_detail:
                    old_sheet_quantity_actual = sheet_detail.quantity_actual
                    old_sheet_quantity_system = sheet_detail.quantity_system

                    # Tính số lượng chênh lệch tồn kho
                    quantity_change = int(old_sheet_quantity_actual) - int(old_sheet_quantity_system)

                    # Tạo một record lưu thông tin của phiếu trong bảng WarehouseInventoryLog
                    WarehouseInventoryLog.objects.create(
                        created_by=current_user,
                        product_variant_batch=sheet_detail.product_variant_batch,
                        warehouse=old_sheet.warehouse,
                        quantity=quantity_change,
                        change_reason=old_sheet.change_reason,
                        type=old_sheet.type,
                        sheet_code=old_sheet.code,
                    )

            serializer.save()


class WarehouseSheetTransferViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    permission_classes = [permissions.IsAuthenticated]
    queryset = (
        models.WarehouseSheetTransfer.objects.select_related(
            "warehouse_from",
            "warehouse_to",
            "change_reason",
        )
        .prefetch_related(
            "warehouse_sheet_transfer_detail_sheet__product_variant_batch__product_variant__images",
            "warehouse_sheet_transfer_detail_sheet__product_variant_batch__product_material",
        )
        .all()
    )
    default_serializer_class = warehouse_sheet_transfer.WarehouseSheetTransferReadOneSerializer

    serializer_classes = {
        "create": warehouse_sheet_transfer.WarehouseSheetTransferCreateSerializer,
        "partial_update": warehouse_sheet_transfer.WarehouseSheetTransferUpdateSerializer,
        "list": warehouse_sheet_transfer.WarehouseSheetTransferReadListSerializer,
        "retrieve": warehouse_sheet_transfer.WarehouseSheetTransferReadOneSerializer,
    }
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, django_filters.DjangoFilterBackend)
    search_fields = (
        "code",
        "note",
        "warehouse_sheet_transfer_detail_sheet__product_variant_batch__product_variant__SKU_code",
        "warehouse_sheet_transfer_detail_sheet__product_variant_batch__product_material__SKU_code",
        "warehouse_sheet_transfer_detail_sheet__product_variant_batch__name",
    )
    ordering_fields = "__all__"
    filterset_class = WarehouseSheetTransferFilterSet

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.default_serializer_class)

    def perform_create(self, serializer):
        current_user = self.request.user
        validated_data = serializer.validated_data
        sheet_type = SheetTransferType.TRANSFER
        validated_data["created_by"] = current_user
        validated_data["type"] = sheet_type

        sheet_is_confirm = validated_data["is_confirm"]
        sheet_warehouse_from = validated_data["warehouse_from"]
        sheet_warehouse_to = validated_data["warehouse_to"]
        sheet_change_reason = validated_data["change_reason"]

        list_sheet_detail = validated_data.pop("sheet_detail")

        with transaction.atomic():
            seq = SequenceIdentity.get_code_by_type(sheet_type)
            validated_data["code"] = seq.next_code()
            seq.value += 1
            seq.save()

            if sheet_is_confirm:
                validated_data["confirm_date"] = timezone.now()
                validated_data["confirm_by"] = current_user

            # Tạo phiếu check.
            new_sheet = serializer.save()

            for sheet_detail in list_sheet_detail:
                product_variant_batch = sheet_detail["product_variant_batch"]
                quantity = sheet_detail["quantity"]

                # Lưu thông tin chi tiết của phiếu
                new_sheet.warehouse_sheet_transfer_detail_sheet.create(created_by=current_user, **sheet_detail)

                # Nếu phiếu được xác nhận
                if sheet_is_confirm:
                    # Tạo 2 record lưu thông tin của phiếu trong bảng WarehouseInventoryLog
                    # Lưu record log trừ tồn của kho đi
                    WarehouseInventoryLog.objects.create(
                        created_by=current_user,
                        product_variant_batch=product_variant_batch,
                        warehouse=sheet_warehouse_from,
                        quantity=-quantity,
                        change_reason=sheet_change_reason,
                        type=sheet_type,
                        sheet_code=new_sheet.code,
                    )

                    # Lưu record log cộng tồn của kho đến
                    WarehouseInventoryLog.objects.create(
                        created_by=current_user,
                        product_variant_batch=product_variant_batch,
                        warehouse=sheet_warehouse_to,
                        quantity=quantity,
                        change_reason=sheet_change_reason,
                        type=sheet_type,
                        sheet_code=new_sheet.code,
                    )

    def perform_update(self, serializer, current_user=None):
        if current_user is None:
            current_user = self.request.user

        validated_data = serializer.validated_data

        validated_data["modified_by"] = current_user
        new_sheet_is_confirm = validated_data.get("is_confirm")

        with transaction.atomic():
            old_sheet = serializer.instance
            old_sheet_is_confirm = old_sheet.is_confirm

            if new_sheet_is_confirm is False and old_sheet_is_confirm is True:
                raise ValidationError({"is_confirm": "Không thể cập nhật trạng thái xác nhận từ True -> False."})

            # Nếu cập nhật trạng thái xác nhận của phiếu từ False sang True
            if old_sheet_is_confirm is False and new_sheet_is_confirm is True:
                old_list_sheet_detail = old_sheet.warehouse_sheet_transfer_detail_sheet.all()
                validated_data["confirm_date"] = timezone.now()
                validated_data["confirm_by"] = current_user

                for sheet_detail in old_list_sheet_detail:
                    old_sheet_product_variant_batch = sheet_detail.product_variant_batch
                    old_sheet_quantity = sheet_detail.quantity

                    # Tạo 2 record lưu thông tin của phiếu trong bảng WarehouseInventoryLog
                    # Lưu record log trừ tồn của kho đi
                    WarehouseInventoryLog.objects.create(
                        created_by=current_user,
                        product_variant_batch=old_sheet_product_variant_batch,
                        warehouse=old_sheet.warehouse_from,
                        quantity=-old_sheet_quantity,
                        change_reason=old_sheet.change_reason,
                        type=old_sheet.type,
                        sheet_code=old_sheet.code,
                    )

                    # Lưu record log cộng tồn của kho đến
                    WarehouseInventoryLog.objects.create(
                        created_by=current_user,
                        product_variant_batch=old_sheet_product_variant_batch,
                        warehouse=old_sheet.warehouse_to,
                        quantity=old_sheet_quantity,
                        change_reason=old_sheet.change_reason,
                        type=old_sheet.type,
                        sheet_code=old_sheet.code,
                    )

            serializer.save()


class WarehouseInventoryVariantListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = ProductsVariants.objects.prefetch_related(
        "batches",
        "batches__warehouse_inventory_product_variant_batch",
        "batches__warehouse_inventory_product_variant_batch__warehouse",
    ).filter(
        type=ProductVariantType.SIMPLE
    )  # Chỉ lấy các variant 'simple' vì chỉ variant loại này mới có tồn kho
    serializer_class = warehouse_inventory.WarehouseInventoryVariantSerializer
    filter_backends = (
        filters.OrderingFilter,
        filters.SearchFilter,
        django_filters.DjangoFilterBackend,
    )
    ordering_fields = "__all__"
    search_fields = ("name", "SKU_code", "bar_code", "batches__name")
    filterset_class = WarehouseInventoryVariantFilterSet

    def process_data(self, df=None):
        data = []
        df_main = pd.DataFrame(
            self.get_queryset().values(
                "id",
                "name",
                "SKU_code",
                "bar_code",
                "status",
                "neo_price",
                "sale_price",
                "batches",
                "batches__name",
                "batches__expire_date",
                "batches__warehouse_inventory_product_variant_batch",
                "batches__warehouse_inventory_product_variant_batch__warehouse",
                "batches__warehouse_inventory_product_variant_batch__warehouse__name",
                "batches__warehouse_inventory_product_variant_batch__quantity",
            )
        ).rename(
            columns={
                "batches": "batch_id",
                "batches__name": "batch_name",
                "batches__expire_date": "batch_expire_date",
                "batches__warehouse_inventory_product_variant_batch__warehouse": "warehouse_id",
                "batches__warehouse_inventory_product_variant_batch__warehouse__name": "warehouse_name",
                "batches__warehouse_inventory_product_variant_batch__quantity": "inventory",
            }
        )
        if not df_main.empty and df is not None:
            df_main["combine_batch_warehouse"] = df_main[
                ["batch_id", "batch_name", "batch_expire_date", "warehouse_id", "warehouse_name", "inventory"]
            ].apply(lambda x: "__$~~$__".join(x.astype(str)), axis=1)

            df_main = pd.merge(df, df_main, on="id", how="inner")
            df_main.fillna(0.00000, inplace=True)
            df_main["inventory"] = df_main["inventory"].apply(Decimal)

            grouped_df = df_main.groupby(["id", "name", "SKU_code", "bar_code", "status", "neo_price", "sale_price"], as_index=False).agg(
                batches=pd.NamedAgg(column="combine_batch_warehouse", aggfunc=list),
                total_inventory=pd.NamedAgg(column="inventory", aggfunc="sum"),
            )

            for item in grouped_df.to_dict("records"):
                batches_inventory = defaultdict(list)
                batches = []
                batches_total_inventory = {}
                for batch in item["batches"]:
                    (batch_id, batch_name, batch_expire_date, warehouse_id, warehouse_name, inventory) = batch.split("__$~~$__")

                    if batch_id != "None":
                        if warehouse_id == "None":
                            warehouse_id = None
                            warehouse_name = None
                            inventory = float(0)

                        inventory = float(inventory)
                        batch_expire_date = None if batch_expire_date == "None" else batch_expire_date
                        batches_total_inventory[batch_id] = batches_total_inventory.get(batch_id, float(0)) + inventory

                        if batch_id not in batches_inventory:
                            batches.append(
                                {
                                    "batch_id": batch_id,
                                    "batch_name": batch_name,
                                    "batch_expire_date": batch_expire_date,
                                }
                            )

                        batches_inventory[batch_id].append(
                            {
                                "warehouse_id": warehouse_id,
                                "warehouse_name": warehouse_name,
                                "inventory": inventory,
                            }
                        )
                for batch in batches:
                    inventories = batches_inventory.get(batch.get("batch_id"), [])

                    batch.update(
                        {"total_inventory": batches_total_inventory.get(batch.get("batch_id"), float(0)), "inventories": inventories}
                    )

                data.append(
                    {
                        "id": item["id"],
                        "name": item["name"],
                        "SKU_code": item["SKU_code"],
                        "bar_code": item["bar_code"],
                        "status": item["status"],
                        "sale_price": item["sale_price"],
                        "neo_price": item["neo_price"],
                        "total_inventory": item["total_inventory"],
                        "batches": batches,
                    }
                )

        return data

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset.values("id"))
        if page:
            data = self.process_data(pd.DataFrame(page))
            return self.get_paginated_response(data)

        data = self.process_data()
        return self.get_paginated_response(data)


class WarehouseSheetImportExportBulkUpdateView(ActivityLogMixin, generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = warehouse.WarehouseSheetBulkUpdateSerializer

    def post(self, request, *args, **kwargs):
        sheet_import_export_view_set = WarehouseSheetImportExportViewSet()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        current_user = self.request.user
        validated_data = serializer.validated_data

        with transaction.atomic():
            for sheet in validated_data["sheets"]:
                sheet_id = sheet["id"]
                old_sheet_import_export = WarehouseSheetImportExport.objects.filter(pk=sheet_id).first()

                if old_sheet_import_export is None:
                    raise ValidationError({"sheets": f"Không tìm thấy sheet: {sheet_id}"})

                sheet_import_export_update_serializer_class = sheet_import_export_view_set.serializer_classes.get("partial_update")
                sheet_import_export_update_serializer = sheet_import_export_update_serializer_class(
                    instance=old_sheet_import_export, data={"is_confirm": sheet["is_confirm"]}, partial=True
                )
                sheet_import_export_update_serializer.is_valid(raise_exception=True)
                sheet_import_export_view_set.perform_update(serializer=sheet_import_export_update_serializer, current_user=current_user)

        return Response(validated_data)


class WarehouseSheetCheckBulkUpdateView(ActivityLogMixin, generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = warehouse.WarehouseSheetBulkUpdateSerializer

    def post(self, request, *args, **kwargs):
        sheet_check_view_set = WarehouseSheetCheckViewSet()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        current_user = self.request.user
        validated_data = serializer.validated_data

        with transaction.atomic():
            for sheet in validated_data["sheets"]:
                sheet_id = sheet["id"]
                old_sheet_check = WarehouseSheetCheck.objects.filter(pk=sheet_id).first()

                if old_sheet_check is None:
                    raise ValidationError({"sheets": f"Không tìm thấy sheet: {sheet_id}"})

                sheet_check_update_serializer_class = sheet_check_view_set.serializer_classes.get("partial_update")
                sheet_check_update_serializer = sheet_check_update_serializer_class(
                    instance=old_sheet_check, data={"is_confirm": sheet["is_confirm"]}, partial=True
                )
                sheet_check_update_serializer.is_valid(raise_exception=True)
                sheet_check_view_set.perform_update(serializer=sheet_check_update_serializer, current_user=current_user)

        return Response(validated_data)


class WarehouseSheetTransferBulkUpdateView(ActivityLogMixin, generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = warehouse.WarehouseSheetBulkUpdateSerializer

    def post(self, request, *args, **kwargs):
        sheet_transfer_view_set = WarehouseSheetTransferViewSet()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        current_user = self.request.user
        validated_data = serializer.validated_data

        with transaction.atomic():
            for sheet in validated_data["sheets"]:
                sheet_id = sheet["id"]
                old_sheet_transfer = WarehouseSheetTransfer.objects.filter(pk=sheet_id).first()

                if old_sheet_transfer is None:
                    raise ValidationError({"sheets": f"Không tìm thấy sheet: {sheet_id}"})

                sheet_transfer_update_serializer_class = sheet_transfer_view_set.serializer_classes.get("partial_update")
                sheet_transfer_update_serializer = sheet_transfer_update_serializer_class(
                    instance=old_sheet_transfer, data={"is_confirm": sheet["is_confirm"]}, partial=True
                )
                sheet_transfer_update_serializer.is_valid(raise_exception=True)
                sheet_transfer_view_set.perform_update(serializer=sheet_transfer_update_serializer, current_user=current_user)

        return Response(validated_data)


class ReportWarehouseView(generics.ListAPIView):
    serializer_class = ReportWarehouseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, django_filters.DjangoFilterBackend)
    filterset_class = ProductWarehouseReportFilter
    queryset = None

    def list(self, request, *args, **kwargs):
        params = request.query_params
        date_from = params.get("date_from")
        date_to = params.get("date_to")
        warehouse_ids = params.getlist("warehouse_id")
        try:
            date_from = parser.parse(date_from).replace(tzinfo=pytz.utc) if date_from else None
            date_to = parser.parse(date_to).replace(tzinfo=pytz.utc) if date_to else None
        except Exception as err:
            return Response(data={"status": "failed", "msg": err.args[0]}, status=status.HTTP_400_BAD_REQUEST)
        report = ReportWarehouse(
            warehouse_ids=warehouse_ids, date_from=date_from, date_to=date_to, search=request.GET.get("search", None)
        ).reports()
        result = data_sortby(report, request.GET.get("ordering", None))

        page = self.paginate_queryset(result)
        result_page = process_images(page)
        result = self.serializer_class(result_page, many=True).data
        response = self.get_paginated_response(result)
        return response


class WarehouseInventoryAvailableHistoryAPIView(generics.ListAPIView):
    serializer_class = WarehouseInventoryAvailableHistorySerializer
    queryset = WarehouseInventoryAvailable.history.model.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = ["history_date"]

    def get_queryset(self):
        inventory_available_id = self.kwargs.get("id")
        return self.queryset.filter(id=inventory_available_id)

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        result = self.serializer_class(page, many=True).data
        for index, data in enumerate(result):
            if index < len(result) - 1:
                data["quantity_confirm_change"] = "{:.4f}".format(
                    float(data["quantity_confirm"]) - float(result[index + 1]["quantity_confirm"])
                )
                data["quantity_non_confirm_change"] = "{:.4f}".format(
                    float(data["quantity_non_confirm"]) - float(result[index + 1]["quantity_non_confirm"])
                )
            else:
                data["quantity_confirm_change"] = f"{0:.4f}"
                data["quantity_non_confirm_change"] = f"{0:.4f}"
        response = self.get_paginated_response(result)
        return response


class ReportWarehouseCategoryView(generics.ListAPIView):
    queryset = None
    serializer_class = PassSerializer
    filter_backends = [django_filters.DjangoFilterBackend]
    filterset_class = ReportWarehouseCategoryFilterset

    def get(self, request, *args, **kwargs):
        params = request.query_params
        warehouse_ids = params.getlist("warehouse_id")
        category_ids = params.getlist("category_id")
        date_from = params.get("date_from")
        date_to = params.get("date_to")
        
        data = get_report_category_inventory(warehouse_ids, category_ids, date_from, date_to)
        result = data_sortby(data, request.GET.get("ordering", None))

        page = self.paginate_queryset(result)
        return self.get_paginated_response(page)