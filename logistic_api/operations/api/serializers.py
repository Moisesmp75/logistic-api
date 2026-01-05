from django.db import models
from rest_framework import serializers
from ..models import Operation, OperationStatus


class OperationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationStatus
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class OperationSerializer(serializers.ModelSerializer):
    statuses = OperationStatusSerializer(many=True, read_only=True)
    
    class Meta:
        model = Operation
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')


class CreateOperationSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    order_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    
    def validate_order_ids(self, value):
        """Validar que los orders no estén finalizados"""
        if not value:
            return value
        
        from ...orders.models import Order
        orders = Order.objects.filter(id__in=value)
        
        # Verificar que todos los orders existan
        found_ids = set(orders.values_list('id', flat=True))
        requested_ids = set(value)
        missing_ids = requested_ids - found_ids
        if missing_ids:
            raise serializers.ValidationError(
                f"Orders not found: {list(missing_ids)}"
            )
        
        # Verificar que ningún order esté finalizado
        finalized_orders = []
        for order in orders:
            if order.is_finalized():
                finalized_orders.append(str(order.id))
        
        if finalized_orders:
            raise serializers.ValidationError(
                f"Cannot assign finalized orders to an operation: {', '.join(finalized_orders)}"
            )
        
        return value

    def create(self, validated_data):
        request = self.context['request']
        order_ids = validated_data.pop('order_ids', [])
        
        operation = Operation.objects.create(
            name=validated_data['name'],
            description=validated_data.get('description', ''),
            created_by=request.user
        )
        
        # Asignar pedidos al operativo si se proporcionaron
        if order_ids:
            from ...orders.models import Order
            Order.objects.filter(id__in=order_ids).update(operation=operation)
        
        return operation


class UpdateOperationSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    driver_id = serializers.UUIDField(required=False, allow_null=True)
    order_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    is_active = serializers.BooleanField(required=False)
    is_finalized = serializers.BooleanField(required=False)
    
    def validate_order_ids(self, value):
        """Validar que los orders no estén finalizados"""
        if not value:
            return value
        
        from ...orders.models import Order
        orders = Order.objects.filter(id__in=value)
        
        # Verificar que todos los orders existan
        found_ids = set(orders.values_list('id', flat=True))
        requested_ids = set(value)
        missing_ids = requested_ids - found_ids
        if missing_ids:
            raise serializers.ValidationError(
                f"Orders not found: {list(missing_ids)}"
            )
        
        # Verificar que ningún order esté finalizado
        finalized_orders = []
        for order in orders:
            if order.is_finalized():
                finalized_orders.append(str(order.id))
        
        if finalized_orders:
            raise serializers.ValidationError(
                f"Cannot assign finalized orders to an operation: {', '.join(finalized_orders)}"
            )
        
        return value


class CreateOperationStatusSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    order = serializers.IntegerField(required=False)

    def validate_order(self, value):
        operation = self.context['operation']
        if value is not None and value < 1:
            raise serializers.ValidationError("Order must be a positive integer.")
        return value

    def create(self, validated_data):
        operation = self.context['operation']
        order = validated_data.get('order')
        
        # Si no se especifica order, se coloca al final
        if order is None:
            from django.db.models import Max
            max_order = OperationStatus.objects.filter(operation=operation).aggregate(
                max_order=Max('order')
            )['max_order'] or 0
            order = max_order + 1
        
        # Reordenar estados existentes si es necesario
        from django.db.models import F
        OperationStatus.objects.filter(
            operation=operation,
            order__gte=order
        ).update(order=F('order') + 1)
        
        status = OperationStatus.objects.create(
            operation=operation,
            name=validated_data['name'],
            description=validated_data.get('description', ''),
            order=order
        )
        return status


class UpdateOperationStatusOrderSerializer(serializers.Serializer):
    status_id = serializers.UUIDField()
    new_order = serializers.IntegerField()

    def validate_new_order(self, value):
        if value < 1:
            raise serializers.ValidationError("Order must be a positive integer.")
        return value


class ReorderOperationStatusesSerializer(serializers.Serializer):
    statuses = UpdateOperationStatusOrderSerializer(many=True)

