# pylint: disable=C0302
import ast

from django.utils import timezone
from rest_framework import serializers

from customers.api.serializers import CustomerBaseInfo
from customers.models import Customer

from files.api.serializers import ImagesReadBaseSerializer
from files.models import Images
from leads.api.serializers import LeadChannelSerializer
from leads.models.attributes import LeadChannel
from locations.api.serializers import AddressSerializer
from locations.models import Address
from orders.enums import OrderStatus
from orders.enums import WarehouseSheetType
from orders.models import ConfirmationSheetLog
from orders.models import Orders
from orders.models import OrdersCancelReason
from orders.models import OrdersType
from orders.models import OrdersItems
from orders.models import OrdersItemsCombo
from orders.models import OrdersItemsPromotion
from orders.models import OrdersPayments
from orders.models import OrdersPromotion
from orders.models import OrdersTag
from orders.models import OrderVariantsPromotion
from orders.reports import OrdersReportPivot
from products.api.serializers import ProductVariantRetrieveSerializer
from products.enums import ProductVariantStatus
from products.enums import ProductVariantType
from products.models import ProductsVariants
from promotions.api.serializers.promotion_orders import PromotionOrderReadOneSerializer
from promotions.api.serializers.promotion_variants import PromotionVariantReadOnceSerializer
from promotions.enums import PromotionStatus
from promotions.enums import PromotionVariantType
from promotions.models import PromotionOrder
from promotions.models import PromotionVariant
from users.api.serializers import UserReadBaseInfoSerializer
from utils.reports import BindingExprEnum
from warehouses.models import WarehouseSheetImportExport


class OrdersPaymentsHistorySerializer(serializers.ModelSerializer):
    modified_by = UserReadBaseInfoSerializer()

    class Meta:
        model = OrdersPayments.history.model
        fields = "__all__"


class OrdersPaymentsSerialzier(serializers.ModelSerializer):
    images = ImagesReadBaseSerializer(many=True)

    class Meta:
        model = OrdersPayments
        fields = "__all__"
        extra_kwargs = {
            "created": {"read_only": True},
            "modified": {"read_only": True},
        }


class OrdersPaymentsUpdateSerializer(serializers.ModelSerializer):
    image_id = serializers.UUIDField(required=False)

    class Meta:
        model = OrdersPayments
        fields = ("is_confirm", "note", "image_id")

    def update(self, instance, validated_data):
        request = self.context.get("request")
        instance.modified_by = request.user
        if not instance.date_confirm and validated_data.get("is_confirm", False):
            instance.date_confirm = timezone.now()

        image_id = validated_data.pop("image_id", None)

        # Cập nhật payment_id cho tất cả các Image có id trong danh sách image_id
        if image_id:
            Images.objects.filter(id=image_id).update(payment_id=instance.id)

        return super().update(instance, validated_data)


class OrdersPaymentsReadDetailSerializer(serializers.ModelSerializer):
    created_by = UserReadBaseInfoSerializer()
    modified_by = UserReadBaseInfoSerializer(required=False)
    history = OrdersPaymentsHistorySerializer(many=True)
    images = ImagesReadBaseSerializer(many=True)

    class Meta:
        model = OrdersPayments
        fields = "__all__"


class OrdersPaymentsCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdersPayments
        fields = (
            "type",
            "price_from_order",
            "price_from_third_party",
            "date_from_third_party",
            "price_from_upload_file",
            "date_from_upload_file",
            "is_confirm",
            "note",
        )


class OrdersPaymentsAuditFileSerializer(serializers.Serializer):
    file = serializers.FileField(allow_empty_file=False, required=True)
    image = serializers.FileField(allow_empty_file=False, required=False)

    def validate_file(self, file):
        TYPE_SUPPORTED = ["xlsx", "xls"]
        MAX_SIZE = 25000000  # byte = 25Mb
        if file.name.split(".")[-1] not in TYPE_SUPPORTED:
            raise serializers.ValidationError(f"File type not support. Support {TYPE_SUPPORTED}")
        if file.size > MAX_SIZE:
            raise serializers.ValidationError(f"File is large. Max size is {MAX_SIZE / 1000000}Mb")
        return file


class OrdersPromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdersPromotion
        fields = "__all__"
        extra_kwargs = {
            "created": {"read_only": True},
            "modified": {"read_only": True},
        }


