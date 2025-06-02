import uuid

from django.db import models
from model_utils.models import TimeStampedModel
from model_utils.models import UUIDModel
from simple_history.models import HistoricalRecords

from customers.models import Customer
from leads.models.attributes import LeadChannel
from locations.models import Address
from orders.enums import OrderItemDataFlowType
from orders.enums import OrderPaymentType
from orders.enums import OrderStatus
from orders.enums import TransportationCareCreationReason
from orders.enums import TransportationCareStatus
from products.enums import ConfirmationLogType
from products.enums import ProductVariantType
from products.models import ProductsVariants
from promotions.enums import PromotionVariantType
from promotions.models import PromotionOrder
from promotions.models import PromotionVariant
from users.models import User


class OrdersTag(TimeStampedModel, UUIDModel):
    name = models.CharField(max_length=255, blank=False, null=False, unique=True)

    class Meta:
        db_table = "tbl_Orders_Tags"
        ordering = ["name"]


class OrdersCancelReason(TimeStampedModel, UUIDModel):
    name = models.CharField(max_length=255, blank=False, null=False, unique=True)

    class Meta:
        db_table = "tbl_Orders_Cancel_Reason"
        ordering = ["name"]


class OrdersType(TimeStampedModel, UUIDModel):
    name = models.CharField(max_length=255, blank=False, null=False, unique=True)

    class Meta:
        db_table = "tbl_Orders_Type"
        ordering = ["name"]


