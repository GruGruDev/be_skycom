from django.contrib import admin

from locations.models import Address
from locations.models import Districts
from locations.models import Provinces
from locations.models import Wards


@admin.register(Provinces)
class ProvincesAdmin(admin.ModelAdmin):
    pass


@admin.register(Districts)
class DistrictsGroupAdmin(admin.ModelAdmin):
    pass


@admin.register(Wards)
class WardsPhoneAdmin(admin.ModelAdmin):
    pass


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    pass
