from rest_framework import serializers
from ..models import User


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'email', 'role')
        read_only_fields = ('role',)


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'role')
        extra_kwargs = {'password': {'write_only': True}}

    def validate_role(self, value):
        request = self.context['request']
        creator = request.user

        if creator.role == User.Roles.ADMIN:
            return value

        if creator.role == User.Roles.CLIENT:
            if value != User.Roles.INTERNAL_CLIENT:
                raise serializers.ValidationError(
                    "Clients can only create internal clients"
                )
            return value

        raise serializers.ValidationError(
            "You are not allowed to create users"
        )

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)