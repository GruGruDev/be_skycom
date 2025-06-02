import django_filters.rest_framework as django_filters

from files.models import Images
from files.models import ImageTypes


class ImagesFilterset(django_filters.FilterSet):
    upload_by = django_filters.UUIDFilter()
    type = django_filters.MultipleChoiceFilter(choices=ImageTypes.choices())
    user = django_filters.UUIDFilter()
    product = django_filters.UUIDFilter()
    product_variant = django_filters.UUIDFilter()

    class Meta:
        model = Images
        fields = ["upload_by", "type", "user", "product", "product_variant"]