class OrdersPromotionCreateSerializer(serializers.ModelSerializer):
    promotion_order_id = serializers.PrimaryKeyRelatedField(
        queryset=PromotionOrder.objects.filter(is_soft_delete=False, status=PromotionStatus.IN_PROGRESS.value), required=True
    )

    class Meta:
        model = OrdersPromotion
        fields = ("promotion_order_id", "price")


class OrdersPromotionReadListSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdersPromotion
        fields = "__all__"


class OrdersPromotionReadDetailSerializer(serializers.ModelSerializer):
    promotion_order = PromotionOrderReadOneSerializer()

    class Meta:
        model = OrdersPromotion
        fields = "__all__"


class OrdersItemsPromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdersItemsPromotion
        fields = "__all__"
        extra_kwargs = {
            "created": {"read_only": True},
            "modified": {"read_only": True},
        }


class OrdersItemsPromotionReadDetailSerializer(serializers.ModelSerializer):
    created_by = UserReadBaseInfoSerializer()
    modified_by = UserReadBaseInfoSerializer()
    variant = ProductVariantRetrieveSerializer()

    class Meta:
        model = OrdersItemsPromotion
        fields = "__all__"


class OrdersItemsPromotionCreateSerializer(serializers.ModelSerializer):
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductsVariants.objects.filter(status=ProductVariantStatus.ACTIVE.value, type=ProductVariantType.SIMPLE.value)
    )

    class Meta:
        model = OrdersItemsPromotion
        fields = ("variant_id", "quantity", "price", "total")


class OrdersVariantsPromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderVariantsPromotion
        fields = "__all__"
        extra_kwargs = {
            "created": {"read_only": True},
            "modified": {"read_only": True},
        }


class OrdersVariantsPromotionReadDetailSerializer(serializers.ModelSerializer):
    created_by = UserReadBaseInfoSerializer()
    modified_by = UserReadBaseInfoSerializer()
    promotion_variant = PromotionVariantReadOnceSerializer()
    items_promotion = OrdersItemsPromotionReadDetailSerializer(many=True)

    class Meta:
        model = OrderVariantsPromotion
        fields = "__all__"


class OrdersVariantsPromotionsCreateSerializer(serializers.ModelSerializer):
    items_promotion = OrdersItemsPromotionCreateSerializer(many=True, required=False)
    promotion_variant_id = serializers.PrimaryKeyRelatedField(
        queryset=PromotionVariant.objects.filter(status=PromotionStatus.IN_PROGRESS.value, is_soft_delete=False)
    )

    class Meta:
        model = OrderVariantsPromotion
        fields = ("promotion_variant_id", "price", "items_promotion")
        extra_kwargs = {"promotion_variant": {"required": True}}


class OrdersItemsComboSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdersItemsCombo
        fields = "__all__"
        extra_kwargs = {
            "created": {"read_only": True},
            "modified": {"read_only": True},
        }


class OrdersItemsComboCreateSerializer(serializers.ModelSerializer):
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductsVariants.objects.filter(status=ProductVariantStatus.ACTIVE.value, type=ProductVariantType.SIMPLE)
    )

    class Meta:
        model = OrdersItemsCombo
        fields = ("variant_id", "quantity", "price", "total")


class OrdersItemsComboReadDetailSerializer(serializers.ModelSerializer):
    created_by = UserReadBaseInfoSerializer()
    modified_by = UserReadBaseInfoSerializer()
    variant = ProductVariantRetrieveSerializer()

    class Meta:
        model = OrdersItemsCombo
        fields = "__all__"


class OrdersItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdersItems
        fields = "__all__"
        extra_kwargs = {
            "created": {"read_only": True},
            "modified": {"read_only": True},
        }


class OrdersItemsReadDetailSerializer(serializers.ModelSerializer):
    created_by = UserReadBaseInfoSerializer()
    modified_by = UserReadBaseInfoSerializer()
    variant = ProductVariantRetrieveSerializer()
    promotions = OrdersVariantsPromotionReadDetailSerializer(source="variant_promotions_used", many=True)
    items_combo = OrdersItemsComboReadDetailSerializer(many=True)

    class Meta:
        model = OrdersItems
        fields = "__all__"


