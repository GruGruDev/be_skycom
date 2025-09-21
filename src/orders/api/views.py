# pylint: disable=C0302
from datetime import datetime

import django_filters.rest_framework as django_filters
import pandas as pd
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework import generics
from rest_framework import mixins
from rest_framework import parsers
from rest_framework import response
from rest_framework import serializers
from rest_framework import status
from rest_framework import views
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.views import Response

from core.pagination import ReportWithTotalValuePagination
from customers.api.views import update_customer_rank
from files.models import Images
from files.models import ImageTypes
from orders.api.filters import OrdersFilterset
from orders.api.filters import OrdersMobileFilterset
from orders.api.filters import OrdersReportByProductFilterset
from orders.api.filters import OrdersReportsFilterset
from orders.api.serializers import ConfirmationLogSerializer
from orders.api.serializers import OrderDetailReportSerializer
from orders.api.serializers import OrderItemDetailReportSerializer
from orders.api.serializers import OrderKPIReportSerializer
from orders.api.serializers import OrdersCancelReasonSerializer
from orders.api.serializers import OrdersTypeSerializer
from orders.api.serializers import OrdersCreateSerializer
from orders.api.serializers import OrderSheetConfirmSerializer
from orders.api.serializers import OrdersHistorySerializer
from orders.api.serializers import OrdersPaymentsAuditFileSerializer
from orders.api.serializers import OrdersPaymentsHistorySerializer
from orders.api.serializers import OrdersPaymentsUpdateSerializer
from orders.api.serializers import OrdersReadDetailSerializer
from orders.api.serializers import OrdersReadListMobileSerializer
from orders.api.serializers import OrdersReadListSerializer
from orders.api.serializers import OrdersReportPivotCompareParams
from orders.api.serializers import OrdersReportPivotCompareResponse
from orders.api.serializers import OrdersReportPivotParams
from orders.api.serializers import OrdersReportPivotResponse
from orders.api.serializers import OrdersSerializer
from orders.api.serializers import OrdersTagsSerializer
from orders.api.serializers import OrdersUpdateSerializer
from orders.enums import OrderPaymentType
from orders.enums import OrderStatus
from orders.enums import WarehouseSheetType
from orders.filters import ConfirmationLogFilter
from orders.models import ConfirmationSheetLog
from orders.models import Orders
from orders.models import OrdersCancelReason
from orders.models import OrdersType
from orders.models import OrdersItems
from orders.models import OrdersItemsCombo
from orders.models import OrdersItemsPromotion
from orders.models import OrdersPayments
from orders.models import OrdersPromotion
from orders.models import OrdersTag
from orders.models import OrderVariantsPromotion
from orders.report import order_detail
from orders.report.revenue import report
from orders.reports import OrdersReportPivot
from products.enums import ProductVariantType
from users.activity_log import ActivityLogMixin
from users.api.serializers import UserReadBaseInfoSerializer
from users.models import User
from utils.basic import data_sortby
from utils.enums import SequenceType
from utils.reports import PivotReportCompare
from utils.serializers import PassSerializer
from warehouses.models import SequenceIdentity
from warehouses.models import WarehouseInventoryLog
from warehouses.models import WarehouseInventoryReason
from warehouses.models import WarehouseSheetImportExport

# from utils.basic import data_sortby


