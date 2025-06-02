import uuid

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import UserManager
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from model_utils.models import TimeStampedModel
from model_utils.models import UUIDModel
from simple_history.models import HistoricalRecords


class Department(UUIDModel):
    name = models.CharField(max_length=255, unique=True)
    is_receive_lead = models.BooleanField(default=False)
    is_shown = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "tbl_User_Department"


class Role(UUIDModel):
    name = models.CharField(max_length=255, unique=True)
    data = models.JSONField(max_length=255)
    default_router = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "tbl_User_Role"


class CustomUserManager(UserManager):
    def _create_user(self, email, password, name=None, **extra_fields):
        if not email:
            raise ValueError("The given username must be set")
        email = self.normalize_email(email)

        if not name:
            name, _ = email.split("@")

        user = self.model(email=email, name=name, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, null=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)

    is_assign_lead_campaign = models.BooleanField(default=False, null=True)
    is_online = models.BooleanField(default=False, null=True)
    is_exportdata = models.BooleanField(default=False, null=True)
    is_CRM = models.BooleanField(default=False, null=True)
    is_hotdata = models.BooleanField(default=False, null=True)
    is_active = models.BooleanField(default=True, null=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"

    objects = CustomUserManager()
    created_by = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, related_name="users_created")
    modified_by = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, related_name="users_modified")
    history = HistoricalRecords(excluded_fields=["created_by"], table_name="tbl_User_Historical")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-created"]
        db_table = "tbl_User"


# Activity Log
CREATE, READ, UPDATE, DELETE = "Create", "Read", "Update", "Delete"
LOGIN, LOGOUT, EXPORT, IMPORT = "Login", "Logout", "Export", "Import"
ACTION_TYPES = [
    (CREATE, CREATE),
    (READ, READ),
    (UPDATE, UPDATE),
    (DELETE, DELETE),
    (LOGIN, LOGIN),
    (LOGOUT, LOGOUT),
    (EXPORT, EXPORT),
    (IMPORT, IMPORT),
]
SUCCESS, FAILED = "Success", "Failed"
ACTION_STATUS = [(SUCCESS, SUCCESS), (FAILED, FAILED)]


class UserActionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="action_logs")
    action_type = models.CharField(choices=ACTION_TYPES, max_length=100, default=READ)
    action_time = models.DateTimeField(auto_now_add=True)
    action_name = models.TextField(blank=True, null=True)
    status = models.CharField(choices=ACTION_STATUS, max_length=15, default=SUCCESS)
    data = models.JSONField(default=dict)
    message = models.CharField(max_length=255, blank=True, null=True)
    content_type = models.ForeignKey(ContentType, models.SET_NULL, blank=True, null=True)
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        ordering = ["-action_time"]
        db_table = "tbl_User_Action_Log"

    def __str__(self) -> str:
        return f"{self.action_type} by {self.user} on {self.action_time}"