class OrdersItemsCreateSerializer(serializers.ModelSerializer):
    promotions = OrdersVariantsPromotionsCreateSerializer(many=True, required=False)
    items_combo = OrdersItemsComboCreateSerializer(many=True, required=False)
    variant_id = serializers.PrimaryKeyRelatedField(queryset=ProductsVariants.objects.filter(status=ProductVariantStatus.ACTIVE.value))
    is_promo_sale = serializers.BooleanField(default=False)

    class Meta:
        model = OrdersItems
        fields = (
            "variant_id",
            "quantity",
            "price_variant_logs",
            "discount",
            "is_promo_sale",
            "price_total",
            "price_total_input",
            "price_total_neo",
            "sales_bonus",
            "third_party_item_id",
            "third_party_source",
            "is_cross_sale",
            "type_data_flow",
            "promotions",
            "items_combo",
            "commission_discount",
        )

    # pylint: disable=R0912
    def validate(self, attrs):
        variant: ProductsVariants = attrs.get("variant_id")
        quantity: int = attrs.get("quantity")
        total_price_promotion = 0
        promotion_variant_ids = []
        # Cho phép tổng giá bán nhập vào nhỏ hơn giá bán của sản phẩm
        if (not attrs["is_promo_sale"]) and (attrs.get("price_total") < (variant.sale_price or 0) * quantity):
            raise serializers.ValidationError({"variant_id": variant.id, "message": "Tổng giá của line item chưa đúng"})
        # Áp dụng khuyến mãi
        for promotion in attrs.get("promotions", []):
            promotion_variant = promotion.get("promotion_variant_id")
            # Khuyến mãi sử dụng nhiều lần
            if promotion_variant.id in promotion_variant_ids:
                raise serializers.ValidationError(
                    {
                        "promotions": [
                            {
                                "promotion_variant_id": promotion_variant.id,
                                "message": "Khuyến mãi không thể áp dụng nhiều lần trên một đơn hàng",
                            }
                        ]
                    }
                )
            # Khuyến mãi không phải của variant
            if promotion_variant.variant.id != variant.id:
                raise serializers.ValidationError(
                    {
                        "promotions": [
                            {"promotion_variant_id": promotion_variant.id, "message": "Khuyến mãi không thể áp dụng cho sản phẩm này"}
                        ]
                    }
                )
            # Line item không đủ điều kiện để áp dụng khuyến mãi
            if promotion_variant.requirement_min_total_quantity_variant_apply and (
                promotion_variant.requirement_min_total_quantity_variant_apply > attrs.get("quantity")
            ):
                raise serializers.ValidationError(
                    {
                        "variant_promotions": [
                            {
                                "promotion_variant_id": promotion_variant.id,
                                "message": "Số lượng sản phẩm mua tối thiểu là "
                                + f"{promotion_variant.requirement_min_total_quantity_variant_apply}",
                            }
                        ]
                    }
                )
            # Trường hợp khuyến mãi theo số tiền
            if (promotion_variant.type == PromotionVariantType.PRICE.value) and (promotion_variant.price_value != promotion.get("price")):
                raise serializers.ValidationError(
                    {
                        "promotions": [
                            {
                                "promotion_variant_id": promotion_variant.id,
                                "message": "Số tiền giảm phải bằng giá trị quy định của khuyến mãi",
                            }
                        ]
                    }
                )
            # Trường hợp khuyến mãi theo phần trăm
            if promotion_variant.type == PromotionVariantType.PERCENT.value:
                _discount_prom = attrs.get("price_total") / 100 * promotion_variant.percent_value
                _discount_prom = (
                    _discount_prom
                    if _discount_prom < promotion_variant.requirement_maximum_value_discount
                    else promotion_variant.requirement_maximum_value_discount
                )
                if _discount_prom != promotion.get("price"):
                    raise serializers.ValidationError(
                        {
                            "promotions": [
                                {
                                    "promotion_variant_id": promotion_variant.id,
                                    "message": "Số tiền giảm của khuyến mãi giảm theo phần trăm phải tính theo giá trị "
                                    + "của line item hoặc bằng giá trị tối đa nếu vượt quá",
                                }
                            ]
                        }
                    )
            # Trường hợp khuyến mãi tặng kèm sản phẩm
            if promotion_variant.type == PromotionVariantType.OTHER_VARIANT.value:
                items_promotion = promotion.get("items_promotion")
                total_quantity_gift = 0
                # Chưa chọn sản phẩm tặng
                if not items_promotion:
                    raise serializers.ValidationError(
                        {"promotions": [{"promotion_variant_id": promotion_variant.id, "message": "Chưa chọn sản phẩm tặng kèm"}]}
                    )
                # Các sản phẩm được tặng
                for item in items_promotion:
                    promotion_variant_other = promotion_variant.promotion_variant_other_variant.filter(
                        variant_id=item.get("variant_id")
                    ).first()
                    # Sản phẩm tặng đã chọn không nằm trong danh sách khuyến mãi
                    if not promotion_variant_other:
                        raise serializers.ValidationError(
                            {
                                "promotions": [
                                    {
                                        "promotion_variant_id": promotion_variant.id,
                                        "message": "Sản phẩm tặng kèm đã chọn không nằm trong danh sách khuyến mãi áp dụng",
                                    }
                                ]
                            }
                        )
                    if item.get("quantity") > promotion_variant_other.requirement_max_quantity:
                        raise serializers.ValidationError(
                            {
                                "promotions": [
                                    {"promotion_variant_id": promotion_variant.id, "message": "Sản phẩm tặng kèm vượt quá số lượng tối đa"}
                                ]
                            }
                        )
                    total_quantity_gift += item.get("quantity")
                if promotion_variant.requirement_max_total_quantity_variant and (
                    total_quantity_gift > promotion_variant.requirement_max_total_quantity_variant
                ):
                    raise serializers.ValidationError(
                        {"promotions": [{"promotion_variant_id": promotion_variant.id, "message": "Tổng số sản phẩm tặng kèm vượt tối đa"}]}
                    )
            total_price_promotion += promotion.get("price")
            promotion_variant_ids.append(promotion_variant.id)
        # Sản phẩm combo
        if variant.type != ProductVariantType.SIMPLE:
            if not attrs.get("items_combo"):
                raise serializers.ValidationError(
                    {
                        "items_combo": [
                            {
                                "message": "Chưa có thông tin sản phẩm của combo/bundle",
                            }
                        ]
                    }
                )
            for item in attrs.get("items_combo"):
                variant_item = item.get("variant_id")
                variant_combo_detail = variant.combo_variants.filter(detail_variant_id=variant_item.id).first()
                if not variant_combo_detail:
                    raise serializers.ValidationError(
                        {
                            "items_combo": [
                                {
                                    "variant_id": variant_item.id,
                                    "message": "Sản phẩm không nằm trong combo/bundle",
                                }
                            ]
                        }
                    )
        # Giá trị khuyến mãi
        if total_price_promotion != attrs.get("discount"):
            raise serializers.ValidationError({"discount": "Số tiền giảm phải bằng số tiền giảm từ các khuyến mãi"})
        # Tính giá NEO và chiết khấu đơn hàng
        attrs.update({"price_total_neo": (variant.neo_price or 0) * quantity, "sales_bonus": (variant.sales_bonus or 0) * quantity})

        if variant.commission:
            attrs["commission_discount"] = variant.commission * quantity
        elif variant.commission_percent:
            attrs["commission_discount"] = (attrs.get("price_total_input") or attrs.get("price_total", 0)) * (variant.commission_percent / 100)
        return super().validate(attrs)


class OrdersTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdersTag
        fields = "__all__"
        extra_kwargs = {
            "created": {"read_only": True},
            "modified": {"read_only": True},
        }


class OrdersCancelReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdersCancelReason
        fields = "__all__"


class OrdersTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdersType
        fields = ("id", "name")


class OrdersSerializer(serializers.ModelSerializer):
    order_key = serializers.ReadOnlyField()

    class Meta:
        model = Orders
        fields = "__all__"
        extra_kwargs = {
            "created": {"read_only": True},
            "modified": {"read_only": True},
        }


class OrdersCreateSerializer(serializers.ModelSerializer):
    payments = OrdersPaymentsCreateSerializer(many=True, required=False)
    promotions = OrdersPromotionCreateSerializer(many=True, required=False)
    line_items = OrdersItemsCreateSerializer(many=True, required=True)
    customer = serializers.PrimaryKeyRelatedField(source="customer_id", queryset=Customer.objects.all(), required=True)
    address_shipping = serializers.PrimaryKeyRelatedField(source="address_shipping_id", queryset=Address.objects.all(), required=False)
    source = serializers.PrimaryKeyRelatedField(source="source_id", queryset=LeadChannel.objects.all(), required=False)
    type_id = serializers.UUIDField(required=False)
    
    class Meta:
        model = Orders
        fields = (
            "sale_note",
            "delivery_note",
            "status",
            "customer",
            "phone_shipping",
            "name_shipping",
            "address_shipping",
            "third_party_id",
            "third_party_name",
            "third_party_type",
            "is_cross_sale",
            "value_cross_sale",
            "appointment_date",
            # "quatity_total_variant_all",
            "price_total_variant_all",
            "price_total_variant_all_neo",
            "price_total_variant_actual",
            "price_total_variant_actual_input",
            "price_total_discount_order_promotion",
            "price_discount_input",
            "price_addition_input",
            "price_delivery_input",
            "price_total_order_actual",
            "price_pre_paid",
            "price_after_paid",
            "tags",
            "source",
            "cancel_reason",
            "payments",
            "promotions",
            "line_items",
            "type_id",
            "date_shipping",
        )
        extra_kwargs = {
            "price_total_variant_all": {"required": True},
            "price_total_variant_actual": {"required": True},
            "price_total_variant_actual_input": {"required": True},
            "price_total_discount_order_promotion": {"required": True},
            "price_discount_input": {"required": True},
            "price_addition_input": {"required": True},
            "price_total_order_actual": {"required": True},
            "price_pre_paid": {"required": True},
            "price_after_paid": {"required": True},
        }

    def validate_payments(self, payments):
        price_total_order_actual = self.initial_data.get("price_total_order_actual")
        type_payments = [payment.get("type") for payment in payments]
        # Trùng loại thanh toán
        if len(type_payments) != len(set(type_payments)):
            raise serializers.ValidationError("Không thể có nhiều phiếu thanh toán cùng loại trên một đơn hàng")

        total_payments = sum(payment.get("price_from_order") for payment in payments)
        # Tổng số tiền phải thanh toán
        if total_payments != price_total_order_actual:
            raise serializers.ValidationError(
                f"Tổng số tiền thanh toán({total_payments}) phải bằng giá cuối của đơn hàng({price_total_order_actual})"
            )
        return payments

    def validate_promotions(self, promotions):
        price_total_variant_actual = self.initial_data.get("price_total_variant_actual")
        promotion_ids = []
        for promotion in promotions:
            promotion_order = promotion.get("promotion_order_id")
            rq_min_total_order_apply = promotion_order.requirement_min_total_order_apply
            # Giá trị đơn hàng tối thiểu để sử dụng khuyến mãi
            if rq_min_total_order_apply and rq_min_total_order_apply > price_total_variant_actual:
                raise serializers.ValidationError(
                    {
                        "promotion_id": promotion_order.id,
                        "message": f"Đơn hàng chưa đạt giá trị tối thiểu({rq_min_total_order_apply}) để sử dụng khuyến mãi",
                    }
                )
            # Khuyến mãi sử dụng nhiều lần trên 1 đơn hàng
            if str(promotion_order.id) in promotion_ids:
                raise serializers.ValidationError(
                    {
                        "promotion_id": promotion_order.id,
                        "message": f"Không thể sử dụng khuyến mãi 2 lần trên đơn hàng. {promotion_order.id}",
                    }
                )
            # Số tiền được giảm vượt quá mức tối đa của khuyến mãi
            if promotion_order.requirement_maximum_value_discount and (
                promotion_order.requirement_maximum_value_discount < promotion.get("price")
            ):
                raise serializers.ValidationError(
                    {
                        "promotion_order_id": promotion_order.id,
                        "message": f"Số tiền được giảm vượt quá giá trị tối đa({promotion_order.requirement_maximum_value_discount})",
                    }
                )
            promotion_ids.append(str(promotion_order.id))
        return promotions

    def validate(self, attrs):
        _price_total_variant_all = 0
        _price_total_variant_actual = 0
        _price_total_variant_all_neo = 0
        promotions = attrs.get("promotions") or []
        _price_total_discount_order_promotion = sum(promo.get("price", 0) for promo in promotions)
        for line in attrs.get("line_items"):
            _price_total_variant_all += line.get("price_total")
            _price_total_variant_actual += line.get("price_total") - line.get("discount", 0)
            _price_total_variant_all_neo += line.get("price_total_neo")
        if _price_total_variant_all != attrs.get("price_total_variant_all"):
            raise serializers.ValidationError({"price_total_variant_all": ["Tổng giá trị đơn hàng phải bằng tổng giá trị các line items"]})
        if _price_total_variant_actual != attrs.get("price_total_variant_actual"):
            raise serializers.ValidationError({"price_total_variant_actual": ["Tổng giá trị các items đã giảm không đúng"]})
        if _price_total_discount_order_promotion != attrs.get("price_total_discount_order_promotion"):
            raise serializers.ValidationError(
                {"price_total_discount_order_promotion": ["Tổng giá trị giảm từ tất cả khuyến mãi trên đơn chưa đúng"]}
            )
        price_discount_input = attrs.get("price_discount_input", 0)
        price_addition_input = attrs.get("price_addition_input", 0)
        price_delivery_input = attrs.get("price_delivery_input", 0)
        _price_total_order_actual = (
            _price_total_variant_actual
            - (price_discount_input + _price_total_discount_order_promotion)
            + price_addition_input
            + price_delivery_input
        )
        # if _price_total_order_actual != attrs.get("price_total_order_actual"):
        # raise serializers.ValidationError({"price_total_order_actual": ["Giá trị cuối của đơn chưa đúng"]})
        # if (attrs.get("price_pre_paid", 0) + attrs.get("price_after_paid")) != _price_total_order_actual:
        if (attrs.get("price_pre_paid", 0) + attrs.get("price_after_paid")) != attrs.get("price_total_order_actual"):
            raise serializers.ValidationError(
                f"Tổng số tiền trả trước và trả sau phải bằng giá trị cuối của đơn hàng: {_price_total_order_actual}"
            )
        # Thêm thông tin giá trị NEO của các sản phẩm trong đơn
        attrs.update({"price_total_variant_all_neo": _price_total_variant_all_neo})
        return super().validate(attrs)


