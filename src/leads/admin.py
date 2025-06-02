from django.contrib import admin

from leads.models.attributes import LeadChannel


@admin.register(LeadChannel)
class LeadChannelAdmin(admin.ModelAdmin):
    pass