class OrdersTagsViewset(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = OrdersTagsSerializer
    queryset = OrdersTag.objects.all()
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name",)
    ordering_fields = "__all__"

    @swagger_auto_schema(operation_summary="Danh sách thẻ đơn hàng")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Tạo mới thẻ đơn hàng")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class OrdersCancelReasonViewset(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = OrdersCancelReasonSerializer
    queryset = OrdersCancelReason.objects.all()
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name",)
    ordering_fields = "__all__"

    @swagger_auto_schema(operation_summary="Danh sách lý do huỷ đơn")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Tạo mới lý do huỷ đơn")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    

class OrdersTypeViewset(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = OrdersTypeSerializer
    queryset = OrdersType.objects.all()
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name",)
    ordering_fields = "__all__"

    @swagger_auto_schema(operation_summary="Danh sách loại đơn hàng")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Tạo mới loại đơn hàng")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class OrdersViewset(
    ActivityLogMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    http_method_names = ("get", "post", "patch")
    queryset = Orders.objects.all()
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, django_filters.DjangoFilterBackend)
    filterset_class = OrdersFilterset
    search_fields = (
        "order_key", "name_shipping", "phone_shipping", "tracking_number", 
        "customer__name", "customer__phones__phone", "sale_note", "delivery_note", 
        "address_shipping__address", "line_items__variant__name", "line_items__variant__SKU_code"
    )
    ordering_fields = "__all__"
    serializer_class = OrdersSerializer
    serializer_classes = {
        "create": OrdersCreateSerializer,
        "list": OrdersReadListSerializer,
        "retrieve": OrdersReadDetailSerializer,
        "update": OrdersUpdateSerializer,
        "partial_update": OrdersUpdateSerializer,
    }
    querysets = {
        "list": Orders.objects.select_related(
            "customer",
            "cancel_reason",
            "address_shipping",
            "address_shipping__ward",
            "address_shipping__ward__district",
            "address_shipping__ward__province",
            "source",
        )
        .prefetch_related("transportation_care","type", "tags", "payments", "customer__phones", "payments__images", "warehouse_sheet_import_export_order")
        .all(),
        "retrieve": Orders.objects.select_related(
            "customer",
            "address_shipping",
            "printed_by",
            "cancel_reason",
            "source",
        )
        .prefetch_related(
            "type",
            "tags",
            "payments",
            "payments__created_by",
            "payments__modified_by",
            "payments__images",
            "shipping",
            "shipping__sheet_export",
            "promotions_used",
            "promotions_used__promotion_order",
            "line_items",
            "line_items__variant",
            "line_items__variant__created_by",
            "line_items__variant__modified_by",
            "line_items__variant__tags",
            "line_items__variant__combo_variants",
            "line_items__variant__combo_variants__detail_variant",
            "line_items__variant_promotions_used",
            "line_items__variant_promotions_used__created_by",
            "line_items__variant_promotions_used__modified_by",
            "line_items__variant_promotions_used__promotion_variant",
            "line_items__variant_promotions_used__promotion_variant__created_by",
            "line_items__variant_promotions_used__promotion_variant__modified_by",
            "line_items__variant_promotions_used__promotion_variant__promotion_variant_other_variant",
            "line_items__variant_promotions_used__items_promotion",
            "line_items__items_combo",
            "line_items__items_combo__created_by",
            "line_items__items_combo__modified_by",
            "line_items__items_combo__variant__created_by",
            "line_items__items_combo__variant__modified_by",
            "warehouse_sheet_import_export_order",
        )
        .all(),
    }

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)

    def get_queryset(self):
        return self.querysets.get(self.action, self.queryset)

    @swagger_auto_schema(operation_summary="Danh sách đơn hàng")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Thông tin chi tiết đơn hàng")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.validated_data["modified_by"] = self.request.user
        return super().perform_update(serializer)

    @swagger_auto_schema(operation_summary="Cập nhật thông tin đơn hàng")
    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        previous_status = order.status

        super().partial_update(request, *args, **kwargs)

        order.refresh_from_db()
        new_status = order.status
        
        self.update_customer_order(previous_status, new_status, order.customer, order.price_total_order_actual)

        return response.Response(data=OrdersReadDetailSerializer(instance=order).data, status=status.HTTP_200_OK)

        # return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Tạo đơn hàng")
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid():
            serializer_data = serializer.data
            payments_data = serializer_data.pop("payments", [])
            order_promotion_data = serializer_data.pop("promotions", [])
            line_items_data = serializer_data.pop("line_items", [])
            order_data = serializer_data

            order_db = self.create_order(request, order_data)
            self.create_order_promotions(request, order_db, order_promotion_data)
            self.create_payments(request, order_db, payments_data)
            self.create_line_items(request, order_db, line_items_data)
            order_db.save()
            self.update_customer_order(None, order_db.status, order_db.customer, order_db.price_total_order_actual)

            return response.Response(data=OrdersReadDetailSerializer(instance=order_db).data, status=status.HTTP_201_CREATED)
        return response.Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create_order(self, request, order_data):
        """Tạo thông tin cơ bản của đơn hàng"""
        tags = order_data.pop("tags", [])
        order_data.update(
            {
                "customer_id": order_data.pop("customer"),
                "address_shipping_id": order_data.pop("address_shipping", None),
                "source_id": order_data.pop("source", None),
            }
        )
        order = Orders(created_by=request.user, **order_data)
        # generate sed code
        seq = SequenceIdentity.get_code_by_type(SequenceType.ORDER.value)
        order.order_key = seq.next_code()
        order.order_number = seq.value + 1
        seq.value += 1
        seq.save()
        order.tags.add(*tags)
        return order

    def update_customer_order(self, order_status_prev, order_status, customer, price_total_order_actual):
        if order_status_prev != OrderStatus.COMPLETED and order_status == OrderStatus.COMPLETED:
            customer = customer
            customer.total_spent += price_total_order_actual
            customer.total_order += 1
            customer.last_order_time = timezone.now()
            customer.save()
            update_customer_rank(customer)
        elif order_status_prev == OrderStatus.COMPLETED and order_status != OrderStatus.COMPLETED:
            customer = customer
            customer.total_spent -= price_total_order_actual
            customer.total_order -= 1
            customer.save()
            update_customer_rank(customer)
        pass

    def create_order_promotions(self, request, order: Orders, order_promotions):
        """Áp các khuyến mãi của đơn hàng"""
        order_promotions_db = []
        for order_promotion in order_promotions:
            order_promotions_db.append(OrdersPromotion.objects.create(created_by=request.user, order=order, **order_promotion))
        return order_promotions_db

    def create_payments(self, request, order: Orders, payments):
        """Tạo các phiếu thanh toán"""
        payments_db = []
        for payment in payments:
            payments_db.append(OrdersPayments.objects.create(created_by=request.user, order=order, **payment))
        return payments_db

    def create_line_items(self, request, order: Orders, line_items):
        """Tạo các items của đơn hàng"""
        line_items_db = []
        for item in line_items:
            promotions = item.pop("promotions", [])
            items_combo = item.pop("items_combo", [])
            line_item = OrdersItems.objects.create(created_by=request.user, order=order, **item)

            self.create_line_item_promotions(request, line_item, promotions)

            if line_item.variant.type in [ProductVariantType.BUNDLE.value, ProductVariantType.COMBO.value]:
                self.create_items_combo(request, line_item, items_combo)

            line_items_db.append(line_item)
        return line_items

    def create_items_combo(self, request, line_item: OrdersItems, items_combo):
        """Tạo các sản phẩm đính kèm nếu line item là combo hoặc bundle"""
        items_combo_db = []
        if line_item.variant.type not in [ProductVariantType.SIMPLE]:
            for item_combo in items_combo:
                item_combo_db = OrdersItemsCombo.objects.create(created_by=request.user, line_item=line_item, **item_combo)
                items_combo_db.append(item_combo_db)
        return items_combo_db

    def create_line_item_promotions(self, request, line_item: OrdersItems, promotions):
        """Áp khuyến mãi cho từng line item"""
        line_item_promotions_db = []
        for promotion in promotions:
            items_promotion = promotion.pop("items_promotion", [])
            line_item_promotion = OrderVariantsPromotion.objects.create(created_by=request.user, line_item=line_item, **promotion)
            self.create_variant_item_promotions(request, line_item_promotion, items_promotion)

        return line_item_promotions_db

    def create_variant_item_promotions(self, request, order_variant_promotion: OrderVariantsPromotion, items_promotion):
        """Tạo thông tin quà tặng nếu khuyến mãi được áp dụng cho line item là khuyến mãi tặng kèm sản phẩm"""
        variant_items_promotion = []
        for item in items_promotion:
            item_promotion = OrdersItemsPromotion.objects.create(
                created_by=request.user, order_variant_promotion=order_variant_promotion, **item
            )
            variant_items_promotion.append(item_promotion)
        return variant_items_promotion


class OrdersMobileViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    http_method_names = ("get",)
    queryset = Orders.objects.prefetch_related("line_items", "line_items__variant", "line_items__variant__images").all()
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, django_filters.DjangoFilterBackend)
    filterset_class = OrdersMobileFilterset
    search_fields = ("order_key", "name_shipping", "phone_shipping")
    ordering_fields = "__all__"
    serializer_class = OrdersReadListMobileSerializer


class OrderHistoryList(viewsets.generics.ListAPIView):
    serializer_class = OrdersHistorySerializer
    queryset = Orders.history.model.objects.all().select_related(
        "created_by", "modified_by", "printed_by", "source", "cancel_reason", "address_shipping"
    )

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Orders.objects.none()
        return self.queryset.filter(id=self.kwargs[self.lookup_field])

    @swagger_auto_schema(operation_summary="Lịch sử đơn hàng")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class OrdersPivotReportAPIView(viewsets.generics.ListAPIView):
    http_method_names = ("get",)
    queryset = Orders.objects.all()
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = OrdersReportsFilterset
    serializer_class = OrdersReportPivotResponse
    pagination_class = None

    @swagger_auto_schema(operation_summary="Báo cáo tổng hợp đơn hàng", query_serializer=OrdersReportPivotParams)
    def get(self, request, *args, **kwargs):
        params = OrdersReportPivotParams(data=request.query_params)
        params.is_valid(raise_exception=True)
        queryset = self.filter_queryset(self.get_queryset())
        try:
            pivot_table = OrdersReportPivot(queryset=queryset, **params.validated_data)
        except (ValueError, Exception) as err:
            raise serializers.ValidationError(str(err))
        return response.Response(data={"count": len(pivot_table.result), "results": pivot_table.result})


