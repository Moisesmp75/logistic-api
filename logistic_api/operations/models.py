import uuid
from django.db import models
from django.conf import settings


class Operation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_operations'
    )
    
    driver = models.ForeignKey(
        'profile.DriverProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operations'
    )
    
    is_active = models.BooleanField(default=True)
    is_finalized = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.id}"


class OperationStatus(models.Model):
    """
    Estados que pertenecen a un operativo.
    Cada estado tiene un orden dentro de la secuencia del operativo.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    operation = models.ForeignKey(
        Operation,
        on_delete=models.CASCADE,
        related_name='statuses'
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    # Orden dentro de la secuencia del operativo
    order = models.PositiveIntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['operation', 'order']
        unique_together = ['operation', 'order']
        indexes = [
            models.Index(fields=['operation', 'order']),
        ]
    
    def __str__(self):
        return f"{self.operation.name} - {self.name} (Orden: {self.order})"
