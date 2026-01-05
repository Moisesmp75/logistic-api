from django.contrib import admin
from .models import ClientProfile, InternalClientProfile, DriverProfile

@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ("business_name", "ruc", "phone_number", "contact_phone", "is_active", "created_at")
    search_fields = ("business_name", "ruc", "phone_number", "contact_phone")


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "license_number", "is_active")
    search_fields = ("first_name", "last_name", "license_number")


@admin.register(InternalClientProfile)
class InternalClientProfileAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "client", "is_active")
    search_fields = ("first_name", "last_name", "client__business_name")
    list_filter = ("client",)
    autocomplete_fields = ["client"]