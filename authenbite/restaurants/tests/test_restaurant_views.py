from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from authenbite.restaurants.models import UserPreference, UserRestaurantInteraction
from authenbite.restaurants.tests.factories import (
    CuisineFactory,
    RestaurantFactory,
    UserFactory,
    UserPreferenceFactory,
)
from authenbite.users.models import Persona
from authenbite.users.tests.factories import PersonaFactory, UserProfileFactory

User = get_user_model()


class RestaurantViewSetTestCase(APITestCase):
    def setUp(self):
        # Create personas only once
        self.personas = {
            Persona.ESCAPIST: PersonaFactory(name=Persona.ESCAPIST),
            Persona.LEARNER: PersonaFactory(name=Persona.LEARNER),
            Persona.PLANNER: PersonaFactory(name=Persona.PLANNER),
            Persona.DREAMER: PersonaFactory(name=Persona.DREAMER),
        }

        # Create users with different personas
        self.user = UserFactory()
        self.escapist_user = UserFactory(username="escapist")
        self.learner_user = UserFactory(username="learner")
        self.planner_user = UserFactory(username="planner")
        self.dreamer_user = UserFactory(username="dreamer")

        # Create UserProfile and UserPreference for each user
        for user, persona in zip(
            [
                self.user,
                self.escapist_user,
                self.learner_user,
                self.planner_user,
                self.dreamer_user,
            ],
            [None, Persona.ESCAPIST, Persona.LEARNER, Persona.PLANNER, Persona.DREAMER],
        ):
            UserProfileFactory(user=user, persona=self.personas.get(persona))
            UserPreferenceFactory(user=user)

        self.cuisine = CuisineFactory(name="Italian")
        self.restaurants = RestaurantFactory.create_batch(15)
        self.restaurants[0].cuisines.add(self.cuisine)

    def test_list_restaurants(self):
        self.client.force_authenticate(user=self.user)
        url = "/api/restaurants/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)  # Default page size
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_retrieve_restaurant(self):
        self.client.force_authenticate(user=self.user)
        url = f"/api/restaurants/{self.restaurants[0].pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.restaurants[0].name)

    def test_search_restaurants(self):
        self.client.force_authenticate(user=self.user)
        url = "/api/restaurants/"
        response = self.client.get(url, {"name": self.restaurants[0].name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data["results"]), 0)

    def test_nearest_restaurants(self):
        self.client.force_authenticate(user=self.user)
        url = "/api/restaurants/nearest/"
        response = self.client.get(url, {"lat": 1, "lon": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data["results"]), 0)
        self.assertIn("distance", response.data["results"][0])
        self.assertIsInstance(response.data["results"][0]["distance"], float)

    def test_suggest_restaurants(self):
        self.client.force_authenticate(user=self.user)
        UserPreference.objects.filter(user=self.user).update(
            preferred_price_level=2, preferred_rating=4.0
        )
        self.user.userpreference.favorite_cuisines.add(self.cuisine)

        url = "/api/restaurants/"
        response = self.client.get(url, {"suggest": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data["results"]), 0)

    def test_filter_favorite_restaurants(self):
        self.client.force_authenticate(user=self.user)
        UserRestaurantInteraction.objects.create(
            user=self.user, restaurant=self.restaurants[0], liked=True
        )

        url = "/api/restaurants/"
        response = self.client.get(url, {"is_favorite": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        response = self.client.get(url, {"is_favorite": "false"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)  # Default page size

    def test_get_queryset_with_suggest_and_persona(self):
        for user in [
            self.escapist_user,
            self.learner_user,
            self.planner_user,
            self.dreamer_user,
        ]:
            self.client.force_authenticate(user=user)
            UserPreference.objects.filter(user=user).update(
                preferred_price_level=4, preferred_rating=4.0
            )
            user.userpreference.favorite_cuisines.add(self.cuisine)

            url = "/api/restaurants/"
            response = self.client.get(url, {"suggest": "true"})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertGreater(len(response.data["results"]), 0)

    def test_persona_recommendations(self):
        for user in [
            self.escapist_user,
            self.learner_user,
            self.planner_user,
            self.dreamer_user,
        ]:
            self.client.force_authenticate(user=user)
            response = self.client.get("/api/restaurants/persona_recommendations/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertGreater(len(response.data["results"]), 0)

    def test_filter_restaurants(self):
        self.client.force_authenticate(user=self.user)
        url = "/api/restaurants/"
        response = self.client.get(url, {"price_level": "2"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data["results"]), 0)

        response = self.client.get(url, {"price_level": "5"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_persona_recommendations_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/restaurants/persona_recommendations/")
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_pagination(self):
        self.client.force_authenticate(user=self.user)
        url = "/api/restaurants/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)  # Default page size
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

        # Test second page
        response = self.client.get(response.data["next"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data["results"]), 5
        )  # 15 total, so 5 on second page
        self.assertIsNone(response.data["next"])
        self.assertIsNotNone(response.data["previous"])

    def test_custom_page_size(self):
        self.client.force_authenticate(user=self.user)
        url = "/api/restaurants/"
        response = self.client.get(url, {"page_size": 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNotNone(response.data["next"])
