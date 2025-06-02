from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from orders.api.views import ConfirmationLogListView
from orders.api.views import ConfirmationLogTurnRetrieveView
from orders.api.views import OrderDetailReportListView
from orders.api.views import OrderHistoryList
from orders.api.views import OrderItemDetailReportListView
from orders.api.views import OrderKPIReportListView
from orders.api.views import OrderRevenueByProductReportView
from orders.api.views import OrderRevenueBySaleReportView
from orders.api.views import OrderRevenueRatioView
from orders.api.views import OrderRevenueReportDashboardView
from orders.api.views import OrdersCancelReasonViewset
from orders.api.views import OrdersTypeViewset
from orders.api.views import OrderSheetConfirmAPIView
from orders.api.views import OrdersMobileViewset
from orders.api.views import OrdersPaymentsHistoryListView
from orders.api.views import OrdersPaymentsViewset
from orders.api.views import OrdersPivotReportAPIView
from orders.api.views import OrdersPivotReportCompareAPIView
from orders.api.views import OrdersTagsViewset
from orders.api.views import OrdersViewset
from orders.api.views import PaymentsAuditUploadView
from orders.api.views import TurnListView

router = DefaultRouter()
router.register("tags", OrdersTagsViewset, basename="orders_tags")
router.register("cancel-reason", OrdersCancelReasonViewset, basename="orders_cancel_reason")
router.register("type", OrdersTypeViewset, basename="orders_cancel_reason")
router.register("payments", OrdersPaymentsViewset, basename="orders_payment")
router.register("mobile", OrdersMobileViewset, basename="orders-mobile")
router.register("", OrdersViewset, basename="orders")


urlpatterns = [
    path("confirm/logs/turn", ConfirmationLogTurnRetrieveView.as_view(), name="confirm-logs-turn"),
    path("confirm/logs/turn/all", TurnListView.as_view(), name="order-all-turn"),
    path("confirm/logs/all", ConfirmationLogListView.as_view(), name="confirm-logs-all"),
    path("sheets/confirm/", OrderSheetConfirmAPIView.as_view(), name="order-sheets-confirm"),
    path("reports/pivot", OrdersPivotReportAPIView.as_view(), name="orders-reports-pivot"),
    path("reports/pivot/compare", OrdersPivotReportCompareAPIView.as_view(), name="orders-reports-pivot-compare"),
    path("<uuid:pk>/histories/", OrderHistoryList.as_view(), name="histories"),
    path("payments/<uuid:pk>/histories", OrdersPaymentsHistoryListView.as_view(), name="payments_histories"),
    path("payments/upload-file", PaymentsAuditUploadView.as_view(), name="payment-audit-upload-file"),
    path("", include(router.urls)),
    # report
    path("reports/detail/order-item/", OrderItemDetailReportListView.as_view(), name="order-item-detail"),
    path("reports/detail/order/", OrderDetailReportListView.as_view(), name="order-detail"),
    path("reports/detail/order-kpi/", OrderKPIReportListView.as_view(), name="order-kpi"),
    path("reports/revenue/dashboard", OrderRevenueReportDashboardView.as_view(), name="dashboard-revenue"),
    path("reports/revenue/ratio", OrderRevenueRatioView.as_view(), name="pre-and-current-month-revenue"),
    path("reports/revenue/product", OrderRevenueByProductReportView.as_view(), name="revenue-by-product-variant"),
    path("reports/revenue/sale", OrderRevenueBySaleReportView.as_view(), name="revenue-by-sale"),
]
