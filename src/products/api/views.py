import time
from io import BytesIO
import traceback

import django_filters.rest_framework as django_filters
import pandas as pd
from django.db import transaction
from django.db.models import Count
from django.db.models import F
from django.db.models import Q
from django.db.models import Prefetch
from django.db.models import Sum
from django.db.models import IntegerField
from django.db.models import Value
from django.db.models import Subquery
from django.db.models import OuterRef
from django.db.models import Case
from django.db.models import When
from django.db.models import FloatField
from django.db.models.functions import Coalesce
from django.http import FileResponse
from drf_yasg.utils import swagger_auto_schema
from openpyxl import Workbook
from openpyxl.styles import Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from rest_framework import decorators
from rest_framework import filters
from rest_framework import generics
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.views import CustomModelViewSet
from orders.enums import OrderStatus
from orders.enums import WarehouseSheetType
from orders.models import OrdersItems
from products.api.filters import ProductCategoryFilterset
from products.api.filters import ProductFilterset
from products.api.filters import ProductMaterialFilterset
from products.api.filters import ProductReportsFilterset
from products.api.filters import ProductVariantBatchFilterset
from products.api.filters import ProductVariantFilterset
from products.api.filters import ProductVariantMaterialFilterset
from products.api.filters import ProductVariantRevenueFilterset
from products.api.serializers import BulkUpdateProductVariantSerializer, CategorySerializer
from products.api.serializers import ImportProductVariantSerializer
from products.api.serializers import ProductCreateSerializer
from products.api.serializers import ProductCreateWtVariantSerializer
from products.api.serializers import ProductListSerializer
from products.api.serializers import ProductMaterialSerializer
from products.api.serializers import ProductMaterialVariantSerializer
from products.api.serializers import ProductReportPivotParams
from products.api.serializers import ProductReportPivotResponse
from products.api.serializers import ProductRetrieveSerializer
from products.api.serializers import ProductSerializer
from products.api.serializers import ProductVariantBatchCreateSerializer
from products.api.serializers import ProductVariantBatchSerializer
from products.api.serializers import ProductVariantBatchUpdateSerializer
from products.api.serializers import ProductVariantBulkCreateSerializer
from products.api.serializers import ProductVariantCreateSingleSerializer
from products.api.serializers import ProductVariantMappingSerializer
from products.api.serializers import ProductVariantRetrieveSerializer
from products.api.serializers import ProductVariantsSerializer
from products.api.serializers import ProductVariantUpdateSerializer
from products.api.serializers import SupplierPatchUpdateSerializer
from products.api.serializers import SupplierSerializer
from products.api.serializers import TagSerializer
from products.api.serializers import ProductVariantRevenueSerializer
from products.enums import ProductVariantType
from products.models import ProductCategory
from products.models import Products
from products.models import ProductsMaterials
from products.models import ProductSupplier
from products.models import ProductsVariants
from products.models import ProductsVariantsBatches
from products.models import ProductsVariantsComboDetail
from products.models import ProductsVariantsMapping
from products.models import ProductsVariantsMaterials
from products.models import ProductTag
from products.reports import ProductReportPivot
from users.activity_log import ActivityLogMixin
from warehouses.api.serializers.warehouse_sheet_import_export import WarehouseSheetImportExportCreateSerializer
from warehouses.api.views import WarehouseSheetImportExportViewSet
from warehouses.models import Warehouse
from warehouses.models import WarehouseInventory


