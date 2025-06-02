import django_filters.rest_framework as django_filters
from django.db import models
from django_filters.conf import settings
from django_filters.filterset import remote_queryset

from promotions.enums import PromotionOrderType
from promotions.enums import PromotionStatus
from promotions.enums import PromotionVariantType
from promotions.models import PromotionOrder
from promotions.models import PromotionVariant


class PromotionOrderFilterset(django_filters.FilterSet):
    created_from = django_filters.DateFilter(field_name="created__date", lookup_expr="gte")
    created_to = django_filters.DateFilter(field_name="created__date", lookup_expr="lte")
    status = django_filters.MultipleChoiceFilter(choices=PromotionStatus.choices())
    type = django_filters.MultipleChoiceFilter(choices=PromotionOrderType.choices())
    active_to_date = django_filters.DateFilter(field_name="requirement_time_expire__date", lookup_expr="lte")

    class Meta:
        model = PromotionOrder
        fields = (
            "created_by",
            "modified_by",
            "status",
            "type",
            "created_from",
            "created_to",
            "active_to_date",
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


class PromotionVariantFilterset(django_filters.FilterSet):
    created_from = django_filters.DateFilter(field_name="created__date", lookup_expr="gte")
    created_to = django_filters.DateFilter(field_name="created__date", lookup_expr="lte")
    status = django_filters.MultipleChoiceFilter(choices=PromotionStatus.choices())
    type = django_filters.MultipleChoiceFilter(choices=PromotionVariantType.choices())
    active_to_date = django_filters.DateFilter(field_name="requirement_time_expire__date", lookup_expr="lte")

    class Meta:
        model = PromotionVariant
        fields = (
            "created_by",
            "modified_by",
            "status",
            "type",
            "created_from",
            "created_to",
            "active_to_date",
            "variant",
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