class OrdersPivotReportCompareAPIView(views.APIView):
    http_method_names = ("get",)

    @swagger_auto_schema(
        operation_summary="So sánh báo cáo tổng hợp đơn hàng",
        query_serializer=OrdersReportPivotCompareParams,
        responses={200: OrdersReportPivotCompareResponse},
    )
    def get(self, request, *args, **kwargs):
        srl = OrdersReportPivotCompareParams(data=request.query_params)
        srl.is_valid(raise_exception=True)
        srl_data = srl.validated_data
        first_pivot_report = OrdersReportPivot(
            queryset=Orders.objects.filter(created__date__gte=srl_data.get("created_from"), created__date__lte=srl_data.get("created_to")),
            **srl_data,
        )
        second_pivot_report = OrdersReportPivot(
            queryset=Orders.objects.filter(
                created__date__gte=srl_data.get("created_from_cp"), created__date__lte=srl_data.get("created_to_cp")
            ),
            **srl_data,
        )
        compare_inst = PivotReportCompare(
            first_created_date=[srl_data.get("created_from"), srl_data.get("created_to")],
            second_created_date=[srl_data.get("created_from_cp"), srl_data.get("created_to_cp")],
            first_inst=first_pivot_report,
            second_inst=second_pivot_report,
            dimensions=first_pivot_report._get_dimension_names(),
        )
        compare_result = compare_inst.map_compare()
        return response.Response(data={"count": len(compare_result), "results": compare_result})


