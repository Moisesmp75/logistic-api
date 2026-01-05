from django.db import transaction
from rest_framework import serializers
from ..models import Order
from ...profile.models import ClientProfile
from ...operations.models import Operation


class OrderSerializer(serializers.ModelSerializer):
    client_business_name = serializers.CharField(source='client.business_name', read_only=True)
    operation_name = serializers.CharField(source='operation.name', read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'current_status')


class CreateOrderSerializer(serializers.Serializer):
    order_number = serializers.CharField()
    client_id = serializers.UUIDField()
    description = serializers.CharField(required=False, allow_blank=True)
    delivery_address = serializers.CharField()
    delivery_city = serializers.CharField(required=False, allow_blank=True)
    delivery_region = serializers.CharField(required=False, allow_blank=True)
    delivery_country = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_client_id(self, value):
        request = self.context['request']
        user = request.user
        
        # Validar que el client_id existe
        try:
            client = ClientProfile.objects.get(id=value)
        except ClientProfile.DoesNotExist:
            raise serializers.ValidationError("Client profile not found.")
        
        # Validar que el usuario del token coincide con el client_id
        if user.role == 'client':
            try:
                user_client = user.client_profile
                if user_client.id != value:
                    raise serializers.ValidationError("You can only create orders for your own client profile.")
            except ClientProfile.DoesNotExist:
                raise serializers.ValidationError("You don't have an associated client profile.")
        
        elif user.role == 'internal_client':
            try:
                user_client = user.internal_client_profile.client
                if user_client.id != value:
                    raise serializers.ValidationError("You can only create orders for your associated client profile.")
            except:
                raise serializers.ValidationError("You don't have an associated client profile.")
        else:
            raise serializers.ValidationError("Only clients and internal clients can create orders.")
        
        return value

    @transaction.atomic
    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        client_id = validated_data.pop('client_id')
        
        # Obtener el cliente (ya validado en validate_client_id)
        client = ClientProfile.objects.get(id=client_id)
        
        order = Order.objects.create(
            order_number=validated_data['order_number'],
            description=validated_data.get('description', ''),
            delivery_address=validated_data['delivery_address'],
            delivery_city=validated_data.get('delivery_city', ''),
            delivery_region=validated_data.get('delivery_region', ''),
            delivery_country=validated_data.get('delivery_country', ''),
            notes=validated_data.get('notes', ''),
            created_by=user,
            client=client
        )
        
        return order


class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'order_number', 'description', 'delivery_address',
            'delivery_city', 'delivery_region', 'delivery_country',
            'notes', 'is_active'
        ]