class OrdersUpdateSerializer(serializers.ModelSerializer):
    type_id = serializers.UUIDField(required=False)

    class Meta:
        model = Orders
        fields = (
            "sale_note",
            "delivery_note",
            "status",
            "is_cross_sale",
            "value_cross_sale",
            "phone_shipping",
            "name_shipping",
            "is_print",
            "third_party_id",
            "third_party_name",
            "third_party_type",
            "appointment_date",
            "tracking_number",
            "address_shipping",
            "source",
            "cancel_reason",
            "tags",
            "complete_by",
            "type_id",
            "date_shipping",
        )
        extra_kwargs = {
            "phone_shipping": {"required": False},
            "name_shipping": {"required": False},
        }

    def update(self, instance, validated_data):
        request = self.context.get("request")
        time_now = timezone.now()
        if not instance.is_print and validated_data.get("is_print", False):
            instance.printed_by = request.user
            instance.printed_at = time_now
        if not instance.complete_time and validated_data.get("status") == OrderStatus.COMPLETED:
            instance.customer.last_order_time = time_now
            instance.complete_time = time_now
            instance.complete_by = request.user
        instance.modified_by = request.user
        return super().update(instance, validated_data)


class WarehouseSheetImportExportReadBase(serializers.ModelSerializer):
    class Meta:
        model = WarehouseSheetImportExport
        fields = ("id", "code", "is_confirm")


