from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from authenbite.restaurants.urls import router as restaurant_router
from authenbite.users.api.views import UserViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)

# Include restaurant routes
router.registry.extend(restaurant_router.registry)

app_name = "api"
urlpatterns = router.urls
