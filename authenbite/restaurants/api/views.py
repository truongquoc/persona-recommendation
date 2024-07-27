from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from authenbite.restaurants.api.filters import RestaurantFilter
from authenbite.restaurants.api.serializers import (
    CuisineSerializer,
    RestaurantSerializer,
    UserPreferenceSerializer,
    UserRestaurantInteractionSerializer,
)
from authenbite.restaurants.models import (
    Cuisine,
    Restaurant,
    UserPreference,
    UserRestaurantInteraction,
)
from authenbite.users.models import Persona


class RestaurantViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    queryset = Restaurant.objects.all()
    pagination_class = PageNumberPagination
    filterset_class = RestaurantFilter
    search_fields = ["name", "address"]
    ordering_fields = ["name", "rating", "price_level", "distance"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        lat = self.request.query_params.get("lat")
        lon = self.request.query_params.get("lon")

        if lat and lon:
            user_location = Point(float(lon), float(lat), srid=4326)
            queryset = queryset.annotate(distance=Distance("location", user_location))

        suggest = self.request.query_params.get("suggest", "").lower() == "true"
        if suggest and user.is_authenticated:
            preferences, created = UserPreference.objects.get_or_create(user=user)

            filter_conditions = Q()
            if preferences.favorite_cuisines.exists():
                filter_conditions |= Q(cuisines__in=preferences.favorite_cuisines.all())
            if preferences.preferred_price_level:
                filter_conditions |= Q(
                    price_level__lte=preferences.preferred_price_level
                )
            if preferences.preferred_rating:
                filter_conditions |= Q(rating__gte=preferences.preferred_rating)

            queryset = (
                queryset.filter(filter_conditions)
                .exclude(
                    userrestaurantinteraction__user=user,
                    userrestaurantinteraction__liked=False,
                )
                .distinct()
            )

            # Persona-based filtering
            if user.profile.persona:
                persona = user.profile.persona
                if persona.name == Persona.ESCAPIST:
                    queryset = queryset.filter(adventure_rating__gte=7).order_by(
                        "-adventure_rating", "-rating"
                    )
                elif persona.name == Persona.LEARNER:
                    queryset = queryset.filter(cultural_significance__gte=7).order_by(
                        "-cultural_significance", "-rating"
                    )
                elif persona.name == Persona.PLANNER:
                    queryset = queryset.filter(planning_friendly=True).order_by(
                        "-rating", "price_level"
                    )
                elif persona.name == Persona.DREAMER:
                    queryset = queryset.filter(instagram_worthy=True).order_by(
                        "-instagram_worthiness", "-rating"
                    )

        return queryset

    @action(detail=False, methods=["GET"], permission_classes=[IsAuthenticated])
    def persona_recommendations(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        queryset = self.filter_queryset(self.get_queryset())
        persona = user.profile.persona

        if persona:
            if persona.name == Persona.ESCAPIST:
                queryset = queryset.order_by("-adventure_rating", "-rating")
            elif persona.name == Persona.LEARNER:
                queryset = queryset.order_by("-cultural_significance", "-rating")
            elif persona.name == Persona.PLANNER:
                queryset = queryset.filter(planning_friendly=True).order_by(
                    "-rating", "price_level"
                )
            elif persona.name == Persona.DREAMER:
                queryset = queryset.filter(instagram_worthy=True).order_by(
                    "-instagram_worthiness", "-rating"
                )

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # If pagination is not required
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["GET"], permission_classes=[IsAuthenticated])
    def search(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.paginate_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def nearest(self, request):
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")

        if not lat or not lon:
            return Response(
                {"error": "Latitude and longitude are required"}, status=400
            )

        user_location = Point(float(lon), float(lat), srid=4326)

        queryset = Restaurant.objects.annotate(
            distance=Distance("location", user_location)
        ).order_by("distance")
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CuisineViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Cuisine.objects.all()
    serializer_class = CuisineSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]
    filterset_fields = ["name"]

    @action(detail=False, methods=["get"])
    def popular(self, request):
        # This is a placeholder for a "popular cuisines" feature
        # You might implement this based on the number of restaurants or user preferences
        popular_cuisines = self.get_queryset().order_by("?")[:5]  # Random 5 for now
        serializer = self.get_serializer(popular_cuisines, many=True)
        return Response(serializer.data)


class UserPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = UserPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserPreference.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get", "put", "patch"])
    def me(self, request):
        user_preference, created = UserPreference.objects.get_or_create(
            user=request.user
        )

        if request.method == "GET":
            serializer = self.get_serializer(user_preference)
            return Response(serializer.data)

        elif request.method in ["PUT", "PATCH"]:
            serializer = self.get_serializer(
                user_preference, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def add_favorite_cuisine(self, request):
        user_preference, created = UserPreference.objects.get_or_create(
            user=request.user
        )
        cuisine_id = request.data.get("cuisine_id")

        if not cuisine_id:
            return Response(
                {"error": "cuisine_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cuisine = Cuisine.objects.get(id=cuisine_id)
            user_preference.favorite_cuisines.add(cuisine)
            serializer = self.get_serializer(user_preference)
            return Response(serializer.data)
        except Cuisine.DoesNotExist:
            return Response(
                {"error": "Cuisine not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"])
    def remove_favorite_cuisine(self, request):
        user_preference, created = UserPreference.objects.get_or_create(
            user=request.user
        )
        cuisine_id = request.data.get("cuisine_id")

        if not cuisine_id:
            return Response(
                {"error": "cuisine_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cuisine = Cuisine.objects.get(id=cuisine_id)
            user_preference.favorite_cuisines.remove(cuisine)
            serializer = self.get_serializer(user_preference)
            return Response(serializer.data)
        except Cuisine.DoesNotExist:
            return Response(
                {"error": "Cuisine not found"}, status=status.HTTP_404_NOT_FOUND
            )


class UserRestaurantInteractionViewSet(viewsets.ModelViewSet):
    serializer_class = UserRestaurantInteractionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["liked", "visited", "user_rating"]

    def get_queryset(self):
        return UserRestaurantInteraction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"])
    def like_restaurant(self, request):
        restaurant_id = request.data.get("restaurant_id")
        if not restaurant_id:
            return Response(
                {"error": "restaurant_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
            interaction, created = UserRestaurantInteraction.objects.get_or_create(
                user=request.user, restaurant=restaurant, defaults={"liked": True}
            )
            if not created:
                interaction.liked = True
                interaction.save()
            serializer = self.get_serializer(interaction)
            return Response(serializer.data)
        except Restaurant.DoesNotExist:
            return Response(
                {"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"])
    def unlike_restaurant(self, request):
        restaurant_id = request.data.get("restaurant_id")
        if not restaurant_id:
            return Response(
                {"error": "restaurant_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
            interaction = UserRestaurantInteraction.objects.get(
                user=request.user, restaurant=restaurant
            )
            interaction.liked = False
            interaction.save()
            serializer = self.get_serializer(interaction)
            return Response(serializer.data)
        except Restaurant.DoesNotExist:
            return Response(
                {"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except UserRestaurantInteraction.DoesNotExist:
            return Response(
                {"error": "Interaction not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"])
    def mark_visited(self, request):
        restaurant_id = request.data.get("restaurant_id")
        if not restaurant_id:
            return Response(
                {"error": "restaurant_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
            interaction, created = UserRestaurantInteraction.objects.get_or_create(
                user=request.user, restaurant=restaurant, defaults={"visited": True}
            )
            if not created:
                interaction.visited = True
                interaction.save()
            serializer = self.get_serializer(interaction)
            return Response(serializer.data)
        except Restaurant.DoesNotExist:
            return Response(
                {"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"])
    def rate_restaurant(self, request):
        restaurant_id = request.data.get("restaurant_id")
        rating = request.data.get("rating")
        if not restaurant_id or rating is None:
            return Response(
                {"error": "restaurant_id and rating are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return Response(
                    {"error": "Rating must be between 1 and 5"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            restaurant = Restaurant.objects.get(id=restaurant_id)
            interaction, created = UserRestaurantInteraction.objects.get_or_create(
                user=request.user,
                restaurant=restaurant,
                defaults={"user_rating": rating},
            )
            if not created:
                interaction.user_rating = rating
                interaction.save()
            serializer = self.get_serializer(interaction)
            return Response(serializer.data)
        except Restaurant.DoesNotExist:
            return Response(
                {"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {"error": "Invalid rating value"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["get"])
    def liked_restaurants(self, request):
        liked_interactions = self.get_queryset().filter(liked=True)
        serializer = self.get_serializer(liked_interactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def visited_restaurants(self, request):
        visited_interactions = self.get_queryset().filter(visited=True)
        serializer = self.get_serializer(visited_interactions, many=True)
        return Response(serializer.data)