class OrdersPaymentsViewset(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    http_method_names = ["patch"]
    serializer_class = OrdersPaymentsUpdateSerializer
    queryset = OrdersPayments.objects.all()

    @swagger_auto_schema(operation_summary="Cập nhật thông tin thanh toán")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class OrdersPaymentsHistoryListView(viewsets.generics.ListAPIView):
    serializer_class = OrdersPaymentsHistorySerializer
    queryset = OrdersPayments.history.model.objects.all().select_related(
        "modified_by",
    )

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return OrdersPayments.objects.none()
        return self.queryset.filter(id=self.kwargs[self.lookup_field])

    @swagger_auto_schema(operation_summary="Lịch sử thanh toán")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PaymentsAuditUploadView(views.APIView):
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)

    @swagger_auto_schema(
        operation_summary="Upload file đối soát thanh toán",
        request_body=OrdersPaymentsAuditFileSerializer,
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "status": openapi.Schema(type=openapi.TYPE_STRING, default="success"),
                    "msg": openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "status": openapi.Schema(type=openapi.TYPE_STRING, default="failed"),
                    "msg": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), title="Error detail"),
                },
            ),
        },
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        datetime_now = datetime.now().isoformat()
        serialzier = OrdersPaymentsAuditFileSerializer(data=request.data)
        serialzier.is_valid(raise_exception=True)

        image = serialzier.validated_data.get("image")
        image_data = ContentFile(image.file.read())

        df = pd.read_excel(serialzier.validated_data["file"])
        df_tuples = list(df.itertuples(index=True, name=None))
        payments = []
        last_row = None
        try:
            for (row, order_key, amount_received, time_received, transporter, method) in df_tuples:  # pylint: disable=W0612
                row = row + 1
                if not all([order_key, amount_received, time_received, method]):
                    raise serializers.ValidationError(f"row {row}: missing fields")
                if method not in OrderPaymentType.list():
                    raise serializers.ValidationError(f"row {row}: method invalid")
                order = Orders.objects.filter(order_key=order_key).first()
                if not order:
                    raise serializers.ValidationError(f"row {row}: order does not exist")
                payment = order.payments.filter(type=method, is_confirm=False).first()
                if not payment:
                    raise serializers.ValidationError(f"row {row}: payment does not exist or that have confirmed")
                payment.modified_by = request.user
                payment.price_from_upload_file = amount_received
                payment.date_from_upload_file = time_received

                if payment.price_from_upload_file == payment.price_from_order:
                    payment.is_confirm = True
                    payment.date_confirm = datetime_now
                payments.append(payment)
                last_row = row
        except (serializers.ValidationError) as err:
            return response.Response(data={"status": "failed", "msg": err.detail}, status=400)
        OrdersPayments.objects.bulk_update(
            payments,
            fields=["modified_by", "price_from_upload_file", "date_from_upload_file", "is_confirm", "date_confirm"],
            batch_size=2000,
        )
        if serialzier.validated_data.get("image") and payments:
            for payment in payments:
                img_obj = Images(type=ImageTypes.PAYMENT, upload_by=request.user)
                img_obj.image.save(image.name, image_data)
                payment.images.add(img_obj)
        return response.Response(data={"status": "success", "msg": f"Updated {last_row} payments"}, status=200)


class OrderItemDetailReportListView(generics.GenericAPIView):
    serializer_class = OrderItemDetailReportSerializer
    filterset_class = OrdersFilterset
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    ]
    search_fields = ["order_key", "customer_phone", "ecommerce_code"]
    ordering_fields = [
        "created",
        "modified",
        "price_total_order_actual",
        "price_total_variant_actual",
        "price_total_variant_actual_input",
        "order_key",
    ]
    queryset = Orders.objects.all()

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = order_detail.list_order_item(queryset, **self.request.query_params)
        page = self.paginate_queryset(data)
        return self.get_paginated_response(page)


class OrderDetailReportListView(generics.GenericAPIView):
    serializer_class = OrderDetailReportSerializer
    filterset_class = OrdersFilterset
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    ]
    search_fields = ["order_key", "customer_phone"]
    ordering_fields = [
        "created",
        "modified",
        "price_total_order_actual",
        "price_total_variant_actual",
        "price_total_variant_actual_input",
        "order_key",
    ]
    queryset = Orders.objects.all()

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = order_detail.list_order(queryset, **self.request.query_params)
        page = self.paginate_queryset(data)
        return self.get_paginated_response(page)


class OrderKPIReportListView(generics.ListAPIView):
    filterset_class = OrdersFilterset
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    ]
    search_fields = ["order_key", "customer_phone", "ecommerce_code"]
    ordering_fields = ["created", "modified", "total_actual", "total_variant_actual", "appointment_date", "order_key"]
    queryset = Orders.objects.select_related("created_by", "shipping", "source").prefetch_related("tags").all()
    serializer_class = OrderKPIReportSerializer


class ConfirmationLogTurnRetrieveView(generics.RetrieveAPIView):
    serializer_class = PassSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic()
    def get(self, request, *args, **kwargs):
        with transaction.atomic():
            seq = SequenceIdentity.get_code_by_type(SequenceType.TURN.value)
            seq.value += 1
            seq.save()

        return Response({"turn": seq.value})


