import django_filters.rest_framework as django_filters
from django.db import models
from django.db.models import Q
from django_filters.conf import settings
from django_filters.filterset import remote_queryset
from rest_framework import exceptions

from customers.enums import CustomerGender
from customers.enums import CustomerRank
from customers.models import Customer


class CustomerFilterSet(django_filters.FilterSet):
    email = django_filters.CharFilter(field_name="email")
    gender = django_filters.MultipleChoiceFilter(choices=CustomerGender.choices())
    ranking = django_filters.MultipleChoiceFilter(choices=CustomerRank.choices())

    birthday_from = django_filters.CharFilter(method="filter_birthday_from", required=False)
    birthday_to = django_filters.CharFilter(method="filter_birthday_to", required=False)
    last_order_time_from = django_filters.DateTimeFilter(field_name="last_order_time__date", lookup_expr="gte")
    last_order_time_to = django_filters.DateTimeFilter(field_name="last_order_time__date", lookup_expr="lte")
    created_from = django_filters.DateFilter(field_name="created__date", lookup_expr="gte")
    created_to = django_filters.DateFilter(field_name="created__date", lookup_expr="lte")

    class Meta:
        model = Customer
        fields = [
            "created_by",
            "modified_by",
            "customer_care_staff",
            "modified_care_staff_by",
            "tags",
            "groups",
            "email",
            "gender",
            "ranking",
            "last_order_time_from",
            "last_order_time_to",
            # 'created_from',
            # 'created_to',
        ]
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

    def filter_birthday_from(self, queryset, name, value):
        if value:
            parts = value.split("-")
            if len(parts) != 2:
                raise exceptions.ValidationError("Ngày tháng phải có định dạng MM-DD")

            month, day = parts
            if not (month.isdigit() and day.isdigit()):
                raise exceptions.ValidationError("Ngày tháng phải là số")

            month, day = int(month), int(day)

            if month < 1 or month > 12 or day < 1 or day > 31:
                raise exceptions.ValidationError("Ngày tháng không hợp lệ")

            return queryset.filter(Q(birthday__month=month, birthday__day__gte=day) | Q(birthday__month__gt=month))
        return queryset

    def filter_birthday_to(self, queryset, name, value):
        if value:
            parts = value.split("-")
            if len(parts) != 2:
                raise exceptions.ValidationError("Ngày tháng phải có định dạng MM-DD")

            month, day = parts
            if not (month.isdigit() and day.isdigit()):
                raise exceptions.ValidationError("Ngày tháng phải là số")

            month, day = int(month), int(day)

            if month < 1 or month > 12 or day < 1 or day > 31:
                raise exceptions.ValidationError("Ngày hoặc tháng không hợp lệ")

            return queryset.filter(Q(birthday__month=month, birthday__day__lte=day) | Q(birthday__month__lt=month))
        return queryset

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self.form, "cleaned_data"):
            print(f"Applying filters with values: {self.form.cleaned_data}")
        else:
            print(f"Applying filters with initial values: {self.form.data}")


class CustomerHistoryFilterSet(django_filters.FilterSet):
    customer_id = django_filters.CharFilter(field_name="id", lookup_expr="exact")

    class Meta:
        model = Customer.history.model
        fields = ["customer_id"]
