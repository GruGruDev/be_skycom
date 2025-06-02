import django_filters.rest_framework as django_filters
from django.db import models
from django.db.models import Q
from django_filters.conf import settings
from django_filters.filterset import remote_queryset

from locations.models import Provinces
from orders.enums import OrderStatus
from orders.enums import TransportationCareCreationReason
from orders.enums import TransportationCareStatus
from orders.models import Orders
from orders.models import TransportationCare
from orders.models import TransportationCareAction
from orders.models import TransportationCareReason
from products.models import Products
from products.models import ProductsVariants
from users.models import Department
from users.models import User


class OrdersFilterset(django_filters.FilterSet):
    created_from = django_filters.DateFilter(field_name="created__date", lookup_expr="gte")
    created_to = django_filters.DateFilter(field_name="created__date", lookup_expr="lte")
    completed_from = django_filters.DateFilter(field_name="complete_time__date", lookup_expr="gte")
    completed_to = django_filters.DateFilter(field_name="complete_time__date", lookup_expr="lte")
    variant = django_filters.ModelMultipleChoiceFilter(field_name="line_items__variant", queryset=ProductsVariants.objects.all())
    status = django_filters.MultipleChoiceFilter(choices=OrderStatus.choices())
    shipping_isnull = django_filters.BooleanFilter(field_name="shipping", lookup_expr="isnull")
    department_id = django_filters.ModelMultipleChoiceFilter(field_name="created_by__department_id", queryset=Department.objects.all())
    customer_phone = django_filters.CharFilter(field_name="customer__phones__phone", lookup_expr="icontains")
    customer_care_staff_id = django_filters.ModelMultipleChoiceFilter(
        field_name="customer__customer_care_staff", queryset=User.objects.all()
    )

    class Meta:
        model = Orders
        fields = (
            "created_by",
            "modified_by",
            "status",
            "customer",
            "is_print",
            "printed_by",
            "third_party_id",
            "is_cross_sale",
            "source",
            "tracking_number",
            "cancel_reason",
        )
        filter_overrides = {
            models.ForeignKey: {
                "filter_class": django_filters.filters.ModelMultipleChoiceFilter,
                "extra": lambda f: {
                    "queryset": remote_queryset(f),
                    "to_field_name": f.remote_field.field_name,
                    "null_label": settings.NULL_CHOICE_LABEL if f.null else None,
                },
            },
        }


class OrdersMobileFilterset(django_filters.FilterSet):
    created_from = django_filters.DateFilter(field_name="created__date", lookup_expr="gte")
    created_to = django_filters.DateFilter(field_name="created__date", lookup_expr="lte")
    completed_from = django_filters.DateFilter(field_name="complete_time__date", lookup_expr="gte")
    completed_to = django_filters.DateFilter(field_name="complete_time__date", lookup_expr="lte")
    variant = django_filters.ModelMultipleChoiceFilter(field_name="line_items__variant", queryset=ProductsVariants.objects.all())
    status = django_filters.MultipleChoiceFilter(choices=OrderStatus.choices())

    class Meta:
        model = Orders
        fields = (
            "created_by",
            "modified_by",
            "status",
            "customer",
        )


class OrdersReportsFilterset(django_filters.FilterSet):
    created_from = django_filters.DateFilter(field_name="created__date", lookup_expr="gte")
    created_to = django_filters.DateFilter(field_name="created__date", lookup_expr="lte")
    complete_time_from = django_filters.DateFilter(field_name="complete_time__date", lookup_expr="gte")
    complete_time_to = django_filters.DateFilter(field_name="complete_time__date", lookup_expr="lte")
    user_id = django_filters.ModelMultipleChoiceFilter(field_name="modified_by", queryset=User.objects.all())

    class Meta:
        model = Orders
        fields = ("complete_time_from", "complete_time_to", "user_id", "created_from", "created_to")
        # fields = ("created_from", "created_to")


class OrdersReportByProductFilterset(django_filters.FilterSet):
    complete_time_from = django_filters.DateFilter(field_name="complete_time__date", lookup_expr="gte")
    complete_time_to = django_filters.DateFilter(field_name="complete_time__date", lookup_expr="lte")

    province = django_filters.ModelMultipleChoiceFilter(
        field_name="address_shipping__ward__district__province__label", queryset=Provinces.objects.all(), label="province"
    )

    product = django_filters.ModelMultipleChoiceFilter(
        field_name="line_items__variant__product__name", queryset=Products.objects.all(), label="product"
    )

    class Meta:
        model = Orders
        fields = ("complete_time_from", "complete_time_to", "province", "product")


