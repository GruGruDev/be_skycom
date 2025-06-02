from django.db.models import F
from django.db.models import OuterRef
from django.db.models import Subquery
from django.db.models import Sum
from django.db.models import Value

from utils.reports import Dimensions
from utils.reports import ExprsFilterEnum as ExprD
from utils.reports import Filter
from utils.reports import InType
from utils.reports import Metric
from utils.reports import MetricExprs
from utils.reports import PivotReportBase
from warehouses.enums import SheetImportExportType
from warehouses.models import WarehouseSheetImportExport


class OrdersReportPivot(PivotReportBase):
    DIMS_AVB = {
        # Ngày tạo đơn hàng
        "created_date": Dimensions(fields=["created__date"], rename={"created__date": "created_date"}),
        # Kênh bán hàng
        "source": Dimensions(fields=["source__id", "source__name"]),
        # Trạng thái vận đơn
        "shipping_status": Dimensions(fields=["shipping__carrier_status"], rename={"shipping__carrier_status": "shipping_status"}),
        # Trạng thái đơn hàng
        "status": Dimensions(fields=["status"]),
        # Người tạo đơn
        "created_by": Dimensions(fields=["created_by__id", "created_by__name"]),
        # Người xác nhận đơn
        "complete_by": Dimensions(fields=["complete_by__id", "complete_by__name"]),
        # Ngày xác nhân đơn
        "complete_date": Dimensions(fields=["complete_time__date"], rename={"complete_time__date": "complete_date"}),
        # Ngày tạo vận đơn
        "shipping_date": Dimensions(fields=["shipping__created__date"], rename={"shipping__created__date": "shipping_date"}),
        # Tỉnh thành
        "province": Dimensions(
            fields=["address_shipping__ward__province__label"], rename={"address_shipping__ward__province__label": "province"}
        ),
        "department_sub": Dimensions(
            fields=["created_by__department_sub__name"], rename={"created_by__department_sub__name": "department_sub_name"}
        ),
        # Ngày xuất kho
        "warehouse_exdate": Dimensions(fields=["warehouse_exdate"]),
        # TODO: Chưa triển khai
        # Sản phẩm
        # "product_variant": Dimensions(fields=[]),
        # Chương trình khuyến mãi
        # "promotion": Dimensions(fields=[]),
        # Phương thức thanh toán
        # "payment_method": Dimensions(fields=[]),
    }
    METRICS_AVB = {
        # doanh thu cuối của đơn hàng
        "revenue": Metric(expr=MetricExprs.SUM, field="price_total_order_actual", _in=InType.query),
        # tổng giá bán của sản phẩm trong đơn
        "pre_promo_revenue": Metric(expr=MetricExprs.SUM, field="price_total_variant_all", _in=InType.query),
        # tổng giá bán của của sản phẩm sau khi áp dụng khuyến mãi cho sản phẩm
        "after_promo_revenue": Metric(expr=MetricExprs.SUM, field="price_total_variant_actual", _in=InType.query),
        "after_promo_revenue_input": Metric(expr=MetricExprs.SUM, field="price_total_variant_actual_input", _in=InType.query),
        # tổng giá trị khuyến mãi áp dụng cho sản phẩm
        "total_prod_discount": Metric(expr=MetricExprs.SUM, field="prod_discount", _in=InType.query),
        # tổng giá trị khuyến mãi áp dụng cho đơn hàng
        "total_order_discount": Metric(expr=MetricExprs.SUM, field="price_total_discount_order_promotion", _in=InType.query),
        # Số lượng đơn hàng
        "total_order_quantity": Metric(expr=MetricExprs.SUM, field="total_order_quantity", _in=InType.query),
        # Số lượng sản phẩm trong đơn hàng
        # "total_prod_quantity": Metric(expr=MetricExprs.SUM, field="quatity_total_variant_all", _in=InType.query),
        # Số lượng sản phẩm được tặng
        "total_gift_quantity": Metric(expr=MetricExprs.SUM, field="gift_quantity", _in=InType.query),
        # phụ thu
        "total_addi_fee": Metric(expr=MetricExprs.SUM, field="price_addition_input", _in=InType.query),
        # phí ship
        "total_ship_fee": Metric(expr=MetricExprs.SUM, field="price_delivery_input", _in=InType.query),
        # tổng giá trị giảm giá do salers nhập
        "total_discount_input": Metric(expr=MetricExprs.SUM, field="price_discount_input", _in=InType.query),
        # Trung bình giá trị đơn hàng
        "avg_order_value": Metric(expr=MetricExprs.MEAN, field="avg_order_value", _in=InType.query),
        # Trung bình số lượng sản phầm/đơn hàng
        "avg_items_count": Metric(expr=MetricExprs.MEAN, field="avg_items_count", _in=InType.query),
        # TODO: Trung bình số lượng đơn hàng/ngày
    }

    FILTERS_AVB = {
        # dimensions
        "source": Filter(
            field="source__id",
            _in=InType.query,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.IEP, ExprD.IANYOF, ExprD.INONEOF],
            value_types=[str, int, list],
        ),
        "shipping_status": Filter(
            field="shipping__carrier_status",
            _in=InType.query,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.IEP, ExprD.IANYOF, ExprD.INONEOF],
            value_types=[str, int, list],
        ),
        "status": Filter(
            field="status",
            _in=InType.query,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.IEP, ExprD.IANYOF, ExprD.INONEOF],
            value_types=[int, str, list],
        ),
        "created_by": Filter(
            field="created_by__id",
            _in=InType.query,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.IEP, ExprD.IANYOF, ExprD.INONEOF],
            value_types=[int, str, list],
        ),
        "complete_by": Filter(
            field="complete_by__id",
            _in=InType.query,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.IEP, ExprD.IANYOF, ExprD.INONEOF],
            value_types=[str, int, list],
        ),
        "created_date": Filter(
            field="created__date",
            _in=InType.query,
            exprs=[ExprD.IS, ExprD.IWITHIN, ExprD.IBF, ExprD.IOOBF, ExprD.IAT, ExprD.IOOAF, ExprD.IEP],
            value_types=[list, str, int],
        ),
        "complete_date": Filter(
            field="complete_time__date",
            _in=InType.query,
            exprs=[ExprD.IS, ExprD.IWITHIN, ExprD.IBF, ExprD.IOOBF, ExprD.IAT, ExprD.IOOAF, ExprD.IEP],
            value_types=[list, str, int],
        ),
        "shipping_date": Filter(
            field="shipping__created__date",
            _in=InType.query,
            exprs=[ExprD.IS, ExprD.IWITHIN, ExprD.IBF, ExprD.IOOBF, ExprD.IAT, ExprD.IOOAF, ExprD.IEP],
            value_types=[list, str, int],
        ),
        "warehouse_exdate": Filter(
            field="warehouse_exdate",
            _in=InType.query,
            exprs=[ExprD.IS, ExprD.IWITHIN, ExprD.IBF, ExprD.IOOBF, ExprD.IAT, ExprD.IOOAF, ExprD.IEP],
            value_types=[list, str, int],
        ),
        "province": Filter(
            field="address_shipping__ward__province__code",
            _in=InType.query,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.IEP, ExprD.IANYOF, ExprD.INONEOF],
            value_types=[str, int, list],
        ),
        # metrics
        "revenue": Filter(
            field="revenue",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE, ExprD.BW, ExprD.EX],
            value_types=[int, list],
        ),
        "pre_promo_revenue": Filter(
            field="pre_promo_revenue",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE, ExprD.BW, ExprD.EX],
            value_types=[int, list],
        ),
        "after_promo_revenue": Filter(
            field="after_promo_revenue",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE, ExprD.BW, ExprD.EX],
            value_types=[int, list],
        ),
        "total_order_discount": Filter(
            field="total_order_discount",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE, ExprD.BW, ExprD.EX],
            value_types=[int, list],
        ),
        "total_order_quantity": Filter(
            field="total_order_quantity",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE, ExprD.BW, ExprD.EX],
            value_types=[int, list],
        ),
        "total_prod_quantity": Filter(
            field="total_prod_quantity",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE, ExprD.BW, ExprD.EX],
            value_types=[int, list],
        ),
        "total_gift_quantity": Filter(
            field="total_gift_quantity",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE, ExprD.BW, ExprD.EX],
            value_types=[int, list],
        ),
        "total_addi_fee": Filter(
            field="total_addi_fee",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE, ExprD.BW, ExprD.EX],
            value_types=[int, list],
        ),
        "total_discount_input": Filter(
            field="total_discount_input",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE, ExprD.BW, ExprD.EX],
            value_types=[int, list],
        ),
        "avg_order_value": Filter(
            field="avg_order_value",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE, ExprD.BW, ExprD.EX],
            value_types=[int, list],
        ),
        "avg_items_count": Filter(
            field="avg_items_count",
            _in=InType.data_frame,
            exprs=[ExprD.EQ, ExprD.NEQ, ExprD.GT, ExprD.GTE, ExprD.LT, ExprD.LTE, ExprD.BW, ExprD.EX],
            value_types=[int, list],
        ),
    }

    def _queryset(self, queryset):
        # Lấy ngày xác nhận của phiếu xuất kho đầu tiên
        # TODO: chú ý performance ở đây
        sheet = WarehouseSheetImportExport.objects.filter(order=OuterRef("pk"), type=SheetImportExportType.EXPORT).values(
            "confirm_date__date"
        )
        queryset = queryset.annotate(warehouse_exdate=Subquery(sheet[:1]))
        if "total_order_quantity" in self.metrics:
            queryset = queryset.annotate(total_order_quantity=Value(1))
        if "avg_order_value" in self.metrics:
            queryset = queryset.annotate(avg_order_value=F("price_total_order_actual"))
        if "total_prod_discount" in self.metrics:
            queryset = queryset.annotate(prod_discount=F("price_total_variant_all") - F("price_total_variant_actual"))
        # if "avg_items_count" in self.metrics:
        #     queryset = queryset.annotate(avg_items_count=F("quatity_total_variant_all"))
        if "total_gift_quantity" in self.metrics:
            queryset = queryset.annotate(gift_quantity=Sum("line_items__variant_promotions_used__items_promotion__quantity"))
        return queryset