class OrderSheetConfirmAPIView(ActivityLogMixin, APIView):
    def create_confirm_sheet_log(
        self,
        turn: int,
        scan_by: User,
        order_key: str,
        is_success: bool,
        msg: str,
        type: str,
        order_number: int | None = None,
    ):
        ConfirmationSheetLog(
            turn_number=turn,
            scan_by=scan_by,
            order_number=order_number,
            order_key=order_key,
            is_success=is_success,
            log_message=msg,
            type=type,
        ).save()

    def get_object_from_key(self, turn: int, scan_by: User, order_key: str, sheet_type: str):
        try:
            return Orders.objects.prefetch_related("warehouse_sheet_import_export_order", "shipping").get(order_key=order_key)
        except (Orders.DoesNotExist, ValidationError):
            msg = "Không thể tìm thấy đơn hàng trong hệ thống."
            self.create_confirm_sheet_log(
                turn=turn,
                scan_by=scan_by,
                order_key=order_key,
                is_success=False,
                msg=msg,
                type=sheet_type,
            )
            raise ValidationError(msg)  # pylint: disable=W0707

    @swagger_auto_schema(request_body=OrderSheetConfirmSerializer, responses={201: "success"})
    # pylint: disable=R0912, R0915
    def post(self, request, *args, **kwargs):
        serializer = OrderSheetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_key = request.data["order_key"]
        sheet_type = request.data["sheet_type"]
        turn = request.data["turn"]
        scan_by = request.user
        obj = self.get_object_from_key(turn=turn, scan_by=scan_by, order_key=order_key, sheet_type=sheet_type)
        order_number = obj.order_number

        try:
            obj.shipping
        except Exception:
            msg = "Không thể cập nhật phiếu của đơn hàng chưa có vận chuyển."
            self.create_confirm_sheet_log(
                turn=turn,
                scan_by=scan_by,
                order_key=order_key,
                order_number=order_number,
                is_success=False,
                msg=msg,
                type=sheet_type,
            )
            raise ValidationError(msg)  # pylint: disable=W0707

        export_sheet = None
        import_sheet = None
        sheets = obj.warehouse_sheet_import_export_order.all()
        if sheets:
            for sheet in sheets:
                if sheet.type == WarehouseSheetType.Export.value:
                    export_sheet = sheet
                if sheet.type == WarehouseSheetType.Import.value:
                    import_sheet = sheet

        for sheet in sheets:
            if sheet.is_delete:
                msg = "Không thể xác nhận phiếu xuất của đơn hàng Đã huỷ"
                self.create_confirm_sheet_log(
                    turn=turn,
                    scan_by=scan_by,
                    order_key=order_key,
                    order_number=order_number,
                    is_success=False,
                    msg=msg,
                    type=sheet_type,
                )
                raise ValidationError(msg)

        if sheet_type == WarehouseSheetType.Export.value:
            if not export_sheet:
                msg = "Không thể xác nhận phiếu xuất chưa tồn tại. Vui lòng tạo phiếu xuất."
                self.create_confirm_sheet_log(
                    turn=turn,
                    scan_by=scan_by,
                    order_key=order_key,
                    order_number=order_number,
                    is_success=False,
                    msg=msg,
                    type=sheet_type,
                )
                raise ValidationError(msg)
            if export_sheet.is_confirm:
                msg = f"Phiếu xuất kho của đơn {order_key} đã được xác nhận."
                self.create_confirm_sheet_log(
                    turn=turn,
                    scan_by=scan_by,
                    order_key=order_key,
                    order_number=order_number,
                    is_success=False,
                    msg=msg,
                    type=sheet_type,
                )
                raise ValidationError(msg)
            _export_sheet = WarehouseSheetImportExport.objects.filter(pk=export_sheet.pk).first()
            if _export_sheet and not _export_sheet.is_confirm:
                _export_sheet.is_confirm = True
                _export_sheet.confirmed_by = request.user
                _export_sheet.confirmed_date = timezone.now()
                _export_sheet.save()

                msg = "Xuất hàng thành công."

                for sheet_detail in _export_sheet.warehouse_sheet_import_export_detail_sheet.all():
                    WarehouseInventoryLog.objects.create(
                        created_by=scan_by,
                        product_variant_batch=sheet_detail.product_variant_batch,
                        warehouse=_export_sheet.warehouse,
                        quantity=sheet_detail.quantity,
                        change_reason=_export_sheet.change_reason,
                        type=_export_sheet.type,
                        sheet_code=_export_sheet.code,
                    )

                self.create_confirm_sheet_log(
                    turn=turn,
                    scan_by=scan_by,
                    order_key=order_key,
                    order_number=order_number,
                    is_success=True,
                    msg=msg,
                    type=sheet_type,
                )

        if sheet_type == WarehouseSheetType.Import.value:
            if export_sheet and export_sheet.is_confirm:
                if not import_sheet:
                    with transaction.atomic():
                        seq = SequenceIdentity.get_code_by_type("IP")
                        code = seq.next_code()
                        seq.value += 1
                        seq.save()
                    try:
                        reason = WarehouseInventoryReason.objects.get(name="(System) Returned", type="IP")
                    except Exception:
                        reason = WarehouseInventoryReason.objects.create(name="(System) Returned", type="IP")
                    sheet_created = WarehouseSheetImportExport.objects.create(
                        type="IP",
                        is_confirm=True,
                        warehouse=export_sheet.warehouse,
                        change_reason=reason,
                        order=obj,
                        created_by=scan_by,
                        code=code,
                        confirm_by=scan_by,
                        confirm_date=timezone.now(),
                        modified_by=scan_by,
                    )

                    for sheet_detail in export_sheet.warehouse_sheet_import_export_detail_sheet.all():
                        WarehouseInventoryLog.objects.create(
                            created_by=scan_by,
                            product_variant_batch=sheet_detail.product_variant_batch,
                            warehouse=sheet_created.warehouse,
                            quantity=sheet_detail.quantity * -1,
                            change_reason=sheet_created.change_reason,
                            type=sheet_created.type,
                            sheet_code=sheet_created.code,
                        )
                        sheet_created.warehouse_sheet_import_export_detail_sheet.create(
                            created_by=scan_by,
                            quantity=sheet_detail.quantity * -1,
                            product_variant_batch=sheet_detail.product_variant_batch,
                        )

                    msg = "Nhập hàng thành công."

                    self.create_confirm_sheet_log(
                        turn=turn,
                        scan_by=scan_by,
                        order_key=order_key,
                        order_number=order_number,
                        is_success=True,
                        msg=msg,
                        type=sheet_type,
                    )
                elif import_sheet.is_confirm:
                    msg = f"Phiếu nhập hoàn của đơn {order_key} đã được tạo và xác nhận."
                    self.create_confirm_sheet_log(
                        turn=turn,
                        scan_by=scan_by,
                        order_key=order_key,
                        order_number=order_number,
                        is_success=False,
                        msg=msg,
                        type=sheet_type,
                    )
                    raise ValidationError(msg)
                elif not import_sheet.is_confirm:
                    _import_sheet = WarehouseSheetImportExport.objects.filter(pk=import_sheet.pk).first()
                    if _import_sheet and not _import_sheet.is_confirm:
                        _import_sheet.is_confirm = True
                        _import_sheet.confirmed_by = request.user
                        _import_sheet.confirmed_date = timezone.now()
                        _import_sheet.save()

                        msg = "Nhập hàng thành công."
                        self.create_confirm_sheet_log(
                            turn=turn,
                            scan_by=scan_by,
                            order_key=order_key,
                            order_number=order_number,
                            is_success=True,
                            msg=msg,
                            type=sheet_type,
                        )
            else:
                msg = "Không thể nhập hoàn đơn hàng chưa xuất kho."
                self.create_confirm_sheet_log(
                    turn=turn,
                    scan_by=scan_by,
                    order_key=order_key,
                    order_number=order_number,
                    is_success=False,
                    msg=msg,
                    type=sheet_type,
                )
                raise ValidationError(msg)

        return Response(serializer.data)