class CategoryViewset(
    ActivityLogMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)
    serializer_class = CategorySerializer

    queryset = (
        ProductCategory.objects.annotate(
            total_products=Count("products", distinct=True),
            total_inventory=Coalesce(
                Sum(
                    F(
                        "products__variants__batches__warehouse_inventory_product_variant_batch__quantity"
                    )
                ),
                Value(0),
                output_field=FloatField(),
            ),
        )
        .order_by("-total_inventory")
        .values()
    )

    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    )
    filterset_class = ProductCategoryFilterset

    search_fields = ("name",)
    ordering_fields = "__all__"

    @swagger_auto_schema(operation_summary="Danh sách Category")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Tạo mới Category")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class TagViewset(
    mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    permission_classes = (IsAuthenticated,)
    serializer_class = TagSerializer
    queryset = ProductTag.objects.all()
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = ("tag",)
    ordering_fields = "__all__"

    @swagger_auto_schema(operation_summary="Danh sách Tags")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Tạo mới Tag")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class ProductSupplierViewset(
    ActivityLogMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    http_method_names = ("get", "post", "patch")
    serializer_classes = {
        "partial_update": SupplierPatchUpdateSerializer,
    }
    serializer_class = SupplierSerializer
    queryset = ProductSupplier.objects.all()
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    )
    search_fields = ("name", "business_code", "tax_number")
    ordering_fields = "__all__"

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)

    @swagger_auto_schema(operation_summary="Danh sách Supplier")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Tạo mới Supplier")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Cập nhật một phần thông tin Supplier")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class ProductVariantMappingViewset(
    ActivityLogMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    http_method_names = ("get", "post", "patch")
    serializer_class = ProductVariantMappingSerializer
    queryset = ProductsVariantsMapping.objects.all()

    @swagger_auto_schema(operation_summary="Danh sách sản phẩm mapping")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Tạo mới sản phẩm mapping")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Cập nhật thông tin một phần sản phẩm mapping"
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class ProductViewset(
    ActivityLogMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    http_method_names = ("get", "post", "patch")
    serializer_class = ProductSerializer
    serializer_classes = {
        "create": ProductCreateSerializer,
        "list": ProductListSerializer,
        "retrieve": ProductRetrieveSerializer,
        "bulk_create": ProductCreateWtVariantSerializer,
    }
    queryset = (
        Products.objects.prefetch_related(
            "images",
            "variants",
            # "variants__tags",
            "variants__images",
            "variants__batches",
            "variants__batches__warehouse_inventory_product_variant_batch",
            "variants__materials",
        )
        .annotate(
            total_variants=Count("variants__id", distinct=True),
            total_inventory=Coalesce(
                Sum(
                    "variants__batches__warehouse_inventory_product_variant_batch__quantity"
                ),
                Value(0),
                output_field=FloatField(),
            ),
        )
        .all()
    )
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    )
    filterset_class = ProductFilterset
    search_fields = ("name", "SKU_code", "note")
    ordering_fields = "__all__"

    def get_serializer(self, *args, **kwargs):
        if self.action == "bulk_create":
            kwargs.update({"many": True})
        return super().get_serializer(*args, **kwargs)

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)

    @swagger_auto_schema(operation_summary="Danh sách sản phẩm")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Chi tiết thông tin sản phẩm")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def create_product(self, request, serializer_data) -> Products:
        serializer_data.update(
            {
                "created_by": request.user,
                "category_id": serializer_data.pop("category", None),
                "supplier_id": serializer_data.pop("supplier", None),
            }
        )
        variants = serializer_data.pop("variants", [])
        # Create product
        product_model = Products.objects.create(**serializer_data)
        # Create product variants
        for variant in variants:
            combo_variants = variant.pop("combo_variants", [])
            tags = variant.pop("tags", [])
            variant.update({"created_by": request.user, "product": product_model})
            variant_model = ProductsVariants.objects.create(**variant)
            variant_model.tags.add(*tags)
            # Create combo or bundle
            if combo_variants and variant_model.type != ProductVariantType.SIMPLE.value:
                for variant_detail in combo_variants:
                    variant_detail.update({"origin_variant": variant_model})
                    ProductsVariantsComboDetail.objects.create(**variant_detail)
        return product_model

    @swagger_auto_schema(
        operation_summary="Tạo sản phẩm, biến thể sản phẩm, combo hoặc bundle",
        operation_description="""
        **API cho phép tạo sản phẩm, tạo các biến thể và thông tin các biến thể combo hoặc bundle**

        *Lưu ý khi sử dụng API để tạo các biến thể combo và bundle*
        - Loại biến thể phải là `combo` hoặc `bundle`
        - Sản phẩm biến thể bên trong phải thuộc loại sản phẩm `simple`
        - Số lượng sản phẩm biến thể bên trong phải `>=2`
        - Tổng giá của items combo/bundle (số lượng biến thể * giá của biến thể bên trong combo, bundle) phải `=` \
            Giá được khai báo bên ngoài(`sale_price`)
        """,
    )
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid():
            serializer_data = serializer.data
            product = self.create_product(request, serializer_data)
            return Response(
                data=ProductRetrieveSerializer(instance=product).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_summary="Tạo nhiều sản phẩm")
    @transaction.atomic
    @decorators.action(
        methods=["post"],
        detail=False,
        url_path="bulk-create",
        url_name="Bulk create products, product variants",
    )
    def bulk_create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.validated_data["modified_by"] = self.request.user

        return super().perform_update(serializer)

    @swagger_auto_schema(operation_summary="Cập nhật một phần thông tin sản phẩm")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class ProductVariantViewset(CustomModelViewSet):
    http_method_names = ("get", "post", "patch", "delete")
    serializer_class = ProductVariantsSerializer
    serializer_classes = {
        "list": ProductVariantRetrieveSerializer,
        "create": ProductVariantCreateSingleSerializer,
        "retrieve": ProductVariantRetrieveSerializer,
        "partial_update": ProductVariantUpdateSerializer,
        "bulk_create": ProductVariantBulkCreateSerializer,
    }
    queryset = (
        ProductsVariants.objects.prefetch_related(
            "images",
            "materials",
            "materials__product_material",
            "batches",
            "batches__warehouse_inventory_product_variant_batch",
        ).annotate(
            total_inventory=Coalesce(
                Sum("batches__warehouse_inventory_product_variant_batch__quantity"), 
                Value(0), 
                output_field=IntegerField()
            ),
            category_name=F("product__category__name"),
        ).all()
    )
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    )
    filterset_class = ProductVariantFilterset
    search_fields = ("name", "SKU_code", "bar_code", "note", "product__SKU_code")
    ordering_fields = "__all__"

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)

    def get_serializer(self, *args, **kwargs):
        if self.action == "bulk_create":
            kwargs.update({"many": True})
        return super().get_serializer(*args, **kwargs)

    @swagger_auto_schema(operation_summary="Danh sách sản phẩm biến thể")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Chi tiết thông tin sản phẩm biến thể")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Tạo mới sản phẩm biến thể, combo hoặc bundle"
    )
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid():
            variant_data = serializer.data
            variant_data.update({"created_by": request.user})

            materials = variant_data.pop("materials", [])
            combo_variants = variant_data.pop("combo_variants", [])
            tags = variant_data.pop("tags", [])
            inventory_quantity = variant_data.pop("inventory_quantity", None)
            inventory_note = variant_data.pop("inventory_note", None)

            variant_model = ProductsVariants.objects.create(**variant_data)
            variant_model.tags.add(*tags)

            if materials:
                product_variant_materials = []
                for material in materials:
                    product_variant_materials.append(
                        ProductsVariantsMaterials(
                            product_material_id=material.get("id"),
                            product_variant_id=variant_model.id,
                            quantity=material.get("quantity"),
                            weight=material.get("weight"),
                        )
                    )
                ProductsVariantsMaterials.objects.bulk_create(product_variant_materials)

            # Create combo or bundle
            if combo_variants and variant_model.type != ProductVariantType.SIMPLE.value:
                for variant_detail in combo_variants:
                    variant_detail.update({"origin_variant": variant_model})
                    ProductsVariantsComboDetail.objects.create(**variant_detail)

            if inventory_quantity:
                batch = ProductsVariantsBatches.objects.create(
                    product_variant=variant_model, name=variant_model.name, is_default=True
                )
                default_warehouse = Warehouse.objects.filter(is_default=True).first()
                if not default_warehouse:
                    raise ValidationError({"warehouse": "Không tìm thấy kho mặc định"})
                
                data={
                    "is_confirm": True,
                    "type": WarehouseSheetType.Import.value,
                    "note": inventory_note or "",
                    "warehouse": default_warehouse.id,
                    "sheet_detail": [{
                        "product_variant_batch": batch.id,
                        "quantity": inventory_quantity
                    }]
                }
                warehouse_serializer = WarehouseSheetImportExportCreateSerializer(data=data)
                warehouse_serializer.is_valid(raise_exception=True)
                WarehouseSheetImportExportViewSet.perform_create(WarehouseSheetImportExportViewSet, warehouse_serializer, self.request.user)
                
            return Response(
                data=ProductVariantRetrieveSerializer(instance=variant_model).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_summary="Tạo nhiều biến thể cho sản phẩm")
    @transaction.atomic
    @decorators.action(methods=["post"], detail=False, url_path="bulk-create")
    def bulk_create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.validated_data["modified_by"] = self.request.user
        return super().perform_update(serializer)

    @swagger_auto_schema(
        operation_summary="Cập nhật một phần thông tin sản phẩm biến thể"
    )
    def partial_update(self, request, *args, **kwargs):
        materials = request.data.pop("materials", [])
        if materials:
            instance = self.get_object()
            product_variant_materials = []
            ProductsVariantsMaterials.objects.filter(
                product_variant_id=instance.id
            ).delete()
            for material in materials:
                product_variant_materials.append(
                    ProductsVariantsMaterials(
                        product_material_id=material.get("id"),
                        product_variant_id=instance.id,
                        quantity=material.get("quantity"),
                        weight=material.get("weight"),
                    )
                )
            ProductsVariantsMaterials.objects.bulk_create(product_variant_materials)
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Xoá sản phẩm biến thể")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ProductMaterialViewset(CustomModelViewSet):
    http_method_names = ("get", "post", "patch", "delete")
    serializer_class = ProductMaterialSerializer
    # serializer_classes = {
    #     "list": ProductMaterialSerializer,
    #     "create": ProductMaterialCreateUpdateSerializer,
    #     "retrieve": ProductMaterialSerializer,
    #     "partial_update": ProductMaterialCreateUpdateSerializer,
    # }
    queryset = (
        ProductsMaterials.objects.prefetch_related(
            "images",
            # "tags",
            "batches",
            "variants",
            "variants__product_variant",
            "batches__warehouse_inventory_product_variant_batch",
        )
        .annotate(
            warehouse_inventory=F("batches__warehouse_inventory_product_variant_batch"),
        )
        .all()
    )
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    )
    filterset_class = ProductMaterialFilterset
    search_fields = ("name", "SKU_code", "note", "variants__product_variant__SKU_code")
    ordering_fields = "__all__"

    # def get_serializer_class(self):
    #     return self.serializer_classes.get(self.action, self.serializer_class)

    @swagger_auto_schema(operation_summary="Danh sách nguyên liệu sản phẩm")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Chi tiết thông tin nguyên liệu ")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Tạo mới sản phẩm nguyên liệu")
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_summary="Cập nhật một phần thông tin nguyên liệu")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class ProductMaterialVariantViewset(CustomModelViewSet):
    http_method_names = ("get", "post", "patch", "delete")
    serializer_class = ProductMaterialVariantSerializer
    queryset = ProductsVariantsMaterials.objects.all()
    filter_backends = (filters.OrderingFilter, django_filters.DjangoFilterBackend)
    filterset_class = ProductVariantMaterialFilterset
    ordering_fields = "__all__"


