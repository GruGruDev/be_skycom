from django.db import models
from model_utils.models import TimeStampedModel
from model_utils.models import UUIDModel

from users.models import User


class LeadAttribute(TimeStampedModel, UUIDModel):
    name = models.CharField(max_length=500, null=False, unique=True)
    is_shown = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_created_by",
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_modified_by",
    )

    class Meta:
        abstract = True
        ordering = ["id"]

    def __str__(self):
        return self.name



class LeadChannel(LeadAttribute):
    class Meta:
        ordering = ["-created"]
        db_table = "tbl_Leads_Channels"
