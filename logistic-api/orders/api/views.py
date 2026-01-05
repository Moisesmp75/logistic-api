from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from ...users.models import User
from ...profile.models import ClientProfile
from ..models import Order
from .serializers import (
    OrderSerializer,
    CreateOrderSerializer,
    UpdateOrderSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=['Orders V1']),
    retrieve=extend_schema(tags=['Orders V1']),
    create=extend_schema(tags=['Orders V1']),
    update=extend_schema(tags=['Orders V1']),
    partial_update=extend_schema(tags=['Orders V1']),
)
class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = Order.objects.select_related('client', 'operation', 'created_by')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateOrderSerializer
        elif self.action in ["update", "partial_update"]:
            return UpdateOrderSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Roles.ADMIN:
            return self.queryset.all()
        elif user.role == User.Roles.INTERNAL:
            return self.queryset.all()
        elif user.role == User.Roles.CLIENT:
            try:
                client_profile = user.client_profile
                return self.queryset.filter(client=client_profile)
            except ClientProfile.DoesNotExist:
                return self.queryset.none()
        elif user.role == User.Roles.INTERNAL_CLIENT:
            try:
                client_profile = user.internal_client_profile.client
                return self.queryset.filter(client=client_profile)
            except:
                return self.queryset.none()
        elif user.role == User.Roles.DRIVER:
            # Drivers solo ven pedidos de sus operativos
            try:
                driver_profile = user.driver_profile
                operations = driver_profile.operations.all()
                return self.queryset.filter(operation__in=operations)
            except:
                return self.queryset.none()
        else:
            raise PermissionDenied("You do not have permission to access this resource.")

    @extend_schema(
        request=CreateOrderSerializer,
        responses={201: OrderSerializer},
        description="Create a new order"
    )
    def create(self, request, *args, **kwargs):
        user = request.user
        
        if user.role not in [User.Roles.CLIENT, User.Roles.INTERNAL_CLIENT]:
            raise PermissionDenied("Only clients and internal clients can create orders.")
        
        input_serializer = CreateOrderSerializer(
            data=request.data,
            context={'request': request}
        )
        input_serializer.is_valid(raise_exception=True)
        order = input_serializer.save()
        
        output_serializer = OrderSerializer(order)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        user = request.user
        
        # Solo el cliente propietario, ADMIN o INTERNAL pueden actualizar
        if user.role not in [User.Roles.ADMIN, User.Roles.INTERNAL]:
            if user.role in [User.Roles.CLIENT, User.Roles.INTERNAL_CLIENT]:
                # Verificar que el pedido pertenezca al cliente
                try:
                    if user.role == User.Roles.CLIENT:
                        client = user.client_profile
                    else:
                        client = user.internal_client_profile.client
                    
                    if order.client != client:
                        raise PermissionDenied("You can only update your own orders.")
                except:
                    raise PermissionDenied("You do not have permission to update this order.")
            else:
                raise PermissionDenied("You do not have permission to update orders.")
        
        input_serializer = UpdateOrderSerializer(
            order,
            data=request.data,
            partial=kwargs.get('partial', False)
        )
        input_serializer.is_valid(raise_exception=True)
        order = input_serializer.save()
        
        output_serializer = OrderSerializer(order)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