class ProductVariantBatchViewset(
    ActivityLogMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    http_method_names = ("get", "post", "patch")
    serializer_class = ProductVariantBatchSerializer
    serializer_classes = {
        "create": ProductVariantBatchCreateSerializer,
        "partial_update": ProductVariantBatchUpdateSerializer,
    }
    queryset = ProductsVariantsBatches.objects.prefetch_related(
        "product_material__images",
        "product_variant__images",
    ).all()
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    )
    filterset_class = ProductVariantBatchFilterset
    search_fields = ("name",)
    ordering_fields = "__all__"

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)

    @swagger_auto_schema(operation_summary="Danh sách lô sản phẩm")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Tạo mới lô sản phẩm")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Cập nhật một phần thông tin lô sản phẩm")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class ProductReportListAPIView(generics.ListAPIView):
    http_method_names = ("get",)
    queryset = ProductsVariants.objects.prefetch_related(
        Prefetch(
            "orders_items",
            queryset=OrdersItems.objects.select_related("order__shipping"),
        ),
        Prefetch(
            "batches",
            queryset=ProductsVariantsBatches.objects.prefetch_related(
                "warehouse_inventory_product_variant_batch",
                "warehouse_sheet_import_export_detail_product_variant_batch",
            ),
        ),
    )
    filter_backends = (django_filters.DjangoFilterBackend,)
    filterset_class = ProductReportsFilterset
    serializer_class = ProductReportPivotResponse
    pagination_class = None

    @swagger_auto_schema(
        operation_summary="Báo cáo tổng hợp sản phẩm",
        query_serializer=ProductReportPivotParams,
    )
    def get(self, request, *args, **kwargs):
        params = ProductReportPivotParams(data=request.query_params)
        params.is_valid(raise_exception=True)
        queryset = self.filter_queryset(self.get_queryset())
        pivot_table = ProductReportPivot(queryset=queryset, **params.validated_data)
        return Response(data={"count": len(pivot_table.result), "results": pivot_table.result})

