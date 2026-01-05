from rest_framework.routers import DefaultRouter
from .api.views import (
    ClientViewSet,
    DriverViewSet,
    InternalClientViewSet,
    InternalViewSet,
)

router = DefaultRouter()
router.register('clients', ClientViewSet, basename='client')
router.register('drivers', DriverViewSet, basename='driver')
router.register('internal-clients', InternalClientViewSet, basename='internal-client')
router.register('internals', InternalViewSet, basename='internal')

urlpatterns = router.urls