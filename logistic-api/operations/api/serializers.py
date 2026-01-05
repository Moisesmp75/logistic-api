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

    def create(self, validated_data):
        request = self.context['request']
        operation = Operation.objects.create(
            name=validated_data['name'],
            description=validated_data.get('description', ''),
            created_by=request.user
        )
        return operation


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

