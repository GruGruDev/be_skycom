import django_filters.rest_framework as django_filters
from django.db import models
from django_filters.conf import settings
from django_filters.filterset import remote_queryset

from users.models import ACTION_TYPES
from users.models import User
from users.models import UserActionLog


class UserFilter(django_filters.FilterSet):
    # group = django_filters.ModelMultipleChoiceFilter(queryset=GroupUser.objects.all(), field_name="groups_participated")
    # group_name = django_filters.CharFilter(field_name="groups_participated__name", lookup_expr="exact")

    class Meta:
        model = User
        fields = [
            "is_assign_lead_campaign",
            "is_active",
            "is_superuser",
            "is_online",
            "is_exportdata",
            "is_CRM",
            "is_hotdata",
            "department",
            "role",
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


class UserActionLogFilter(django_filters.FilterSet):
    ACTION_NAME_CHOICES = [
        ("CUSTOMERS", "Quản lí khách hàng"),
        ("USERS", "Quản lí người dùng"),
        ("LOCATIONS", "Quản lí địa chỉ"),
        ("LEADS", "Quản lí lead"),
        ("PRODUCTS", "Quản lí sản phẩm"),
        ("PROMOTIONS", "Quản lí khuyến mãi"),
        ("WAREHOUSES", "Quản lí kho"),
        ("ORDERS", "Quản lí đơn hàng"),
        ("DELIVERY", "Quản lí vận chuyển"),
        ("FILES", "Quản lí file"),
        ("LOGIN", "Đăng nhập"),
        ("LOGOUT", "Đăng xuất"),
        ("EXPORT_FILE", "Xuất file"),
        ("IMPORT_FILE", "Nhập file"),
    ]
    action_time_from = django_filters.DateFilter(field_name="action_time__date", lookup_expr="gte")
    action_time_to = django_filters.DateFilter(field_name="action_time__date", lookup_expr="lte")
    action_name = django_filters.MultipleChoiceFilter(field_name="action_name", choices=ACTION_NAME_CHOICES)
    action_type = django_filters.MultipleChoiceFilter(field_name="action_type", choices=ACTION_TYPES)
    instance_name = django_filters.CharFilter(method="filter_instance_name")

    class Meta:
        model = UserActionLog
        fields = ["user", "status", "action_name", "action_time_from", "action_time_to"]

    def filter_instance_name(self, queryset, name, value):
        # Convert the value to lowercase before filtering
        value = value.lower()
        return queryset.filter(content_type__model=value)
