import django_filters.rest_framework as django_filters
from django.db.models.functions import ExtractMonth, ExtractDay
from django.db import transaction
from django.db.models import Q
from django.db.models import Prefetch
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework import mixins
from rest_framework import permissions
from rest_framework import response
from rest_framework import serializers
from rest_framework import status
from rest_framework import views
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.views import CustomModelViewSet
from customers.api.filters import CustomerFilterSet
from customers.api.filters import CustomerHistoryFilterSet
from customers.api.serializers import BulkAddCustomersToGroupSerializer
from customers.api.serializers import VariantCustomerSerializer
from customers.api.serializers import CustomerCreateSerializer
from customers.api.serializers import CustomerGroupMemberSerializer
from customers.api.serializers import CustomerGroupSerializer
from customers.api.serializers import CustomerHistorySerializer
from customers.api.serializers import CustomerPhoneSerializer
from customers.api.serializers import CustomerRankSerializer
from customers.api.serializers import CustomerSerializer
from customers.api.serializers import CustomerTagDetailSerializer
from customers.api.serializers import CustomerTagSerizalizer
from customers.api.serializers import CustomerUpdateSerializer
from customers.models import Customer
from customers.models import CustomerGroup
from customers.models import CustomerGroupDetail
from customers.models import CustomerPhone
from customers.models import CustomerRank
from customers.models import CustomerTag
from customers.models import CustomerTagDetail
from orders.models import OrdersItems
from users.activity_log import ActivityLogMixin


def update_customer_rank(customer):
    total_spent = customer.total_spent
    # total_order = customer.total_order
    highest_rank = CustomerRank.objects.order_by("-spend_to").first()
    if highest_rank and total_spent > highest_rank.spend_to:
        new_rank = highest_rank
    else:
        new_rank = CustomerRank.objects.filter(Q(spend_from__lte=total_spent) & Q(spend_to__gte=total_spent)).first()

    if new_rank and customer.rank != new_rank:
        customer.rank = new_rank
        customer.latest_up_rank_date = timezone.now()
        customer.save()


class CustomerTagView(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CustomerTagSerizalizer
    queryset = CustomerTag.objects.all()
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    )
    search_fields = ("name",)
    ordering_fields = "__all__"


class CustomerRankViewSet(viewsets.ModelViewSet):
    queryset = CustomerRank.objects.all()
    serializer_class = CustomerRankSerializer

    def create(self, request, *args, **kwargs):
        try:
            create_response = super().create(request, *args, **kwargs)
            return Response({"detail": "Thêm mới thành công", "data": create_response.data}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            update_response = super().update(request, *args, **kwargs)
            return Response({"detail": "Cập nhật thành công", "data": update_response.data}, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"detail": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CustomerTagDetailCreateDestroyView(mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CustomerTagDetailSerializer
    queryset = CustomerTagDetail.objects.all()


class CustomerGroupView(
    ActivityLogMixin, mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CustomerGroupSerializer
    queryset = CustomerGroup.objects.all()
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    )
    search_fields = ("name",)
    ordering_fields = "__all__"


class BulkAddUsersToGroupView(views.APIView):
    @swagger_auto_schema(request_body=BulkAddCustomersToGroupSerializer)
    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        serializer = BulkAddCustomersToGroupSerializer(data=request.data)
        if serializer.is_valid():
            customers = serializer.data.pop("customers", [])
            group = serializer.data.pop("group")
            for customer in customers:
                serializer_gr_member_dt = CustomerGroupMemberSerializer(data={"customer_group": group, "customer": customer})
                if serializer_gr_member_dt.is_valid():
                    serializer_gr_member_dt.save()
                else:
                    raise serializers.ValidationError(f"Customer({customer}) is already a member of the group({group})")
            return response.Response({"success"}, status=status.HTTP_201_CREATED)
        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BulkRemoveUsersGroupView(views.APIView):
    @swagger_auto_schema(request_body=BulkAddCustomersToGroupSerializer)
    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        serializer = BulkAddCustomersToGroupSerializer(data=request.data)
        if serializer.is_valid():
            customers = serializer.data.pop("customers", [])
            group = serializer.data.pop("group")
            CustomerGroupDetail.objects.filter(customer_group_id=group, customer_id__in=customers).delete()
            return response.Response({"status": "success"}, status=status.HTTP_201_CREATED)
        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerGroupMemberCreateDestroyView(ActivityLogMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CustomerGroupMemberSerializer
    queryset = CustomerGroupDetail.objects.all()


class CustomerPhoneCreateDestroyView(mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CustomerPhoneSerializer
    queryset = CustomerPhone.objects.all()
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    )
    search_fields = ("phone",)
    ordering_fields = "__all__"

    def perform_destroy(self, instance):
        if not self.queryset.filter(customer=instance.customer).exclude(phone=instance.phone).exists():
            raise serializers.ValidationError("This phone number cannot be deleted because it's unique of customer")
        return super().perform_destroy(instance)


class CustomerViewSet(CustomModelViewSet):
    serializer_class = CustomerSerializer
    serializer_classes = {"create": CustomerCreateSerializer, "partial_update": CustomerUpdateSerializer}
    queryset = Customer.objects.prefetch_related(
        "tags", "groups", "phones", "addresses", "addresses__ward", "addresses__ward__district", "addresses__ward__province"
    ).annotate(
        birthday_day=ExtractDay("birthday"),
        birthday_month=ExtractMonth("birthday"),
    ).all()
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    )
    filterset_class = CustomerFilterSet
    search_fields = ("name", "email", "phones__phone")
    ordering_fields = "__all__"

    def get_queryset(self):
        params = self.request.query_params
        if params.get("variant") and params.get("order_status"):
            return Customer.objects.filter(
                orders__line_items__variant_id=params.get("variant"),
                orders__status=params.get("order_status"),
            ).prefetch_related(
                "phones",
                Prefetch(
                    "orders__line_items",
                    queryset=OrdersItems.objects.filter(
                        variant_id=params.get("variant"), 
                        order__status=params.get("order_status"),
                    ),
                    to_attr="order_items"
                )
            ).distinct().all()

        return super().get_queryset()

    def get_serializer_class(self):
        params = self.request.query_params
        if params.get("variant") and params.get("order_status"):
            return VariantCustomerSerializer
        return self.serializer_classes.get(self.action, self.serializer_class)

    def perform_create(self, serializer):
        serializer.validated_data["created_by"] = self.request.user
        customer = serializer.save()
        update_customer_rank(customer)

        # return super().perform_create(serializer)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(CustomerSerializer(instance).data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.validated_data["modified_by"] = self.request.user
        serializer.save()
        update_customer_rank(serializer.instance)


class CustomerHistoryViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CustomerHistorySerializer
    queryset = Customer.history.all()
    filter_backends = (
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    )
    filterset_class = CustomerHistoryFilterSet
    ordering_fields = ("history_date",)
