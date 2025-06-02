from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.validators import UniqueValidator

from core.validators import PhoneValidator
from customers.models import Customer
from customers.models import CustomerGroup
from customers.models import CustomerGroupDetail
from customers.models import CustomerPhone
from customers.models import CustomerRank
from customers.models import CustomerTag
from customers.models import CustomerTagDetail
from locations.api.serializers import AddressSerializer
from users.models import User


class CustomerTagSerizalizer(serializers.ModelSerializer):
    class Meta:
        model = CustomerTag
        fields = "__all__"


class CustomerTagDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerTagDetail
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=CustomerTagDetail.objects.all(),
                fields=["customer_tag", "customer"],
                message="Tag has been attached",
            )
        ]


class CustomerGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerGroup
        fields = "__all__"


class BulkAddCustomersToGroupSerializer(serializers.Serializer):
    customers = serializers.PrimaryKeyRelatedField(many=True, queryset=Customer.objects.all())
    group = serializers.PrimaryKeyRelatedField(many=False, queryset=CustomerGroup.objects.all())


class CustomerGroupMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerGroupDetail
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=CustomerGroupDetail.objects.all(),
                fields=["customer_group", "customer"],
                message="Customer is already a member of the group",
            )
        ]


class CustomerPhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerPhone
        fields = "__all__"


class CustomerSerializer(serializers.ModelSerializer):
    tags = CustomerTagSerizalizer(many=True, read_only=True)
    groups = CustomerGroupSerializer(many=True, read_only=True)
    phones = CustomerPhoneSerializer(many=True, read_only=True)
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = "__all__"
        extra_kwargs = {
            "ranking": {"read_only": True},
            "latest_up_rank_date": {"read_only": True},
            "total_order": {"read_only": True},
            "total_spent": {"read_only": True},
            "last_order_id": {"read_only": True},
            "last_order_time": {"read_only": True},
            "last_shipping_completed": {"read_only": True},
            "care_start_time": {"read_only": True},
        }

class VariantCustomerSerializer(serializers.ModelSerializer):
    phones = CustomerPhoneSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = ("id", "name", "phones")

    def process_order_item(self, orders, order_items, order, total_amount):
        total_variant = 0
        for item in order_items:
            total_variant += item.quantity
            total_amount += item.price_total_input
        orders.append({
            "id": order.id,
            "created": order.created,
            "complete_time": order.complete_time,
            "order_key": order.order_key,
            "total_variant": total_variant,
        })
        return total_amount

    def to_representation(self, instance):
        data = super().to_representation(instance)
        orders = []
        total_amount = 0
        for order in instance.orders.all():
            order_items = order.order_items
            if order_items:
                total_amount = self.process_order_item(orders, order_items, order, total_amount)
                
        data["orders"] = orders
        data["total_amount"] = total_amount
        return data


class CustomerCareStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "name", "phone", "email")


class CustomerBaseInfo(serializers.ModelSerializer):
    phones = CustomerPhoneSerializer(many=True, read_only=True)
    customer_care_staff = CustomerCareStaffSerializer(read_only=True)

    class Meta:
        model = Customer
        fields = ("id", "name", "email", "birthday", "gender", "ranking", "phones", "customer_care_staff")


class CustomerHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer.history.model
        fields = "__all__"


class CustomerCreateSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(
        required=True, write_only=True, validators=[PhoneValidator(), UniqueValidator(CustomerPhone.objects.all())]
    )
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=CustomerTag.objects.all(), required=False)
    groups = serializers.PrimaryKeyRelatedField(many=True, queryset=CustomerGroup.objects.all(), required=False)
    rank_name = serializers.SerializerMethodField()

    def get_rank_name(self, obj):
        if obj.rank:
            return obj.rank.name_rank
        return None

    def create(self, validated_data):
        phone = validated_data.pop("phone")
        tags = validated_data.pop("tags", [])
        groups = validated_data.pop("groups", [])
        customer = Customer.objects.create(**validated_data)
        for tag in tags:
            customer.tags.add(tag)
        for group in groups:
            customer.groups.add(group)
        CustomerPhone.objects.create(customer=customer, phone=phone)
        return customer

    class Meta:
        model = Customer
        exclude = (
            "ranking",
            "latest_up_rank_date",
            "total_order",
            "total_spent",
            "last_order_id",
            "last_order_time",
            "last_shipping_completed",
            "care_start_time",
        )


class CustomerUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=CustomerTag.objects.all(), required=False)
    groups = serializers.PrimaryKeyRelatedField(many=True, queryset=CustomerGroup.objects.all(), required=False)
    rank_name = serializers.SerializerMethodField()

    def get_rank_name(self, obj):
        if obj.rank:
            return obj.rank.name_rank
        return None

    def update(self, instance, validated_data):
        if "tags" in validated_data:
            tags = validated_data.pop("tags", [])
            tag_ids = [str(tag.id) for tag in tags]
            for tag in tags:
                instance.tags.add(tag)
            for tag in instance.tags.all():
                if str(tag.id) not in tag_ids:
                    instance.tags.remove(tag)

        groups = validated_data.pop("groups", [])

        for group in groups:
            instance.groups.add(group)

        instance = super().update(instance, validated_data)
        return instance

    class Meta:
        model = Customer
        exclude = (
            "ranking",
            "latest_up_rank_date",
            "total_order",
            "total_spent",
            "last_order_id",
            "last_order_time",
            "last_shipping_completed",
            "care_start_time",
        )


class CustomerRankSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerRank
        fields = "__all__"