class OrdersReadListSerializer(serializers.ModelSerializer):
    order_key = serializers.ReadOnlyField()
    customer = CustomerBaseInfo()
    address_shipping = AddressSerializer()
    cancel_reason = OrdersCancelReasonSerializer(required=False)
    source = LeadChannelSerializer(required=False)
    type = OrdersTypeSerializer(required=False)
    tags = OrdersTagsSerializer(many=True)
    payments = OrdersPaymentsSerialzier(many=True)
    sheet = WarehouseSheetImportExportReadBase(source="warehouse_sheet_import_export_order", many=True, read_only=True)

    class Meta:
        model = Orders
        fields = "__all__"


class OrdersReadLineItemsMobileSerializer(serializers.ModelSerializer):
    SKU_code = serializers.CharField(source="variant.SKU_code")
    name = serializers.CharField(source="variant.name")
    images = ImagesReadBaseSerializer(source="variant.images", many=True)

    class Meta:
        model = OrdersItems
        fields = ("SKU_code", "name", "quantity", "price_variant_logs", "price_total", "price_total_input", "images")


class OrdersReadListMobileSerializer(serializers.ModelSerializer):
    variants = OrdersReadLineItemsMobileSerializer(source="line_items", many=True)

    class Meta:
        model = Orders
        fields = ("id", "order_key", "status", "phone_shipping", "name_shipping", "created", "price_total_order_actual", "variants")


