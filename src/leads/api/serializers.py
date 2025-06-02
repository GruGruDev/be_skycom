from rest_framework import serializers
from leads.models.attributes import LeadChannel


class LeadAttributeSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=500)
    is_shown = serializers.BooleanField(default=True)


class LeadChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadChannel
        fields = "__all__"