class Orders(TimeStampedModel):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, null=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="orders_created")
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="orders_modified")
    order_number = models.PositiveBigIntegerField(null=False, editable=False, unique=True)
    order_key = models.CharField(null=False, max_length=256, editable=False, unique=True)
    sale_note = models.TextField(null=True)
    delivery_note = models.TextField(null=True)
    status = models.CharField(max_length=9, choices=OrderStatus.choices(), default=OrderStatus.DRAFT.value)

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name="orders")
    phone_shipping = models.CharField(max_length=15, blank=False, null=True)
    name_shipping = models.CharField(max_length=255, blank=False, null=True)
    address_shipping = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name="orders")
    date_shipping = models.DateField(blank=True, null=True)

    is_print = models.BooleanField(default=False)
    printed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="orders_printed")
    printed_at = models.DateTimeField(null=True)
    third_party_id = models.CharField(max_length=255, null=True)
    third_party_name = models.CharField(max_length=255, null=True)
    third_party_type = models.CharField(max_length=255, null=True)
    is_cross_sale = models.BooleanField(default=False)
    value_cross_sale = models.PositiveBigIntegerField(default=0)
    appointment_date = models.DateTimeField(null=True)

    # Số lượng sản phẩm trong đơn hàng
    # quatity_total_variant_all = models.PositiveSmallIntegerField(default=0)
    # Tổng giá niêm yết của tất cả sản phẩm
    price_total_variant_all_neo = models.PositiveBigIntegerField(blank=False, null=True)
    # Tổng giá sản phẩm
    price_total_variant_all = models.PositiveBigIntegerField(default=0)
    # Tổng giá sản phẩm sau khi áp khuyến mãi cho SẢN PHẨM
    price_total_variant_actual = models.PositiveBigIntegerField(default=0)
    price_total_variant_actual_input = models.PositiveBigIntegerField(default=0)

    # Tổng số tiền được giảm khi áp khuyến mãi cho ĐƠN HÀNG
    price_total_discount_order_promotion = models.PositiveBigIntegerField(default=0)
    # Số tiền được giảm do salers nhập vào
    price_discount_input = models.PositiveIntegerField(default=0)
    # Số tiền phụ thu do salers nhập vào
    price_addition_input = models.PositiveIntegerField(default=0)
    # Số tiền vận chuyển
    price_delivery_input = models.PositiveIntegerField(default=0)
    # Giá cuối của đơn hàng
    # Công thức: price_total_order_actual = price_total_variant_actual
    # - (price_total_discount_order_promotion + price_discount_input)
    # + price_addition_input + price_delivery_input
    price_total_order_actual = models.PositiveBigIntegerField(default=0)
    # Số tiền khách cọc
    price_pre_paid = models.PositiveBigIntegerField(default=0)
    # Số tiền còn lại sau khi cọc
    price_after_paid = models.PositiveBigIntegerField(default=0)

    complete_time = models.DateTimeField(null=True)
    complete_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="orders_complete")
    source = models.ForeignKey(LeadChannel, on_delete=models.SET_NULL, null=True, related_name="orders")
    tracking_number = models.CharField(max_length=255, null=True)
    tags = models.ManyToManyField(OrdersTag, db_table="tbl_Orders_Tags_Detail", blank=True)
    cancel_reason = models.ForeignKey(OrdersCancelReason, on_delete=models.SET_NULL, null=True, related_name="orders")
    type = models.ForeignKey(OrdersType, on_delete=models.SET_NULL, null=True, related_name="orders")

    history = HistoricalRecords(
        history_id_field=models.UUIDField(default=uuid.uuid4),
        excluded_fields=[
            "tags",
            "order_number",
            "order_key",
            "customer",
            # "quatity_total_variant_all",
            "price_total_variant_all",
            "price_total_variant_actual",
            "price_total_discount_order_promotion",
            "price_total_variant_actual_input",
            "price_discount_input",
            "price_addition_input",
            "price_delivery_input",
            "price_total_order_actual",
            "price_pre_paid",
            "price_after_paid",
        ],
        table_name="tbl_Orders_Historical",
    )

    def items_list(self) -> (list[object]):
        """Lấy toàn bộ sản phẩm và số lượng có trong đơn hàng(line items, items combo, items gift)"""
        keys_obj_item = ("url", "code", "name", "price", "quantity")
        items = {}

        def add_update_quantity_item(variant_id, item):
            if items.get(variant_id):
                items[variant_id].update({"quantity": items[variant_id]["quantity"] + item["quantity"]})
            else:
                items[variant_id] = item

        line_items: list[OrdersItems] = self.line_items.all()
        for line_item in line_items:
            quantity = line_item.quantity
            # line item
            if line_item.variant.type != ProductVariantType.SIMPLE:
                items_combo = line_item.items_combo.all()
                for item_combo in items_combo:
                    variant = item_combo.variant
                    quantity_in_combo = item_combo.quantity
                    add_update_quantity_item(
                        str(variant.id),
                        dict(zip(keys_obj_item, ("", str(variant.id), variant.name, variant.sale_price, quantity * quantity_in_combo))),
                    )
            else:
                variant: ProductsVariants = line_item.variant
                add_update_quantity_item(
                    str(variant.id), dict(zip(keys_obj_item, ("", str(variant.id), variant.name, variant.sale_price, quantity)))
                )
            # promotions type == other_variant
            promotions_variant = line_item.variant_promotions_used.filter(promotion_variant__type=PromotionVariantType.OTHER_VARIANT)
            for promotion in promotions_variant:
                items_promotion = promotion.items_promotion.all()
                for item in items_promotion:
                    variant = item.variant
                    add_update_quantity_item(
                        str(variant.id), dict(zip(keys_obj_item, ("", str(variant.id), variant.name, variant.sale_price, item.quantity)))
                    )
        return len(line_items), list(items.values())

    class Meta:
        db_table = "tbl_Orders"
        ordering = ["-order_key"]