class ProductVariantRevenueView(generics.ListAPIView):
    serializer_class = ProductVariantRevenueSerializer
    queryset = (
        ProductsVariants.objects.prefetch_related("images")
        .annotate(
            inventory_quantity=Coalesce(
                Sum("batches__warehouse_inventory_product_variant_batch__quantity", distinct=True),
                Value(0),
                output_field=IntegerField()
            )
        )
        .all()
    )
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, django_filters.DjangoFilterBackend)
    filterset_class = ProductVariantRevenueFilterset
    search_fields = ("name", "SKU_code", "bar_code")
    ordering_fields = "__all__"

    def get_queryset(self):
        queryset = self.queryset
        query = self.get_query_by_date_range()
        exclude = Q()
        query.add(Q(orders_items__order__status=OrderStatus.COMPLETED), Q.AND)
        query.add(~Q(orders_items__order__complete_time=None), Q.AND)
        if self.request.query_params.get("customer"):
            customer_query = Q(orders_items__order__customer=self.request.query_params.get("customer"))
            query.add(customer_query, Q.AND)
            queryset = queryset.filter(customer_query)
            exclude = Q(sold_quantity=0)
        
        sold_quantity_subquery = self.get_sold_quantity_subquery(query)
        revenue_subquery = self.get_revenue_subquery(query)

        return queryset.annotate(
            sold_quantity=Coalesce(Subquery(sold_quantity_subquery), Value(0), output_field=IntegerField()),
            revenue=Coalesce(Subquery(revenue_subquery), Value(0), output_field=IntegerField())
        ).exclude(exclude)

    @swagger_auto_schema(operation_summary="Danh sách doanh thu sản phẩm biến thể")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_query_by_date_range(self):
        complete_time_from = self.request.query_params.get("complete_time_from")
        complete_time_to = self.request.query_params.get("complete_time_to")

        if complete_time_from and complete_time_to:
            return Q(
                orders_items__order__complete_time__date__gte=complete_time_from, 
                orders_items__order__complete_time__date__lte=complete_time_to
            )
        
        return Q() 

    def get_sold_quantity_subquery(self, query):
        return ProductsVariants.objects.filter(
            id=OuterRef('pk')
        ).annotate(
            sold_quantity=Coalesce(
                Sum('orders_items__quantity', filter=query),
                Value(0),
                output_field=IntegerField()
            )
        ).values('sold_quantity')[:1]

    def get_revenue_subquery(self, query):
        return ProductsVariants.objects.filter(
            id=OuterRef('pk')
        ).annotate(
            revenue=Coalesce(
                Sum(
                    Case(
                        When(orders_items__price_total_input__gt=0, then=F('orders_items__price_total_input')),
                        default=F('orders_items__price_total')
                    ),
                    filter=query
                ),
                Value(0),
                output_field=IntegerField()
            )
        ).values('revenue')[:1]


