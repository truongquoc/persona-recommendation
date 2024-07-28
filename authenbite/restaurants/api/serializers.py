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
    opening_hours_formatted = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()

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
            "opening_hours_formatted",
            "is_open",
            "vegan_options",
        ]

    def get_distance(self, obj):
        if hasattr(obj, "distance"):
            if isinstance(obj.distance, Distance):
                return obj.distance.m  # Convert to meters
            return obj.distance
        return None

    def get_opening_hours_formatted(self, obj):
        if obj.opening_hours:
            formatted_hours = {}
            for day, hours in obj.opening_hours.items():
                if hours:
                    start_minutes, end_minutes = hours
                    formatted_hours[day] = (
                        f"{self.minutes_to_time(start_minutes)} - {self.minutes_to_time(end_minutes)}"
                    )
                else:
                    formatted_hours[day] = "Closed"
            return formatted_hours
        return None

    def get_is_open(self, obj):
        return obj.is_open()

    @staticmethod
    def minutes_to_time(minutes):
        hours, mins = divmod(minutes, 60)
        return f"{hours:02d}:{mins:02d}"

    def create(self, validated_data):
        lat = self.initial_data.get("latitude")
        lon = self.initial_data.get("longitude")
        if lat and lon:
            validated_data["location"] = Point(float(lon), float(lat))

        opening_hours = self.initial_data.get("opening_hours")
        if opening_hours:
            validated_data["opening_hours"] = self.format_opening_hours(opening_hours)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        lat = self.initial_data.get("latitude")
        lon = self.initial_data.get("longitude")
        if lat and lon:
            instance.location = Point(float(lon), float(lat))

        opening_hours = self.initial_data.get("opening_hours")
        if opening_hours:
            instance.opening_hours = self.format_opening_hours(opening_hours)

        return super().update(instance, validated_data)

    def format_opening_hours(self, opening_hours):
        formatted = {}
        for day_data in opening_hours:
            day = day_data["day"]
            hours = day_data["hours"]
            start, end = hours.split(" to ")
            start_minutes = self.time_to_minutes(start)
            end_minutes = self.time_to_minutes(end)
            if start_minutes is not None and end_minutes is not None:
                formatted[day] = [start_minutes, end_minutes]
        return formatted

    @staticmethod
    def time_to_minutes(time_str):
        pattern = r"^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)$"
        match = re.match(pattern, time_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2) or 0)
            period = match.group(3)

            if period == "PM" and hours != 12:
                hours += 12
            elif period == "AM" and hours == 12:
                hours = 0

            return hours * 60 + minutes
        else:
            print(f"Warning: Could not parse time string '{time_str}'")
            return None


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
