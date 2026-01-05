from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from ...users.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from ...profile.models import (
    ClientProfile,
    DriverProfile,
    InternalClientProfile
)
from ...profile.api.serializers import (
    CreateClientSerializer,
    CreateDriverSerializer,
    CreateInternalClientSerializer,
    CreateInternalSerializer,
    InternalClientSerializer,
    DriverProfileSerializer,
    ClientProfileSerializer
)
from ...users.api.serializers import UserSerializer

@extend_schema_view(
    list=extend_schema(tags=['Drivers V1']),
    retrieve=extend_schema(tags=['Drivers V1']),
    create=extend_schema(tags=['Drivers V1']),
    update=extend_schema(tags=['Drivers V1']),
    partial_update=extend_schema(tags=['Drivers V1']),
    destroy=extend_schema(tags=['Drivers V1']),
)
class DriverViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = DriverProfile.objects.select_related('user')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateDriverSerializer
        return DriverProfileSerializer
    
    @extend_schema(
        request=CreateDriverSerializer,
        responses={201: DriverProfileSerializer},
        description="Create a new driver (creates user + driver profile)"
    )
    def create(self, request, *args, **kwargs):
        input_serializer = CreateDriverSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        client_profile = input_serializer.save() 

        output_serializer = DriverProfileSerializer(client_profile)
        return Response(output_serializer.data, status=201)


@extend_schema_view(
    list=extend_schema(tags=['Clients V1']),
    retrieve=extend_schema(tags=['Clients V1']),
    create=extend_schema(tags=['Clients V1']),
    update=extend_schema(tags=['Clients V1']),
    partial_update=extend_schema(tags=['Clients V1']),
)
class ClientViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = ClientProfile.objects.select_related('user')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateClientSerializer
        return ClientProfileSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Roles.ADMIN:
            return self.queryset
        return self.queryset.filter(user=user)
    
    @extend_schema(
        request=CreateClientSerializer,
        responses={201: ClientProfileSerializer},
        description="Create a client (creates user + client profile)"
    )
    def create(self, request, *args, **kwargs):
        input_serializer = CreateClientSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        client_profile = input_serializer.save() 

        output_serializer = ClientProfileSerializer(client_profile)
        return Response(output_serializer.data, status=201)


@extend_schema_view(
    list=extend_schema(tags=['Internal Clients V1']),
    retrieve=extend_schema(tags=['Internal Clients V1']),
    create=extend_schema(tags=['Internal Clients V1']),
    update=extend_schema(tags=['Internal Clients V1']),
    partial_update=extend_schema(tags=['Internal Clients V1']),
    destroy=extend_schema(tags=['Internal Clients V1']),
)
class InternalClientViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = InternalClientProfile.objects.select_related('user', 'client')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateInternalClientSerializer
        return InternalClientSerializer

    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Roles.ADMIN:
            return self.queryset.all()
        elif user.role == User.Roles.CLIENT:
            try:
                client_profile = user.client_profile
                return self.queryset.filter(client=client_profile)
            except ClientProfile.DoesNotExist:
                return self.queryset.none()
        else:
            raise PermissionDenied("You do not have permission to access this resource.")

    @extend_schema(
        request=CreateInternalClientSerializer,
        responses={201: InternalClientSerializer},
        description="Create an internal client (creates user + internal client profile)"
    )
    def create(self, request, *args, **kwargs):
        input_serializer = CreateInternalClientSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        internal_client = input_serializer.save()

        output_serializer = InternalClientSerializer(internal_client)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(tags=['Internals V1']),
    retrieve=extend_schema(tags=['Internals V1']),
    create=extend_schema(tags=['Internals V1']),
)
class InternalViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = User.objects.filter(role=User.Roles.INTERNAL)
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateInternalSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        
        if user.role not in [User.Roles.ADMIN, User.Roles.INTERNAL]:
            raise PermissionDenied("You do not have permission to access this resource.")
        
        if user.role == User.Roles.ADMIN:
            return self.queryset.all()
        
        # INTERNAL puede ver todos los internos
        return self.queryset.all()

    @extend_schema(
        request=CreateInternalSerializer,
        responses={201: UserSerializer},
        description="Create an internal user (creates user with INTERNAL role)"
    )
    def create(self, request, *args, **kwargs):
        user = self.request.user
        
        if user.role not in [User.Roles.ADMIN, User.Roles.INTERNAL]:
            raise PermissionDenied("You do not have permission to create internal users.")
        
        input_serializer = CreateInternalSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        internal_user = input_serializer.save()

        output_serializer = UserSerializer(internal_user)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
