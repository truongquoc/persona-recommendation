from django.contrib import admin

from authenbite.restaurants.models import (
    Cuisine,
    Restaurant,
    UserPreference,
    UserRestaurantInteraction,
)

admin.site.register(Cuisine)
admin.site.register(Restaurant)
admin.site.register(UserPreference)
admin.site.register(UserRestaurantInteraction)
