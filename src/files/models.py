import os

from django.db import models
from model_utils.models import TimeStampedModel
from model_utils.models import UUIDModel

from utils.enums import EnumBase


class ImageTypes(EnumBase):
    PRODUCT = "PD"
    PRODUCT_VARIANT = "PDV"
    USER = "US"
    PAYMENT = "PM"
    OTHER = "OT"
    MATERIAL = "MT"
    ORDER = "OD"


FOLDER_UP_IM_BY_TYPE = {
    ImageTypes.OTHER: "uploads/images/other",
    ImageTypes.PRODUCT: "uploads/images/product",
    ImageTypes.PRODUCT_VARIANT: "uploads/images/product-variant",
    ImageTypes.USER: "uploads/images/user",
    ImageTypes.PAYMENT: "uploads/images/payment",
    ImageTypes.MATERIAL: "uploads/images/material",
    ImageTypes.ORDER: "uploads/images/order",
}


def image_file_path(instance, filename):
    """Generate file path for new recipe image"""
    ext = filename.split(".")[-1]
    filename = f"{instance.id}.{ext}"
    path = FOLDER_UP_IM_BY_TYPE.get(instance.type)
    return os.path.join(path, filename)


class Images(UUIDModel, TimeStampedModel):
    type = models.CharField(choices=ImageTypes.choices(), max_length=5, default=ImageTypes.OTHER)
    image = models.ImageField(upload_to=image_file_path, null=False)
    upload_by = models.ForeignKey("users.User", null=True, on_delete=models.SET_NULL, related_name="images_uploaded")
    user = models.ForeignKey("users.User", null=True, on_delete=models.CASCADE, related_name="images")
    product = models.ForeignKey("products.Products", null=True, on_delete=models.CASCADE, related_name="images")
    product_variant = models.ForeignKey("products.ProductsVariants", null=True, on_delete=models.CASCADE, related_name="images")
    payment = models.ForeignKey("orders.OrdersPayments", null=True, on_delete=models.CASCADE, related_name="images")
    material = models.ForeignKey("products.ProductsMaterials", null=True, on_delete=models.CASCADE, related_name="images")
    order = models.ForeignKey("orders.Orders", null=True, on_delete=models.CASCADE, related_name="images")
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "tbl_Images"
        ordering = ["-created"]

    def delete(self, using=None):
        self.image.delete(save=False)
        super().delete()