class ImportProductVariantsView(ActivityLogMixin, generics.CreateAPIView):
    serializer_class = ImportProductVariantSerializer
    queryset = ProductsVariants.objects.all()

    @swagger_auto_schema(operation_summary="Nhập nhiều biến thể từ file")
    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                existing_sku = set(
                    self.get_queryset().values_list("SKU_code", flat=True)
                )
                existing_categories = {
                    category.name: category
                    for category in ProductCategory.objects.all()
                }
                existing_products = {
                    product.SKU_code: product for product in Products.objects.all()
                }
                self.process_existing_category(existing_categories)
                self.process_existing_product(existing_categories, existing_products)

                serializer = self.get_serializer(
                    data=request.data,
                    many=True,
                    context={
                        "existing_sku": existing_sku,
                        "existing_products": existing_products,
                    },
                )
                if serializer.is_valid():
                    validated_data = serializer.validated_data
                    inventory_quantity = {
                        item["SKU_code"]: item.pop("batches")[
                            "warehouse_inventory_product_variant_batch"
                        ]["quantity"]
                        for item in validated_data
                    }
                    new_variants = [
                        ProductsVariants(created_by=request.user, **item)
                        for item in validated_data
                    ]
                    ProductsVariants.objects.bulk_create(new_variants)
                    self.save_inventory(new_variants, inventory_quantity)
                    return Response(
                        data={
                            "success": True,
                            "data": [{"id": obj.id} for obj in new_variants]
                        }, status=status.HTTP_201_CREATED
                    )
                # return Response(
                #     data=serializer.errors, status=status.HTTP_400_BAD_REQUEST
                # )
                raise ValidationError("Validation failed")
        except ValidationError:
            transaction.rollback()

            df = self.process_errors(serializer)
            buffer = self.process_file(df)
            file_name = f"{self.request.user}_import_variants_error_{str(int(time.time()))}.xlsx"
            response = FileResponse(
                buffer,
                as_attachment=True,
                filename=file_name,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response.status_code = status.HTTP_206_PARTIAL_CONTENT
            return response
        except Exception as e:
            transaction.rollback()
            raise APIException(e)

    def process_existing_category(self, existing_categories: dict):
        new_category = {}
        for data in self.request.data:
            category_name = data.get("product_category")
            if category_name not in existing_categories:
                new_category[f"{category_name}"] = ProductCategory(name=category_name)
        ProductCategory.objects.bulk_create(new_category.values())
        # existing_categories.update({key: value for key, value in new_category.items()})
        existing_categories.update(new_category)

    def process_existing_product(
        self, existing_categories: dict, existing_products: dict
    ):
        new_product = {}
        for data in self.request.data:
            product_SKU_code = data.get("product_SKU_code")
            product_name = data.get("product_name")
            category_name = data.get("product_category")
            if product_SKU_code not in existing_products:
                category = existing_categories.get(category_name)
                new_product[f"{product_SKU_code}"] = Products(
                    SKU_code=product_SKU_code,
                    name=product_name,
                    category=category,
                    created_by=self.request.user,
                )
        Products.objects.bulk_create(new_product.values())
        # existing_products.update({key: value for key, value in new_product.items()})
        existing_products.update(new_product)

    def save_inventory(
        self, variants: list[ProductsVariants], inventory_quantity: dict
    ):
        default_warehouse = Warehouse.objects.filter(
            is_default=True
        ).first()
        if not default_warehouse:
            raise ValidationError({"error": "Kho mặc định chưa tồn tại"})
        new_batch, new_inventory = [], []
        for variant in variants:
            batch = ProductsVariantsBatches(name=variant.name, product_variant=variant)
            new_batch.append(batch)
            new_inventory.append(
                WarehouseInventory(
                    created_by=self.request.user,
                    warehouse=default_warehouse,
                    product_variant_batch=batch,
                    quantity=inventory_quantity.get(variant.SKU_code, 0),
                )
            )

        ProductsVariantsBatches.objects.bulk_create(new_batch)
        WarehouseInventory.objects.bulk_create(new_inventory)

    def process_errors(self, serializer: ImportProductVariantSerializer):
        column_rename_dict = {
            "product_name": "*Tên sản phẩm",
            "product_SKU_code": "*SKU code",
            "product_category": "*Danh mục",
            "name": "*Tên biến thể",
            "SKU_code": "*SKU biến thể",
            "sale_price": "*Giá bán",
            "neo_price": "*Giá niêm yết",
            "note": "*Ghi chú",
            "errors": "Lỗi",
            "inventory_quantity": "*Tồn kho",
        }

        df_errors = pd.DataFrame(serializer.errors)
        df_errors.rename(columns=column_rename_dict, inplace=True)

        def drop_na_columns(row):
            return row.dropna().to_dict()

        filtered_rows = df_errors.apply(drop_na_columns, axis=1)
        errors_rename = filtered_rows.tolist()
        error_data = []
        for i, data in enumerate(self.request.data):
            error_row = data.copy()
            if i < len(errors_rename):
                errors = errors_rename[i]
                error_row["errors"] = ", ".join(
                    f"{key}: {msg[0] if isinstance(msg, list) else msg}"
                    for key, msg in errors.items()
                )
            else:
                error_row["errors"] = ""
            error_data.append(error_row)

        df = pd.DataFrame(error_data)
        df.rename(columns=column_rename_dict, inplace=True)
        return df

    def process_file(self, df: pd.DataFrame):
        buffer = BytesIO()
        wb = Workbook()
        ws = wb.active
        ws.title = "Lỗi"

        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)

        for column_cells in ws.columns:
            length = max(len(str(cell.value)) for cell in column_cells)
            ws.column_dimensions[column_cells[0].column_letter].width = length + 2
            for cell in column_cells:
                cell.alignment = Alignment(horizontal="center")

        wb.save(buffer)
        buffer.seek(0)
        return buffer


