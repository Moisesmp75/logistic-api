from rest_framework.routers import DefaultRouter
from .api.views import (
    OperationViewSet,
    OperationStatusViewSet,
)

router = DefaultRouter()
router.register('operations', OperationViewSet, basename='operation')
router.register('operation-statuses', OperationStatusViewSet, basename='operation-status')

urlpatterns = router.urls