class OrdersPayments(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="payments_created")
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="payments_modified")
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name="payments")
    type = models.CharField(max_length=15, choices=OrderPaymentType.choices(), default=OrderPaymentType.COD.value)
    price_from_order = models.PositiveBigIntegerField(null=True)
    price_from_third_party = models.PositiveBigIntegerField(null=True)
    date_from_third_party = models.DateTimeField(null=True)
    price_from_upload_file = models.PositiveBigIntegerField(null=True)
    date_from_upload_file = models.DateTimeField(null=True)
    is_confirm = models.BooleanField(default=False)
    date_confirm = models.DateTimeField(null=True)
    note = models.TextField(blank=False, null=True)

    history = HistoricalRecords(
        history_id_field=models.UUIDField(default=uuid.uuid4),
        excluded_fields=[
            "created",
            "created_by",
            "order",
            "price_from_order",
        ],
        table_name="tbl_Orders_Payments_Historical",
    )

    class Meta:
        db_table = "tbl_Orders_Payments"
        ordering = ["-created"]
        unique_together = ["order", "type"]


class OrdersPromotion(TimeStampedModel, UUIDModel):
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_promotions_created")
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_promotions_modified")
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name="promotions_used")
    promotion_order = models.ForeignKey(PromotionOrder, on_delete=models.SET_NULL, null=True, related_name="orders_used")
    price = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "tbl_Orders_Promotion"
        unique_together = ["order", "promotion_order"]
        ordering = ["-created"]


class OrdersItems(TimeStampedModel, UUIDModel):
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_items_created")
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_items_modified")
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name="line_items")
    variant = models.ForeignKey(ProductsVariants, on_delete=models.SET_NULL, null=True, related_name="orders_items")
    quantity = models.PositiveSmallIntegerField(default=1)
    price_variant_logs = models.PositiveBigIntegerField(null=False, blank=False)
    discount = models.PositiveIntegerField(default=0)
    price_total = models.PositiveBigIntegerField(blank=False, null=False)
    price_total_input = models.PositiveBigIntegerField(blank=False, null=True, default=0)
    price_total_neo = models.PositiveBigIntegerField(blank=False, null=True)
    sales_bonus = models.PositiveIntegerField(blank=False, null=True)
    third_party_item_id = models.CharField(max_length=255, blank=False, null=True)
    third_party_source = models.CharField(max_length=255, blank=False, null=True)
    is_cross_sale = models.BooleanField(default=False)
    is_promo_sale = models.BooleanField(default=False)
    type_data_flow = models.CharField(max_length=13, choices=OrderItemDataFlowType.choices(), default=OrderItemDataFlowType.SIMPLE.value)

    commission_discount = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        db_table = "tbl_Orders_Items"
        ordering = ["-created"]


class OrderVariantsPromotion(TimeStampedModel, UUIDModel):
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_variant_promotions_created")
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_variant_promotions_modified")
    line_item = models.ForeignKey(OrdersItems, on_delete=models.CASCADE, null=True, related_name="variant_promotions_used")
    promotion_variant = models.ForeignKey(PromotionVariant, models.SET_NULL, null=True, related_name="order_variants")
    price = models.PositiveBigIntegerField(blank=False, null=False)

    class Meta:
        db_table = "tbl_Order_Variants_Promotion"
        ordering = ["-created"]


class OrdersItemsPromotion(TimeStampedModel, UUIDModel):
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_item_promotion_created")
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_item_promotion_modified")
    order_variant_promotion = models.ForeignKey(OrderVariantsPromotion, on_delete=models.CASCADE, related_name="items_promotion")
    variant = models.ForeignKey(ProductsVariants, on_delete=models.SET_NULL, null=True, related_name="line_items_promotions")
    quantity = models.PositiveSmallIntegerField(default=0)
    price = models.PositiveBigIntegerField(blank=False, null=False)
    total = models.PositiveBigIntegerField(blank=False, null=False)

    class Meta:
        db_table = "tbl_Orders_Items_Promotion"
        ordering = ["-created"]


