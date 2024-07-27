from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from rest_framework import serializers

from authenbite.restaurants.models import (
    Cuisine,
    Restaurant,
    UserPreference,
    UserRestaurantInteraction,
)


class CuisineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuisine
        fields = ["id", "name"]


class RestaurantSerializer(serializers.ModelSerializer):
    distance = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = [
            "id",
            "name",
            "address",
            "latitude",
            "longitude",
            "phone_number",
            "website",
            "rating",
            "price_level",
            "cuisines",
            "created_at",
            "updated_at",
            "distance",
            "main_image_url",
        ]

    def get_distance(self, obj):
        if hasattr(obj, "distance"):
            if isinstance(obj.distance, Distance):
                return obj.distance.m  # Convert to meters
            return obj.distance
        return None

    def create(self, validated_data):
        lat = self.initial_data.get("latitude")
        lon = self.initial_data.get("longitude")
        if lat and lon:
            validated_data["location"] = Point(float(lon), float(lat))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        lat = self.initial_data.get("latitude")
        lon = self.initial_data.get("longitude")
        if lat and lon:
            instance.location = Point(float(lon), float(lat))
        return super().update(instance, validated_data)


class UserPreferenceSerializer(serializers.ModelSerializer):
    favorite_cuisines = CuisineSerializer(many=True, read_only=True)

    class Meta:
        model = UserPreference
        fields = [
            "id",
            "user",
            "favorite_cuisines",
            "preferred_price_level",
            "preferred_rating",
        ]


class UserRestaurantInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRestaurantInteraction
        fields = [
            "id",
            "user",
            "restaurant",
            "liked",
            "visited",
            "user_rating",
            "interaction_date",
        ]
        read_only_fields = ["user", "interaction_date"]
