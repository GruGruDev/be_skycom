from rest_framework import serializers

from files.api.serializers import ImagesReadBaseSerializer
from users.models import Department
from users.models import Role
from users.models import User
from users.models import UserActionLog


class UserRoleSerializer(serializers.ModelSerializer):
    # Thêm một trường mới để xử lý và trả về danh sách permissions
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        # Thêm "permissions" vào danh sách các trường để response trả về có trường này
        fields = ("id", "name", "data", "default_router", "permissions")

    # Hàm này sẽ lấy dữ liệu từ trường `data` và chuyển thành một danh sách permissions
    def get_permissions(self, obj):
        permission_list = []
        # Kiểm tra xem `data` có phải là một dict không
        if isinstance(obj.data, dict):
            # Lặp qua các nhóm quyền (vd: "product", "order")
            for group, perms in obj.data.items():
                if isinstance(perms, dict):
                    # Lấy tất cả các key (chính là codename của quyền) và thêm vào danh sách
                    permission_list.extend(perms.keys())
        return permission_list


class UserDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ("id", "name", "is_shown", "is_receive_lead")


class UserReadListSerializer(serializers.ModelSerializer):
    images = ImagesReadBaseSerializer(many=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "name",
            "phone",
            "is_assign_lead_campaign",
            "is_active",
            "is_superuser",
            "is_online",
            "is_exportdata",
            "is_CRM",
            "is_hotdata",
            "role",
            "department",
            "images",
            "created_by",
            "modified_by",
        )


class UserReadOneSerializer(serializers.ModelSerializer):
    role = UserRoleSerializer()
    images = ImagesReadBaseSerializer(many=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "name",
            "phone",
            "is_assign_lead_campaign",
            "is_active",
            "is_superuser",
            "is_online",
            "is_exportdata",
            "is_CRM",
            "is_hotdata",
            "role",
            "department",
            "images",
            "created_by",
            "modified_by",
        )


class UserBaseWriteSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return UserReadOneSerializer(instance).data


class UserCreateSerializer(UserBaseWriteSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "name",
            "phone",
            "is_assign_lead_campaign",
            "is_online",
            "is_exportdata",
            "is_CRM",
            "is_hotdata",
            "department",
            "role",
        )
        extra_kwargs = {"name": {"required": False}, "phone": {"required": False}}


class UserPatchUpdateSerializer(UserBaseWriteSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "name",
            "phone",
            "password",
            "is_assign_lead_campaign",
            "is_online",
            "is_active",
            "is_exportdata",
            "is_CRM",
            "is_hotdata",
            "department",
            "role",
        )
        extra_kwargs = {
            "password": {"required": False},
            "email": {"required": False},
            "name": {"required": False},
            "phone": {"required": False},
        }


class UserReadBaseInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "name")


class UserHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = User.history.model
        exclude = ("password",)


class UserActionLogCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActionLog
        fields = ("user", "action_type", "action_time", "action_name", "message")


class UserActionLogListSerializerList(serializers.ModelSerializer):
    class Meta:
        model = UserActionLog
        fields = ("user", "action_time", "action_type", "object_id", "content_type_id", "action_name", "message")

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["instance_name"] = instance.content_type.model_class().__name__ if instance.content_type else None
        representation["instance_id"] = representation.pop("object_id")
        representation.pop("content_type_id")
        return representation