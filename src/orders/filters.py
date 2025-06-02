import django_filters.rest_framework as django_filters
from django.core.exceptions import ValidationError
from django_filters.fields import MultipleChoiceField

from orders.models import ConfirmationSheetLog


class EnhanceMultipleChoiceField(MultipleChoiceField):
    def validate(self, value):
        """Validate that the input is a list or tuple."""
        if self.required and not value:
            raise ValidationError(self.error_messages["required"], code="required")


class EnhanceMultipleChoiceFilter(django_filters.filters.MultipleChoiceFilter):
    field_class = EnhanceMultipleChoiceField


class ConfirmationLogFilter(django_filters.FilterSet):
    turn_number = EnhanceMultipleChoiceFilter(field_name="turn_number", lookup_expr="exact")
    order_number = django_filters.CharFilter(field_name="order_key", lookup_expr="gte")
    order_key = django_filters.CharFilter(field_name="order_key", lookup_expr="gte")
    scan_by = EnhanceMultipleChoiceFilter(field_name="scan_by__id", lookup_expr="exact")
    scan_at_from = django_filters.CharFilter(field_name="scan_at", lookup_expr="gte")
    scan_at_to = django_filters.CharFilter(field_name="scan_at", lookup_expr="lte")
    is_success = django_filters.BooleanFilter(field_name="is_success")

    class Meta:
        model = ConfirmationSheetLog
        fields = [
            "turn_number",
            "order_number",
            "order_key",
            "scan_by",
            "scan_at_from",
            "scan_at_to",
            "is_success",
        ]