class OrdersReadDetailSerializer(serializers.ModelSerializer):
    order_key = serializers.ReadOnlyField()
    customer = CustomerBaseInfo()
    address_shipping = AddressSerializer()
    printed_by = UserReadBaseInfoSerializer(required=False)
    cancel_reason = OrdersCancelReasonSerializer(required=False)
    source = LeadChannelSerializer(required=False)
    type = OrdersTypeSerializer(required=False)
    tags = OrdersTagsSerializer(many=True)
    payments = OrdersPaymentsReadDetailSerializer(many=True)
    promotions = OrdersPromotionReadDetailSerializer(source="promotions_used", many=True)
    line_items = OrdersItemsReadDetailSerializer(many=True)
    images = ImagesReadBaseSerializer(many=True)

    class Meta:
        model = Orders
        fields = "__all__"


class OrdersHistorySerializer(serializers.ModelSerializer):
    created_by = UserReadBaseInfoSerializer()
    modified_by = UserReadBaseInfoSerializer()
    printed_by = UserReadBaseInfoSerializer()
    source = LeadChannelSerializer()
    cancel_reason = OrdersCancelReasonSerializer()
    address_shipping = AddressSerializer()

    class Meta:
        model = Orders.history.model
        fields = "__all__"


class OrdersReportPivotFilters(serializers.Serializer):
    dimensions = ""
    metrics = ""


class OrdersReportPivotParams(serializers.Serializer):
    dimensions = serializers.CharField(help_text=OrdersReportPivot.help_text_dims())
    metrics = serializers.CharField(help_text=OrdersReportPivot.help_text_metrics())
    filters = serializers.CharField(help_text=OrdersReportPivot.help_text_filters(), allow_null=True, required=False)
    b_expr_dims = serializers.ChoiceField(choices=BindingExprEnum.choices(), default=BindingExprEnum.AND, required=False)
    b_expr_metrics = serializers.ChoiceField(choices=BindingExprEnum.choices(), default=BindingExprEnum.AND, required=False)

    def validate_dimensions(self, value):
        try:
            value_list = ast.literal_eval(value)
            for v in value_list:
                if v not in OrdersReportPivot.DIMS_AVB:
                    raise ValueError("%s not implemented yet" % v)
            return value_list
        except (ValueError, Exception) as err:
            raise serializers.ValidationError("Dimensions invalid: %s" % str(err))

    def validate_metrics(self, value):
        try:
            value_list = ast.literal_eval(value)
            for v in value_list:
                if v not in OrdersReportPivot.METRICS_AVB:
                    raise ValueError("%s not implemented yet" % v)
            return value_list
        except (ValueError, Exception) as err:
            raise serializers.ValidationError("Metrics invalid: %s" % str(err))

    def validate_filters(self, value):
        try:
            return ast.literal_eval(value)
        except (ValueError, Exception) as err:
            raise serializers.ValidationError("Filters invalid: %s" % str(err))


class OrdersReportPivotCompareParams(OrdersReportPivotParams):
    created_from = serializers.DateField(required=True)
    created_to = serializers.DateField(required=True)
    created_from_cp = serializers.DateField(required=True)
    created_to_cp = serializers.DateField(required=True)

    def validate(self, values):
        days = values.get("created_to") - values.get("created_from")
        days_c = values.get("created_to_cp") - values.get("created_from_cp")
        if days != days_c:
            raise serializers.ValidationError(
                {
                    "created_from_cp": ["The comparison time must be similar to the original time"],
                    "created_to_cp": ["The comparison time must be similar to the original time"],
                }
            )
        return super().validate(values)