class OrdersItemsCombo(TimeStampedModel, UUIDModel):
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_item_combo_created")
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_item_combo_modified")
    line_item = models.ForeignKey(OrdersItems, on_delete=models.CASCADE, related_name="items_combo")
    variant = models.ForeignKey(ProductsVariants, on_delete=models.SET_NULL, null=True, related_name="order_item_combos")
    quantity = models.PositiveSmallIntegerField(default=1)
    price = models.PositiveBigIntegerField(blank=False, null=False)
    total = models.PositiveBigIntegerField(blank=False, null=False)

    class Meta:
        db_table = "tbl_Orders_Items_Combo"
        ordering = ["-created"]


class ConfirmationSheetLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    turn_number = models.IntegerField()
    order_number = models.PositiveBigIntegerField(null=True)
    order_key = models.CharField(max_length=256)
    scan_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="sheet_confirm_logs", null=True)
    scan_at = models.DateTimeField(auto_now_add=True)
    is_success = models.BooleanField(default=True)
    log_message = models.TextField(max_length=512, blank=True)
    type = models.CharField(choices=ConfirmationLogType.choices(), max_length=36, null=True)


class TransportationCareReason(models.Model):
    name = models.CharField(max_length=264, blank=True, null=True)
    type = models.CharField(choices=TransportationCareCreationReason.choices(), max_length=18, blank=True, null=True)

    class Meta:
        db_table = "tbl_Transportation_Care_Reason"


class TransportationCareAction(models.Model):
    name = models.CharField(max_length=264, blank=True, null=True)
    type = models.CharField(choices=TransportationCareCreationReason.choices(), max_length=18, blank=True, null=True)

    class Meta:
        db_table = "tbl_Transportation_Care_Action"


class TransportationCare(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Orders, on_delete=models.SET_NULL, null=True, related_name="transportation_care")
    assign_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="transportation_care_assign_by")
    assigned_at = models.DateTimeField(blank=True, null=True)
    handle_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="transportation_care_handle_by")
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="transportation_care_modified_by")
    note = models.TextField(null=True, blank=True)
    appointment_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=32, choices=TransportationCareStatus.choices(), default=TransportationCareStatus.NEW.value)

    late_created = models.DateTimeField(blank=True, null=True)
    late_reason = models.ForeignKey(
        TransportationCareReason,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="transportation_late_reason",
    )
    late_action = models.ForeignKey(
        TransportationCareAction,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="transportation_late_action",
    )

    wait_return_created = models.DateTimeField(blank=True, null=True)
    wait_return_reason = models.ForeignKey(
        TransportationCareReason,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="transportation_wait_return_reason",
    )
    wait_return_action = models.ForeignKey(
        TransportationCareAction,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="transportation_wait_return_action",
    )

    returning_created = models.DateTimeField(blank=True, null=True)
    returning_reason = models.ForeignKey(
        TransportationCareReason,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="transportation_wait_returning_reason",
    )
    returning_action = models.ForeignKey(
        TransportationCareAction,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="transportation_wait_returning_action",
    )
    returned_created = models.DateTimeField(blank=True, null=True)
    returned_reason = models.ForeignKey(
        TransportationCareReason,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="transportation_returned_reason",
    )
    returned_action = models.ForeignKey(
        TransportationCareAction,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="transportation_returned_action",
    )

    reason_old = models.ForeignKey(
        TransportationCareReason, on_delete=models.SET_NULL, related_name="transportation_care_reason", null=True
    )
    action_old = models.ForeignKey(
        TransportationCareAction, on_delete=models.SET_NULL, related_name="transportation_care_action", null=True
    )
    created_reason_old = models.CharField(max_length=32, choices=TransportationCareCreationReason.choices(), blank=True, null=True)
    history = HistoricalRecords(
        history_id_field=models.UUIDField(default=uuid.uuid4),
        excluded_fields=[
            "created",
            "created_by",
        ],
        table_name="tbl_Transportation_Care_Historical",
    )

    class Meta:
        db_table = "tbl_Transportation_Care"
        ordering = ["-created"]
