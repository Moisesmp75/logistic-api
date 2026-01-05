from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from ..models import User
from .serializers import CreateUserSerializer, UserSerializer
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(tags=['Users V1']),
    retrieve=extend_schema(tags=['Users V1']),
    create=extend_schema(tags=['Users V1']),
    update=extend_schema(tags=['Users V1']),
    partial_update=extend_schema(tags=['Users V1']),
)
class UserViewSet(
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """
    Updates and retrieves user accounts
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role == User.Roles.ADMIN:
            return User.objects.all()

        return User.objects.filter(id=user.id)

    @extend_schema(
        request=CreateUserSerializer,
        responses={201: UserSerializer},
        description="Create a new user account"
    )
    def create(self, request, *args, **kwargs):
        serializer = CreateUserSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = User.objects.create_user(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            role=serializer.validated_data.get('role', User.Roles.CLIENT),
        )

        output_serializer = UserSerializer(user)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
