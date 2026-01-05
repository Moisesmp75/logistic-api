from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'client', 'operation', 'delivery_city',
        'current_status', 'is_active', 'created_at'
    )
    search_fields = (
        'order_number', 'delivery_address', 'delivery_city',
        'client__business_name', 'operation__name'
    )
    list_filter = (
        'is_active', 'created_at', 'client', 'operation',
        'delivery_country', 'delivery_region', 'current_status'
    )
    readonly_fields = ('id', 'created_at', 'updated_at', 'created_by', 'current_status', 'operation')
    fieldsets = (
        (None, {
            'fields': ('id', 'order_number', 'description')
        }),
        ('Información de entrega', {
            'fields': (
                'delivery_address', 'delivery_city',
                'delivery_region', 'delivery_country'
            )
        }),
        ('Asignaciones', {
            'fields': ('client', 'operation', 'current_status'),
            'description': 'El campo operation solo puede ser asignado por ADMIN o INTERNAL al crear/actualizar operativos.'
        }),
        ('Información adicional', {
            'fields': ('notes', 'is_active')
        }),
        ('Información del sistema', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    autocomplete_fields = ['client', 'created_by']
    ordering = ['-created_at']
