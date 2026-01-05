from django.contrib import admin
from .models import Operation, OperationStatus


class OperationStatusInline(admin.TabularInline):
    """Inline para mostrar y editar estados dentro de un operativo"""
    model = OperationStatus
    extra = 1
    ordering = ['order']
    fields = ('name', 'description', 'order')
    readonly_fields = ('created_at',)


@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'driver', 'is_active', 'is_finalized', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'created_by__email', 'driver__first_name', 'driver__last_name')
    list_filter = ('is_active', 'is_finalized', 'created_at', 'driver')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'description')
        }),
        ('Asignaciones', {
            'fields': ('driver',)
        }),
        ('Estado', {
            'fields': ('is_active', 'is_finalized')
        }),
        ('Información', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    inlines = [OperationStatusInline]
    autocomplete_fields = ['created_by', 'driver']


@admin.register(OperationStatus)
class OperationStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'operation', 'order', 'created_at')
    search_fields = ('name', 'description', 'operation__name')
    list_filter = ('operation', 'created_at')
    readonly_fields = ('id', 'created_at')
    fieldsets = (
        (None, {
            'fields': ('id', 'operation', 'name', 'description', 'order')
        }),
        ('Información', {
            'fields': ('created_at',)
        }),
    )
    autocomplete_fields = ['operation']
    ordering = ['operation', 'order']
