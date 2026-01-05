import uuid
from django.db import models
from django.conf import settings


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Código único del pedido
    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Información del pedido
    description = models.TextField(blank=True, null=True)
    
    # Dirección de entrega
    delivery_address = models.TextField()
    delivery_city = models.CharField(max_length=100, blank=True, null=True)
    delivery_region = models.CharField(max_length=100, blank=True, null=True)
    delivery_country = models.CharField(max_length=100, blank=True, null=True)
    
    # Creador del pedido (CLIENT o INTERNAL_CLIENT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_orders'
    )
    
    # Cliente propietario del pedido
    client = models.ForeignKey(
        'profile.ClientProfile',
        on_delete=models.CASCADE,
        related_name='orders',
        null=True,
        blank=True
    )
    
    # Operativo al que pertenece (opcional al crear, se asigna después)
    operation = models.ForeignKey(
        'operations.Operation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    
    # Estado actual del pedido (se sincroniza con el estado del operativo)
    current_status = models.CharField(max_length=100, blank=True, null=True)
    
    # Información adicional
    notes = models.TextField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['operation']),
            models.Index(fields=['client']),
        ]
    
    def __str__(self):
        client_name = self.client.business_name if self.client else "No client"
        return f"{self.order_number} - {client_name}"
    
    def is_finalized(self):
        """
        Verifica si el pedido está en el estado final del operativo.
        Un pedido está finalizado si tiene un operativo asignado y su current_status
        coincide con el último estado (mayor orden) del operativo.
        """
        if not self.operation or not self.current_status:
            return False
        
        from ..operations.models import OperationStatus
        # Obtener el último estado del operativo (mayor orden)
        last_status = OperationStatus.objects.filter(
            operation=self.operation
        ).order_by('-order').first()
        
        if not last_status:
            return False
        
        # Comparar el current_status con el nombre del último estado
        return self.current_status == last_status.name