class ResultOrderPivotResponse(serializers.Serializer):
    created_date = serializers.DateField(help_text="Ngày cơm")
    source__id = serializers.UUIDField(help_text="ID kênh bán hàng")
    source__name = serializers.CharField(help_text="Tên kênh bán hàng")
    shipping_status = serializers.CharField(help_text="Trạng thái vận chuyển")
    status = serializers.CharField(help_text="Trạng thái đơn hàng")
    created_by__id = serializers.UUIDField(help_text="ID người tạo đơn hàng")
    created_by__name = serializers.CharField(help_text="Tên người tạo đơn")
    complete_by__id = serializers.UUIDField(help_text="ID người xác nhận")
    complete_by__name = serializers.CharField(help_text="Tên người tạo")
    complete_date = serializers.DateField(help_text="Ngày xác nhận")
    shipping_date = serializers.DateField(help_text="Ngày tạo vận đơn")
    province = serializers.CharField(help_text="Tỉnh thành")
    warehouse_exdate = serializers.DateField(help_text="Ngày xuất kho")
    revenue = serializers.FloatField(help_text="Doanh thu cuối của đơn hàng")
    pre_promo_revenue = serializers.FloatField(help_text="Tổng giá bán của sản phẩm trong đơn")
    after_promo_revenue = serializers.FloatField(help_text="Tổng giá bán của của sản phẩm sau khi áp dụng khuyến mãi cho sản phẩm")
    after_promo_revenue_input = serializers.FloatField(help_text="Tổng giá bán của của sản phẩm nhập tay")
    total_prod_discount = serializers.FloatField(help_text="Tổng giá trị khuyến mãi áp dụng cho sản phẩm")
    total_order_discount = serializers.FloatField(help_text="Tổng giá trị khuyến mãi áp dụng cho đơn hàng")

    total_order_quantity = serializers.FloatField(help_text="Tổng số lượng đơn hàng")
    total_prod_quantity = serializers.FloatField(help_text="Tổng số lượng sản phẩm trong các đơn hàng")
    total_gift_quantity = serializers.FloatField(help_text="Tổng số lượng sản phẩm đã tặng")
    total_addi_fee = serializers.FloatField(help_text="Tổng giá trị phụ thu")
    total_ship_fee = serializers.FloatField(help_text="Tổng giá trị phí ship")
    total_discount_input = serializers.FloatField(help_text="Tổng giá trị giảm do salers nhập")
    avg_order_value = serializers.FloatField(help_text="Trung bình giá trị đơn hàng")
    avg_items_count = serializers.FloatField(help_text="Trung bình số lượng sản phẩm trong đơn hàng")


class OrdersReportPivotResponse(serializers.Serializer):
    count = serializers.IntegerField()
    results = ResultOrderPivotResponse(many=True)


class ResultOrderPivotCompareResponse(ResultOrderPivotResponse):
    compare = ResultOrderPivotResponse(many=False)


class OrdersReportPivotCompareResponse(serializers.Serializer):
    count = serializers.IntegerField()
    results = ResultOrderPivotCompareResponse()


class OrderItemDetailReportSerializer(serializers.Serializer):
    pass


class OrderDetailReportSerializer(serializers.Serializer):
    pass


class OrderKPIReportSerializer(serializers.ModelSerializer):
    created_by__name = serializers.CharField(source="created_by.name")
    source__name = serializers.CharField(source="source.name")
    shipping__delivery_company_name = serializers.CharField(source="shipping.delivery_company_name")
    shipping__delivery_company_type = serializers.IntegerField(source="shipping.delivery_company_type")
    shipping__carrier_status = serializers.CharField(source="shipping.carrier_status")
    shipping__finish_date = serializers.CharField(source="shipping.finish_date")

    class Meta:
        model = Orders
        fields = (
            "id",
            "order_key",
            "created_by__name",
            "created",
            "modified",
            "source__name",
            "shipping__delivery_company_name",
            "shipping__delivery_company_type",
            "shipping__carrier_status",
            "shipping__finish_date",
            "phone_shipping",
            "name_shipping",
            "price_delivery_input",
            "price_addition_input",
            "complete_time",
            "price_total_order_actual",
        )


class OrderSheetConfirmSerializer(serializers.Serializer):
    order_key = serializers.CharField(max_length=16)
    sheet_type = serializers.ChoiceField(required=True, choices=[item.value for item in WarehouseSheetType])
    turn = serializers.IntegerField(required=True)


class ConfirmationLogSerializer(serializers.ModelSerializer):
    order_id = serializers.SerializerMethodField("get_order_id")

    class Meta:
        model = ConfirmationSheetLog
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["scan_by"] = UserReadBaseInfoSerializer(instance.scan_by).data
        return representation

    def get_order_id(self, obj):
        order = Orders.objects.filter(order_key=obj.order_key).first()

        if not order:
            return None

        return str(order.id)



