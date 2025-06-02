from django.contrib import admin

from customers.models import Customer
from customers.models import CustomerGroup
from customers.models import CustomerPhone
from customers.models import CustomerTag


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    pass


@admin.register(CustomerGroup)
class CustomerGroupAdmin(admin.ModelAdmin):
    pass


@admin.register(CustomerPhone)
class CustomerPhoneAdmin(admin.ModelAdmin):
    pass


@admin.register(CustomerTag)
class CustomerTagAdmin(admin.ModelAdmin):
    pass
