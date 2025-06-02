from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from promotions.api.views import PromotionOrderViewSet
from promotions.api.views import PromotionVariantViewSet
from promotions.api.views import PromotionVoucherViewSet

promotion_order_router = DefaultRouter()
promotion_order_router.register("", PromotionOrderViewSet, basename="promotions-orders")

promotion_voucher_router = DefaultRouter()
promotion_voucher_router.register("", PromotionVoucherViewSet, basename="promotions-vouchers")

promotion_variant_router = DefaultRouter()
promotion_variant_router.register("", PromotionVariantViewSet, basename="promotions-variants")

urlpatterns = [
    path("promotion-order/", include(promotion_order_router.urls)),
    path("promotion-voucher/", include(promotion_voucher_router.urls)),
    path("promotion-variant/", include(promotion_variant_router.urls)),
]
