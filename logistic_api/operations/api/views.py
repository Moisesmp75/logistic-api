from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F
from ...users.models import User
from ..models import Operation, OperationStatus
from .serializers import (
    OperationSerializer,
    CreateOperationSerializer,
    UpdateOperationSerializer,
    OperationStatusSerializer,
    CreateOperationStatusSerializer,
    ReorderOperationStatusesSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=['Operations V1']),
    retrieve=extend_schema(tags=['Operations V1']),
    create=extend_schema(tags=['Operations V1']),
    update=extend_schema(tags=['Operations V1']),
    partial_update=extend_schema(tags=['Operations V1']),
    statuses=extend_schema(tags=['Operation Statuses V1']),
)
class OperationViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = Operation.objects.select_related('created_by').prefetch_related('statuses')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateOperationSerializer
        elif self.action in ["update", "partial_update"]:
            return UpdateOperationSerializer
        return OperationSerializer

    def get_queryset(self):
        user = self.request.user
        
        if user.role not in [User.Roles.ADMIN, User.Roles.INTERNAL]:
            raise PermissionDenied("You do not have permission to access this resource.")
        
        return self.queryset.all()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in [User.Roles.ADMIN, User.Roles.INTERNAL]:
            raise PermissionDenied("You do not have permission to create operations.")
        serializer.save(created_by=user)

    @extend_schema(
        request=CreateOperationSerializer,
        responses={201: OperationSerializer},
        description="Create a new operation"
    )
    def create(self, request, *args, **kwargs):
        input_serializer = CreateOperationSerializer(
            data=request.data,
            context={'request': request}
        )
        input_serializer.is_valid(raise_exception=True)
        operation = input_serializer.save()
        
        output_serializer = OperationSerializer(operation)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        operation = self.get_object()
        user = request.user
        
        if user.role not in [User.Roles.ADMIN, User.Roles.INTERNAL]:
            raise PermissionDenied("You do not have permission to update operations.")
        
        input_serializer = UpdateOperationSerializer(
            data=request.data,
            context={'request': request}
        )
        input_serializer.is_valid(raise_exception=True)
        validated_data = input_serializer.validated_data
        
        # Actualizar campos básicos
        if 'name' in validated_data:
            operation.name = validated_data['name']
        if 'description' in validated_data:
            operation.description = validated_data.get('description', '')
        if 'is_active' in validated_data:
            operation.is_active = validated_data['is_active']
        if 'is_finalized' in validated_data:
            operation.is_finalized = validated_data['is_finalized']
        
        # Actualizar driver si se proporciona
        if 'driver_id' in validated_data:
            driver_id = validated_data['driver_id']
            if driver_id:
                from ...profile.models import DriverProfile
                try:
                    driver = DriverProfile.objects.get(id=driver_id)
                    operation.driver = driver
                except DriverProfile.DoesNotExist:
                    return Response(
                        {"detail": f"Driver {driver_id} not found."},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                operation.driver = None
        
        # Actualizar orders si se proporcionan
        if 'order_ids' in validated_data:
            order_ids = validated_data['order_ids']
            from ...orders.models import Order
            if order_ids:
                Order.objects.filter(id__in=order_ids).update(operation=operation)
            # Si se envía una lista vacía, no se hace nada (mantiene los orders actuales)
            # Si se quiere remover todos, se puede hacer en otro endpoint
        
        operation.save()
        
        output_serializer = OperationSerializer(operation)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['get', 'post', 'put', 'delete'],
        url_path='statuses'
    )
    @extend_schema(
        tags=['Operation Statuses V1'],
        description="Manage statuses for an operation",
        request=CreateOperationStatusSerializer,
        responses={200: OperationStatusSerializer(many=True)},
    )
    def statuses(self, request, pk=None):
        """
        GET: List all statuses for the operation
        POST: Create a new status (optionally at a specific position)
        PUT: Reorder statuses
        DELETE: Delete a status (via query param ?status_id=...)
        """
        operation = self.get_object()
        user = request.user

        if user.role not in [User.Roles.ADMIN, User.Roles.INTERNAL]:
            raise PermissionDenied("You do not have permission to manage operation statuses.")

        if request.method == 'GET':
            statuses = operation.statuses.all()
            serializer = OperationStatusSerializer(statuses, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            # Crear nuevo estado
            serializer = CreateOperationStatusSerializer(
                data=request.data,
                context={'operation': operation}
            )
            serializer.is_valid(raise_exception=True)
            status_obj = serializer.save()
            
            output_serializer = OperationStatusSerializer(status_obj)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'PUT':
            # Reordenar estados
            serializer = ReorderOperationStatusesSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            with transaction.atomic():
                for item in serializer.validated_data['statuses']:
                    status_id = item['status_id']
                    new_order = item['new_order']
                    
                    try:
                        status_obj = OperationStatus.objects.get(
                            id=status_id,
                            operation=operation
                        )
                    except OperationStatus.DoesNotExist:
                        return Response(
                            {"detail": f"Status {status_id} not found in this operation."},
                            status=status.HTTP_404_NOT_FOUND
                        )
                    
                    old_order = status_obj.order
                    
                    if old_order == new_order:
                        continue
                    
                    # Reordenar otros estados
                    if old_order < new_order:
                        # Moviendo hacia abajo
                        OperationStatus.objects.filter(
                            operation=operation,
                            order__gt=old_order,
                            order__lte=new_order
                        ).update(order=F('order') - 1)
                    else:
                        # Moviendo hacia arriba
                        OperationStatus.objects.filter(
                            operation=operation,
                            order__gte=new_order,
                            order__lt=old_order
                        ).update(order=F('order') + 1)
                    
                    status_obj.order = new_order
                    status_obj.save()
            
            # Retornar estados reordenados
            statuses = operation.statuses.all()
            output_serializer = OperationStatusSerializer(statuses, many=True)
            return Response(output_serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'DELETE':
            # Eliminar estado
            status_id = request.query_params.get('status_id')
            if not status_id:
                return Response(
                    {"detail": "status_id query parameter is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                status_obj = OperationStatus.objects.get(
                    id=status_id,
                    operation=operation
                )
            except OperationStatus.DoesNotExist:
                return Response(
                    {"detail": "Status not found in this operation."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            deleted_order = status_obj.order
            
            with transaction.atomic():
                status_obj.delete()
                # Reordenar estados restantes
                OperationStatus.objects.filter(
                    operation=operation,
                    order__gt=deleted_order
                ).update(order=F('order') - 1)
            
            return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    retrieve=extend_schema(tags=['Operation Statuses V1']),
    update=extend_schema(tags=['Operation Statuses V1']),
    partial_update=extend_schema(tags=['Operation Statuses V1']),
    destroy=extend_schema(tags=['Operation Statuses V1']),
)
class OperationStatusViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet para operaciones individuales sobre estados.
    Usar el action 'statuses' del OperationViewSet para la mayoría de operaciones.
    """
    queryset = OperationStatus.objects.select_related('operation')
    permission_classes = [IsAuthenticated]
    serializer_class = OperationStatusSerializer

    def get_queryset(self):
        user = self.request.user
        
        if user.role not in [User.Roles.ADMIN, User.Roles.INTERNAL]:
            raise PermissionDenied("You do not have permission to access this resource.")
        
        return self.queryset.all()

    def perform_destroy(self, instance):
        user = self.request.user
        if user.role not in [User.Roles.ADMIN, User.Roles.INTERNAL]:
            raise PermissionDenied("You do not have permission to delete operation statuses.")
        
        operation = instance.operation
        deleted_order = instance.order
        
        with transaction.atomic():
            instance.delete()
            # Reordenar estados restantes
            OperationStatus.objects.filter(
                operation=operation,
                order__gt=deleted_order
            ).update(order=F('order') - 1)
