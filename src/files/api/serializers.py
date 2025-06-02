from rest_framework import serializers

from files.models import Images


class ImagesSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=True)

    class Meta:
        model = Images
        fields = "__all__"


class ImagesUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Images
        exclude = (
            "id",
            "image",
            "created",
        )


class ImagesReadBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Images
        fields = ("id", "image", "created", "type", "is_default")
