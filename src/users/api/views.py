import django_filters.rest_framework as django_filters
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import filters
from rest_framework import generics
from rest_framework import mixins
from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.views import Response

from core.views import CustomModelViewSet
from users.api import serializers
from users.api.serializers import UserActionLogCreateUpdateSerializer
from users.api.serializers import UserActionLogListSerializerList
from users.filters import UserActionLogFilter
from users.filters import UserFilter
from users.models import Department
from users.models import Role
from users.models import UserActionLog
from utils.serializers import PassSerializer

User = get_user_model()


class UserViewSet(CustomModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    queryset = User.objects.select_related("role", "department").prefetch_related("images").exclude(is_superuser=True)
    serializer_class = PassSerializer

    action_serializer_classes = {
        "create": serializers.UserCreateSerializer,
        "partial_update": serializers.UserPatchUpdateSerializer,
        "list": serializers.UserReadListSerializer,
        "retrieve": serializers.UserReadOneSerializer,
    }

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    ]

    search_fields = ["name", "phone"]
    ordering_fields = "__all__"
    filterset_class = UserFilter

    def get_serializer_class(self):
        return self.action_serializer_classes.get(self.action, self.serializer_class)

    def perform_create(self, serializer):
        data = serializer.validated_data
        email = data["email"]
        password = data["password"]
        name = data.get("name")
        if not name:
            name, _ = email.split("@")
        password = make_password(password)
        data["created_by"] = self.request.user
        serializer.save(name=name, password=password)

    def perform_update(self, serializer):
        serializer.validated_data["modified_by"] = self.request.user
        return super().perform_update(serializer)

    def partial_update(self, request, *args, **kwargs):
        data = request.data
        email = data.get("email")
        password = data.get("password")
        name = data.get("name")

        # Tiền xữ lý dữ liệu
        if not name and email:
            name, _ = email.split("@")
            request.data["name"] = name
        if password:
            request.data["password"] = make_password(password)

        # Validate serializer
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Chỉ super admin mới có quyền chỉnh sửa thông tin của người dùng khác
        # Còn lại họ chỉ có thể chỉnh sửa thông tin của chính họ
        # if not user_from_token.is_superuser and user_from_token.pk != instance.pk:
        #     raise PermissionDenied()
        # Update user
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class ProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(serializers.UserReadOneSerializer(request.user).data, status=status.HTTP_200_OK)


class UserRoleViewSet(CustomModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    queryset = Role.objects.all()
    serializer_class = serializers.UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserDepartmentViewSet(CustomModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    queryset = Department.objects.all()
    serializer_class = serializers.UserDepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserHistoryListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = serializers.UserHistorySerializer
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = "__all__"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return User.objects.none()
        obj = generics.get_object_or_404(self.queryset, id=self.kwargs[self.lookup_field])
        return obj.history.all()


class UserActionLogViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = UserActionLog.objects.select_related("content_type", "user").all()
    serializer_class = PassSerializer
    action_serializer_classes = {
        "create": UserActionLogCreateUpdateSerializer,
        "partial_update": UserActionLogCreateUpdateSerializer,
        "list": UserActionLogListSerializerList,
    }
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    ]
    search_fields = ["user__name", "message"]
    filterset_class = UserActionLogFilter

    def get_serializer_class(self):
        return self.action_serializer_classes.get(self.action, self.serializer_class)
