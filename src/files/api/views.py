import django_filters.rest_framework as django_filters
from rest_framework import filters
from rest_framework import parsers
from rest_framework import permissions
from rest_framework import viewsets
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

from files.api.filters import ImagesFilterset
from files.api.serializers import ImagesSerializer
from files.api.serializers import ImagesUpdateSerializer
from files.models import Images
from users.activity_log import ActivityLogMixin


class ImagesViewset(ActivityLogMixin, viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Images.objects.all()
    serializer_class = ImagesSerializer
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)
    filter_backends = (
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    )
    filterset_class = ImagesFilterset
    ordering_fields = "__all__"

    def get_serializer_class(self):
        if self.action in ["partial_update"]:
            return ImagesUpdateSerializer
        return ImagesSerializer

    def perform_create(self, serializer):
        image = serializer.validated_data.get("image")
        img = Image.open(image)
        # Check if resizing is needed
        if img.width > 1000:
            # Calculate new height maintaining aspect ratio
            ratio = 1000 / float(img.width)
            new_height = int(float(img.height) * ratio)

            # Resize the image
            img = img.resize((1000, new_height), Image.LANCZOS)

            # Save the resized image to a BytesIO object
            output = BytesIO()
            img.save(output, format="JPEG", quality=85)
            output.seek(0)

            # Replace the original image with the resized one
            serializer.validated_data["image"] = InMemoryUploadedFile(
                output,
                "ImageField",
                f"{image.name.split('.')[0]}_resized.jpg",
                "image/jpeg",
                sys.getsizeof(output),
                None,
            )
        serializer.validated_data["upload_by"] = self.request.user
        return super().perform_create(serializer)