class TurnListView(generics.ListAPIView):
    serializer_class = PassSerializer
    queryset = ConfirmationSheetLog.objects.all()
    permission_classes = [IsAuthenticated]

    filter_backends = [
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
    ]
    ordering_fields = ["turn_number"]
    filterset_class = ConfirmationLogFilter
    search_fields = ["turn_number", "scan_by__name"]

    def get(self, request, *args, **kwargs):
        limit = request.GET.get("limit")
        if not limit:
            limit = 30
        page = request.GET.get("page")
        if page:
            start = (int(page) - 1) * int(limit) - 1 if page == 1 else (int(page) - 1) * int(limit)
            end = int(page) * int(limit)
        else:
            start = 0
            end = int(limit)
        data = (
            self.filter_queryset(self.get_queryset())
            .values("turn_number", "scan_by", "type")
            .order_by("-turn_number")
            .prefetch_related("scan_by")
            .annotate(count=Count("turn_number"))
        )
        for obj in data:
            obj["scan_by"] = UserReadBaseInfoSerializer(User.objects.get(pk=obj["scan_by"])).data
            try:
                log = ConfirmationSheetLog.objects.filter(turn_number=obj["turn_number"]).all()
            except Exception:
                log = None
            if log:
                obj["scan_at"] = log[0].scan_at
            else:
                obj["scan_at"] = None

        res = {
            "count": len(data),
            "results": data[start:end],
        }

        return Response(res)


