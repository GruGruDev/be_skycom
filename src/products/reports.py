import pandas as pd
from django.db.models import Count
from django.db.models import F
from django.db.models import Q
from django.db.models import Sum
from django.db.models import Value

from orders.enums import OrderItemDataFlowType
from products.models import ProductsVariants
from utils.reports import BindingExprEnum
from utils.reports import Dimensions
from utils.reports import ExprsFilterEnum as ExprD
from utils.reports import Filter
from utils.reports import InType
from utils.reports import Metric
from utils.reports import MetricExprs
from utils.reports import PivotReportBase
from warehouses.enums import SheetImportExportType
from warehouses.enums import WarehouseBaseType


class ProductReportPivot(PivotReportBase):
    def __init__(
        self,
        queryset,
        dimensions,
        metrics,
        filters=None,
        b_expr_dims: BindingExprEnum = BindingExprEnum.AND,
        b_expr_metrics: BindingExprEnum = BindingExprEnum.AND,
    ):
        self.dimensions: dict = self._dimensions(dimensions)

        self.metrics: dict = self._metrics(metrics)

        self.filterset: Q = Q()
        self.df_filterset: list[str] = []
        self.b_expr_dims = b_expr_dims
        self.b_expr_metrics = b_expr_metrics
        self._parse_filter(filters)

        self.queryset = self._queryset(queryset)
        self._excute_filterset()

        if "sheet_type" in dimensions:
            if "product_variants" not in dimensions:
                self.dimensions.update(self.DIMS_DEFAULT)
            sheet_type = self.dimensions.pop("sheet_type")
            self.df: pd.DataFrame = self._data_frame()
            df_merge = self._get_df_dims_sheet_type()
            self.df = pd.merge(self.df, df_merge, how="inner", on="SKU_code")

            # set dimension and metric for sheet type
            self.dimensions["sheet_type"] = sheet_type
            self.metrics["quantity_in_sheet"] = Metric(expr=MetricExprs.MEAN, field="quantity_in_sheet", _in=InType.query)
        else:
            self.df: pd.DataFrame = self._data_frame()
        self.pivot_table = self._pivot()
        self._excute_df_filterset()

        self.result = self._output()

    DIMS_DEFAULT = {
        # Sản phẩm
        "product_variants": Dimensions(fields=["SKU_code", "name"]),
    }
    DIMS_AVB = {
        # Sản phẩm
        "product_variants": Dimensions(fields=["SKU_code", "name"]),
        # Ngày tạo đơn hàng
        "created_date": Dimensions(fields=["created__date"], rename={"created__date": "created_date"}),
        # Kho
        "warehouse": Dimensions(
            fields=[
                "batches__warehouse_inventory_product_variant_batch__warehouse__id",
                "batches__warehouse_inventory_product_variant_batch__warehouse__name",
            ],
            rename={
                "batches__warehouse_inventory_product_variant_batch__warehouse__id": "warehouse_id",
                "batches__warehouse_inventory_product_variant_batch__warehouse__name": "warehouse_name",
            },
        ),
        # Lô
        "product_variants_batches": Dimensions(fields=["batches__id", "batches__name"]),
        # Phiếu
        "sheet_type": Dimensions(fields=["sheet_type"]),
    }
    METRICS_AVB = {
        "total_revenue": Metric(expr=MetricExprs.SUM, field="total_revenue", _in=InType.query),
        # 2. Actual Revenue: Total value of goods sold after subtracting discounts
        "total_actual_revenue": Metric(expr=MetricExprs.SUM, field="total_actual_revenue", _in=InType.query),
        # 3. Total Promotion Amount: Total amount of promotion for the corresponding product
        "total_promotion_amount": Metric(expr=MetricExprs.SUM, field="total_promotion_amount", _in=InType.query),
        # 4. Quantity Sold: Quantity of products that appear in successfully delivered orders
        "quantity_sold": Metric(expr=MetricExprs.SUM, field="quantity_sold", _in=InType.query),
        # 5. Actual Quantity Sold: Quantity of products actually sold (excluding returns)
        "actual_quantity_sold": Metric(expr=MetricExprs.SUM, field="actual_quantity_sold", _in=InType.query),
        # 6. Number of Orders: Number of orders containing the product
        "number_of_orders": Metric(expr=MetricExprs.SUM, field="number_of_orders", _in=InType.query),
        # 7. Inventory Quantity
        "inventory_quantity": Metric(expr=MetricExprs.SUM, field="inventory_quantity", _in=InType.query),
        # 8. Quantity Purchased
        "quantity_import": Metric(expr=MetricExprs.SUM, field="quantity_import", _in=InType.query),
        # 9. Quantity Sold Out
        "quantity_export": Metric(expr=MetricExprs.SUM, field="quantity_export", _in=InType.query),
        # # 10. Quantity Sheet
        # "quantity": Metric(expr=MetricExprs.MEAN, field="quantity", _in=InType.query)
    }

    FILTERS_AVB = {
        "total_revenue": Filter(
            field="total_revenue",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE],
            value_types=[int],
        ),
        "total_actual_revenue": Filter(
            field="total_actual_revenue",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE],
            value_types=[int],
        ),
        "total_promotion_amount": Filter(
            field="total_promotion_amount",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE],
            value_types=[int],
        ),
        "quantity_sold": Filter(
            field="quantity_sold",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE],
            value_types=[int],
        ),
        "actual_quantity_sold": Filter(
            field="actual_quantity_sold",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE],
            value_types=[int],
        ),
        "number_of_orders": Filter(
            field="number_of_orders",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE],
            value_types=[int],
        ),
        "inventory_quantity": Filter(
            field="inventory_quantity",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE],
            value_types=[int],
        ),
        "quantity_import": Filter(
            field="quantity_import",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE],
            value_types=[int],
        ),
        "quantity_export": Filter(
            field="quantity_export",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE],
            value_types=[int],
        ),
    }

    def _queryset(self, queryset):
        # 1. Revenue: The selling value of the product before discounts
        if "total_revenue" in self.metrics:
            queryset = queryset.annotate(total_revenue=Sum("orders_items__price_total_neo"))

        # 2. Actual Revenue: Total value of goods sold after subtracting discounts
        if "total_actual_revenue" in self.metrics:
            queryset = queryset.annotate(total_actual_revenue=Sum("orders_items__price_total"))

        # 3. Total Promotion Amount: Total amount of promotion for the corresponding product
        if "total_promotion_amount" in self.metrics:
            queryset = queryset.annotate(total_promotion_amount=Sum("orders_items__discount"))

        # 4.1 Quantity Sold: Quantity of products that appear in successfully delivered orders

        # 6. Number of Orders: Number of orders containing the product
        if "number_of_orders" in self.metrics:
            queryset = queryset.annotate(number_of_orders=Count("orders_items__order__order_key", distinct=True))

        # 7. Inventory Quantity
        if "inventory_quantity" in self.metrics:
            queryset = queryset.annotate(inventory_quantity=Sum("batches__warehouse_inventory_product_variant_batch__quantity"))

        # 8. Quantity import
        if "quantity_import" in self.metrics:  # match tới bảng WarehouseSheetImportExportDetail

            queryset = queryset.filter(
                batches__warehouse_sheet_import_export_detail_product_variant_batch__sheet__type=SheetImportExportType.IMPORT.value
            ).annotate(quantity_import=Sum("batches__warehouse_sheet_import_export_detail_product_variant_batch__quantity"))

        # 8. Quantity export
        if "quantity_export" in self.metrics:  # match tới bảng WarehouseSheetImportExportDetail
            queryset = queryset.filter(
                batches__warehouse_sheet_import_export_detail_product_variant_batch__sheet__type=SheetImportExportType.EXPORT.value
            ).annotate(quantity_export=Sum("batches__warehouse_sheet_import_export_detail_product_variant_batch__quantity"))

        return queryset

    @staticmethod
    def _get_df_dims_sheet_type():
        import_query = (
            ProductsVariants.objects.prefetch_related("batches__warehouse_sheet_import_export_detail_product_variant_batch")
            .filter(
                batches__warehouse_sheet_import_export_detail_product_variant_batch__sheet__type=WarehouseBaseType.IMPORT,
                batches__warehouse_sheet_import_export_detail_product_variant_batch__id__isnull=False,
            )
            .annotate(
                sheet_type=Value(WarehouseBaseType.IMPORT),
                quantity_in_sheet=F("batches__warehouse_sheet_import_export_detail_product_variant_batch__quantity"),
            )
        )

        export_query = (
            ProductsVariants.objects.prefetch_related("batches__warehouse_sheet_import_export_detail_product_variant_batch")
            .filter(
                batches__warehouse_sheet_import_export_detail_product_variant_batch__sheet__type=WarehouseBaseType.EXPORT,
                batches__warehouse_sheet_import_export_detail_product_variant_batch__id__isnull=False,
            )
            .annotate(
                sheet_type=Value(WarehouseBaseType.EXPORT),
                quantity_in_sheet=F("batches__warehouse_sheet_import_export_detail_product_variant_batch__quantity"),
            )
        )

        transfer_query = (
            ProductsVariants.objects.prefetch_related("batches__warehouse_sheet_transfer_detail_product_variant_batch")
            .filter(batches__warehouse_sheet_transfer_detail_product_variant_batch__id__isnull=False)
            .annotate(
                sheet_type=Value(WarehouseBaseType.TRANSFER),
                quantity_in_sheet=F("batches__warehouse_sheet_transfer_detail_product_variant_batch__quantity"),
            )
        )

        check_query = (
            ProductsVariants.objects.prefetch_related("batches__warehouse_sheet_check_detail_product_variant_batch")
            .filter(batches__warehouse_sheet_check_detail_product_variant_batch__id__isnull=False)
            .annotate(
                sheet_type=Value(WarehouseBaseType.CHECK),
                quantity_in_sheet=F("batches__warehouse_sheet_check_detail_product_variant_batch__quantity_actual"),
            )
        )

        queryset = import_query.union(export_query, transfer_query, check_query).values("SKU_code", "sheet_type", "quantity_in_sheet")
        df = pd.DataFrame.from_dict(queryset)
        return df
