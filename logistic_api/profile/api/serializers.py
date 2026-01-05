from django.db import transaction
from rest_framework import serializers
from ...users.models import User
from ..models import DriverProfile, ClientProfile, InternalClientProfile

class ClientProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = ClientProfile
        fields = '__all__'


class DriverProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = DriverProfile
        fields = '__all__'

class InternalClientSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = InternalClientProfile
        fields = '__all__'

class CreateDriverSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    license_number = serializers.CharField(required=False, allow_blank=True)

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=User.Roles.DRIVER
        )

        driver = DriverProfile.objects.create(
            user=user,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            license_number=validated_data.get('license_number')
        )

        return driver


class CreateClientSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    business_name = serializers.CharField()
    ruc = serializers.CharField()

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=User.Roles.CLIENT
        )

        client_profile = ClientProfile.objects.create(
            user=user,
            business_name=validated_data['business_name'],
            ruc=validated_data['ruc']
        )


        return client_profile

class CreateInternalClientSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    client_id = serializers.UUIDField()

    @transaction.atomic
    def create(self, validated_data):
        client_id = validated_data.pop('client_id')
        
        try:
            client_profile = ClientProfile.objects.get(id=client_id)
        except ClientProfile.DoesNotExist:
            raise serializers.ValidationError({"client_id": "Client profile not found."})

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=User.Roles.INTERNAL_CLIENT
        )

        internal_client = InternalClientProfile.objects.create(
            user=user,
            client=client_profile,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )

        return internal_client


class CreateInternalSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=User.Roles.INTERNAL
        )

        # Los usuarios INTERNAL no tienen perfil, solo el usuario
        return user