class ConfirmationLogListView(generics.ListAPIView):
    serializer_class = ConfirmationLogSerializer
    queryset = ConfirmationSheetLog.objects.all()
    permission_classes = [IsAuthenticated]

    filter_backends = [
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
    ]
    ordering_fields = ["turn_number", "scan_at", "order_number", "order_key"]
    filterset_class = ConfirmationLogFilter
    search_fields = ["turn_number", "order_key"]


class OrderRevenueReportDashboardView(generics.GenericAPIView):
    queryset = Orders.objects.select_related("shipping", "customer").filter(status=OrderStatus.COMPLETED).exclude(complete_time=None)
    serializer_class = PassSerializer
    filter_backends = [django_filters.DjangoFilterBackend]
    filterset_class = OrdersReportsFilterset
    pagination_class = ReportWithTotalValuePagination

    def get(self, request, *args, **kwargs):
        filterset = self.filterset_class(request.query_params, queryset=self.queryset)
        queryset = self.filter_queryset(self.queryset)
        date_from = filterset.form.data.get("complete_time_from")
        date_to = filterset.form.data.get("complete_time_to")

        data, total = report.get_dashboard(queryset, date_from, date_to)

        page = self.paginate_queryset(data), total
        return self.get_paginated_response(page)


class OrderRevenueRatioView(generics.GenericAPIView):
    queryset = Orders.objects.filter(status=OrderStatus.COMPLETED)
    serializer_class = PassSerializer
    filter_backends = [django_filters.DjangoFilterBackend]
    filterset_class = OrdersReportsFilterset

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.queryset)

        data = report.get_ratio_order_pre_and_current_month(queryset)

        return Response(data={"data": data}, status=status.HTTP_200_OK)


class OrderRevenueByProductReportView(generics.GenericAPIView):
    queryset = Orders.objects.prefetch_related(
        "line_items",
        "line_items__variant",
        "address_shipping__ward__district__province",
        "line_items__variant__product",
        "line_items__variant__images",
    ).filter(status=OrderStatus.COMPLETED).exclude(complete_time=None)
    serializer_class = PassSerializer
    filter_backends = [django_filters.DjangoFilterBackend]
    filterset_class = OrdersReportByProductFilterset
    pagination_class = ReportWithTotalValuePagination

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.queryset)
        data, total = report.get_revenue_by_product_variant(queryset)

        result = data_sortby(data, request.GET.get("ordering", None))
        page = self.paginate_queryset(result), total
        return self.get_paginated_response(page)


class OrderRevenueBySaleReportView(generics.GenericAPIView):
    queryset = Orders.objects.select_related("customer", "customer__customer_care_staff", "modified_by", "source").filter(
        status=OrderStatus.COMPLETED
    ).exclude(complete_time=None)
    serializer_class = PassSerializer
    filter_backends = [django_filters.DjangoFilterBackend]
    filterset_class = OrdersReportsFilterset
    pagination_class = ReportWithTotalValuePagination

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.queryset)
        data, total = report.get_revenue_by_sale(queryset)

        result = data_sortby(data, request.GET.get("ordering", None))
        page = self.paginate_queryset(result), total
        return self.get_paginated_response(page)

