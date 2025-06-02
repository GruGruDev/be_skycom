import django_filters.rest_framework as django_filters
from django.db import transaction
from rest_framework import filters
from rest_framework import permissions

from core.views import CustomModelViewSet
from promotions import models
from promotions.api.filters import PromotionOrderFilterset
from promotions.api.filters import PromotionVariantFilterset
from promotions.api.serializers import promotion_orders
from promotions.api.serializers import promotion_variants
from promotions.api.serializers import promotion_vouchers


class PromotionOrderViewSet(CustomModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    default_serializer_class = promotion_orders.PromotionOrderReadOneSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.PromotionOrder.objects.all()
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, django_filters.DjangoFilterBackend)
    filterset_class = PromotionOrderFilterset
    search_fields = ("name",)
    ordering_fields = "__all__"

    serializer_classes = {
        "create": promotion_orders.PromotionOrderCreateSerializer,
        "partial_update": promotion_orders.PromotionOrderUpdateSerializer,
        "list": promotion_orders.PromotionOrderReadListSerializer,
        "retrieve": promotion_orders.PromotionOrderReadOneSerializer,
    }

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.default_serializer_class)

    def perform_create(self, serializer):
        serializer.validated_data["created_by"] = self.request.user
        return super().perform_create(serializer)

    def perform_update(self, serializer):
        serializer.validated_data["modified_by"] = self.request.user
        return super().perform_update(serializer)


class PromotionVoucherViewSet(CustomModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    default_serializer_class = promotion_vouchers.PromotionVoucherReadOnceSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.PromotionVoucher.objects.all()
    ordering_fields = "__all__"
    serializer_classes = {
        "create": promotion_vouchers.PromotionVoucherCreateSerializer,
        "partial_update": promotion_vouchers.PromotionVoucherUpdateSerializer,
        "list": promotion_vouchers.PromotionVoucherReadListSerializer,
        "retrieve": promotion_vouchers.PromotionVoucherReadOnceSerializer,
    }

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.default_serializer_class)

    def perform_create(self, serializer):
        serializer.validated_data["created_by"] = self.request.user
        return super().perform_create(serializer)

    def perform_update(self, serializer):
        serializer.validated_data["modified_by"] = self.request.user
        return super().perform_update(serializer)


class PromotionVariantViewSet(CustomModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    queryset = models.PromotionVariant.objects.prefetch_related("promotion_variant_other_variant").all()

    default_serializer_class = promotion_variants.PromotionVariantReadOnceSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, django_filters.DjangoFilterBackend)
    search_fields = ("name",)
    ordering_fields = "__all__"
    filterset_class = PromotionVariantFilterset

    serializer_classes = {
        "create": promotion_variants.PromotionVariantCreateSerializer,
        "partial_update": promotion_variants.PromotionVariantUpdateSerializer,
        "list": promotion_variants.PromotionVariantReadListSerializer,
        "retrieve": promotion_variants.PromotionVariantReadOnceSerializer,
    }

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.default_serializer_class)

    def perform_create(self, serializer):
        current_user = self.request.user
        serializer.validated_data["created_by"] = current_user
        other_variants = serializer.validated_data.pop("other_variants", None)

        with transaction.atomic():
            promotion_variant = serializer.save()
            if other_variants:
                for variant in other_variants:
                    variant["created_by"] = current_user
                    variant["promotion_variant"] = promotion_variant
                    models.PromotionVariantsOtherVariant.objects.create(**variant)

    def perform_update(self, serializer):
        serializer.validated_data["modified_by"] = self.request.user
        return super().perform_update(serializer)
