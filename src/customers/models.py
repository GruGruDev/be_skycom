import uuid

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from model_utils.models import TimeStampedModel
from model_utils.models import UUIDModel
from simple_history.models import HistoricalRecords

from customers.enums import CustomerGender
from customers.enums import SourceLead
from users.models import User

# from customers.enums import CustomerRank


class CustomerGroup(UUIDModel):
    name = models.CharField(max_length=255, blank=False, null=False, unique=True)
    note = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self) -> (str):
        return self.name

    class Meta:
        db_table = "tbl_Customers_Group"
        ordering = ["name"]


class CustomerTag(UUIDModel):
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)

    def __str__(self) -> (str):
        return self.name

    class Meta:
        db_table = "tbl_Customers_Tag"
        ordering = ["name"]


class CustomerRank(UUIDModel, TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name_rank = models.CharField(max_length=255, unique=True)
    spend_from = models.PositiveBigIntegerField(blank=True, null=True, default=0)
    spend_to = models.PositiveBigIntegerField(blank=True, null=True, default=0)
    created_by = models.ForeignKey(User, related_name="customer_rank_created", blank=True, null=True, on_delete=models.DO_NOTHING)
    modified_by = models.ForeignKey(User, related_name="customer_rank_modified", blank=True, null=True, on_delete=models.DO_NOTHING)

    class Meta:
        db_table = "tbl_Rank"
        unique_together = [["spend_from", "spend_to"]]

    def clean(self):

        if self.spend_from >= self.spend_to:
            raise ValidationError("Giá bắt đầu phải nhỏ hơn giá kết thúc.")

        overlapping_ranks = CustomerRank.objects.exclude(id=self.id).filter(
            models.Q(spend_from__lte=self.spend_to) & models.Q(spend_to__gte=self.spend_from)
        )

        if overlapping_ranks.exists():
            raise ValidationError(f"Phạm vị chi tiêu trùng lặp với phạm vi xếp hạng {overlapping_ranks} hiện có: ")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name_rank


class Customer(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    rank = models.ForeignKey(CustomerRank, related_name="object_rank", blank=True, null=True, on_delete=models.SET_NULL)
    created_by = models.ForeignKey(User, related_name="customer_created", blank=True, null=True, on_delete=models.DO_NOTHING)
    modified_by = models.ForeignKey(User, related_name="customer_modified", blank=True, null=True, on_delete=models.DO_NOTHING)
    source = models.CharField(max_length=11, choices=SourceLead.choices(), default=SourceLead.OTHER)
    code = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=False, null=False)
    email = models.EmailField(max_length=255, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=CustomerGender.choices(), blank=True, null=True)
    customer_note = models.CharField(max_length=255, blank=True, null=True)
    ecommerce_id = models.CharField(max_length=50, blank=True, null=True)

    ranking = models.CharField(max_length=255, blank=True, null=True)
    latest_up_rank_date = models.DateField(blank=True, null=True)
    total_order = models.IntegerField(blank=True, null=True, default=0)
    total_spent = models.FloatField(blank=True, null=True, default=0)
    last_order_id = models.CharField(max_length=255, blank=True, null=True)
    last_order_time = models.DateTimeField(blank=True, null=True)

    customer_care_staff = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="customer_care_staff")
    modified_care_staff_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="customer_care_staff_modified"
    )
    care_start_time = models.DateTimeField(blank=True, null=True)

    tags = models.ManyToManyField(CustomerTag, through="CustomerTagDetail", through_fields=("customer", "customer_tag"))
    groups = models.ManyToManyField(CustomerGroup, through="CustomerGroupDetail", through_fields=("customer", "customer_group"))
    history = HistoricalRecords(history_id_field=models.UUIDField(default=uuid.uuid4), excluded_fields=["tags", "groups"])

    shipping_completed_order = models.IntegerField(default=0)  # số lượng đơn hàng đã giao thành công
    shipping_completed_spent = models.IntegerField(default=0)  # số tiền khách đã chi trả cho các đơn giao thành công
    last_shipping_completed = models.DateTimeField(blank=True, null=True)

    shipping_return_order = models.IntegerField(default=0)  # số lượng đơn hàng đã hoàn
    shipping_return_spent = models.IntegerField(default=0)  # số tiền khách đã chi trả cho các đơn đã hoàn

    shipping_cancel_order = models.IntegerField(default=0)  # số lượng đơn hàng đã huỷ
    shipping_cancel_spent = models.IntegerField(default=0)  # số tiền khách đã chi trả cho các đơn đã huỷ

    def __str__(self):
        return self.name

    class Meta:
        db_table = "tbl_Customers"
        ordering = ["-created"]


class CustomerTagDetail(UUIDModel):
    customer_tag = models.ForeignKey(CustomerTag, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    class Meta:
        db_table = "tbl_Customers_Tag_Detail"
        constraints = [models.UniqueConstraint(fields=["customer_tag", "customer"], name="unique_customer_tag")]


class CustomerGroupDetail(UUIDModel):
    customer_group = models.ForeignKey(CustomerGroup, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    class Meta:
        db_table = "tbl_Customers_Group_Detail"
        constraints = [models.UniqueConstraint(fields=["customer_group", "customer"], name="unique_customer_group")]


class CustomerPhone(UUIDModel, TimeStampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="phones")
    phone_regex = RegexValidator(
        regex=r"[0|+84|84]{0,4}[9|8|3|5|7]{1}[0-9]{6,10}",
        message="Phone number must be a Vietnamese phone number, \
            include 7-15 digits. Example format: 098xxxxxxx, +8498xxxxxxx",
    )
    phone = models.CharField(max_length=15, validators=[phone_regex], blank=False, null=False, unique=True)

    def __str__(self) -> (str):
        return self.phone

    class Meta:
        db_table = "tbl_Customers_Phone"
        ordering = ["-created"]
        constraints = [models.UniqueConstraint(fields=["customer", "phone"], name="unique_customer_phone")]