class BulkUpdateProductVariantsView(ActivityLogMixin, generics.UpdateAPIView):
    serializer_class = BulkUpdateProductVariantSerializer
    queryset = ProductsVariants.objects.all()

    @swagger_auto_schema(operation_summary="Cập nhật nhiều biến thể từ file")
    def update(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                variants_db = self.get_queryset()
                existing_sku = set()
                existing_variants = {}
                for variant in variants_db:
                    existing_sku.add(variant.SKU_code)
                    existing_variants[variant.SKU_code] = variant

                serializer = self.get_serializer(
                    data=request.data,
                    many=True,
                    context={
                        "existing_sku": existing_sku,
                    },
                )
                if serializer.is_valid():
                    validated_data = serializer.validated_data
                    update_variants = []
                    for item in validated_data:
                        variant = existing_variants.get(f"{item.get('SKU_code')}")
                        for attr, value in item.items():
                            if value is not None:
                                setattr(variant, attr, value)
                        update_variants.append(variant)

                    ProductsVariants.objects.bulk_update(
                        update_variants, 
                        ["sale_price", "neo_price"]
                    )
                    return Response(
                        data={
                            "success": True,
                            "data": [{"id": obj.id} for obj in update_variants]
                        }, status=status.HTTP_200_OK
                    )
                raise ValidationError("Validation failed")
        except ValidationError:
            transaction.rollback()

            df = self.process_errors(serializer)
            buffer = self.process_file(df)
            file_name = f"{self.request.user}_bulk_update_variants_error_{str(int(time.time()))}.xlsx"
            response = FileResponse(
                buffer,
                as_attachment=True,
                filename=file_name,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response.status_code = status.HTTP_206_PARTIAL_CONTENT
            return response
        except Exception as e:
            transaction.rollback()
            traceback.print_exc()
            raise APIException(e)
      

    def process_errors(self, serializer: ImportProductVariantSerializer):
        column_rename_dict = {
            "SKU_code": "*SKU biến thể",
            "sale_price": "*Giá bán",
            "neo_price": "*Giá niêm yết",
            "errors": "Lỗi",
        }

        df_errors = pd.DataFrame(serializer.errors)
        df_errors.rename(columns=column_rename_dict, inplace=True)

        def drop_na_columns(row):
            return row.dropna().to_dict()

        filtered_rows = df_errors.apply(drop_na_columns, axis=1)
        errors_rename = filtered_rows.tolist()
        error_data = []
        for i, data in enumerate(self.request.data):
            error_row = data.copy()
            if i < len(errors_rename):
                errors = errors_rename[i]
                error_row["errors"] = ", ".join(
                    f"{key}: {msg[0] if isinstance(msg, list) else msg}"
                    for key, msg in errors.items()
                )
            else:
                error_row["errors"] = ""
            error_data.append(error_row)

        df = pd.DataFrame(error_data)
        df.rename(columns=column_rename_dict, inplace=True)
        return df

    def process_file(self, df: pd.DataFrame):
        buffer = BytesIO()
        wb = Workbook()
        ws = wb.active
        ws.title = "Lỗi"

        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)

        for column_cells in ws.columns:
            length = max(len(str(cell.value)) for cell in column_cells)
            ws.column_dimensions[column_cells[0].column_letter].width = length + 2
            for cell in column_cells:
                cell.alignment = Alignment(horizontal="center")

        wb.save(buffer)
        buffer.seek(0)
        return buffer
