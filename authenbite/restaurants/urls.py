from rest_framework.routers import DefaultRouter

from authenbite.restaurants.api.views import (
    CuisineViewSet,
    RestaurantViewSet,
    UserPreferenceViewSet,
    UserRestaurantInteractionViewSet,
)

router = DefaultRouter()
router.register(r"cuisines", CuisineViewSet)
router.register(r"restaurants", RestaurantViewSet)
router.register(r"user-preferences", UserPreferenceViewSet, basename="user-preference")
router.register(
    r"user-restaurant-interactions",
    UserRestaurantInteractionViewSet,
    basename="user-restaurant-interaction",
)

urlpatterns = router.urls
