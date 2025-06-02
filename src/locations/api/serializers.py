from rest_framework import serializers

from locations.models import Address
from locations.models import Districts
from locations.models import Provinces
from locations.models import Wards


class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provinces
        fields = ["name", "slug", "label", "code", "type"]


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = Districts
        fields = ["name", "slug", "label", "code", "type"]


class WardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wards
        fields = ["name", "slug", "label", "code", "type"]


class LocationSerializer(serializers.ModelSerializer):
    district = serializers.PrimaryKeyRelatedField(read_only=True)
    province = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Wards
        fields = ["code", "label", "district", "province"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        district = instance.district
        province = instance.province
        representation["district_id"] = district.code
        representation["district"] = district.label
        representation["province_id"] = province.code
        representation["province"] = province.label
        representation["ward_id"] = instance.code
        representation["ward"] = instance.label
        del representation["label"]
        return representation


class AddressSerializer(serializers.ModelSerializer):
    ward = LocationSerializer(read_only=True)

    class Meta:
        model = Address
        fields = "__all__"


class AddressCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"


class AddressUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
        extra_kwargs = {
            "id": {"read_only": True},
            "customer": {"read_only": True},
            "type": {"read_only": True},
            "warehouse": {"read_only": True},
            "address": {"required": False},
            "ward": {"required": False},
        }

    def to_representation(self, instance):
        repre = super().to_representation(instance)
        repre["ward"] = LocationSerializer(instance=instance.ward).data
        return repre
