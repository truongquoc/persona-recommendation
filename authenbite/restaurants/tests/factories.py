# factories.py

import factory
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from factory import Faker, LazyFunction, SubFactory, post_generation
from factory.django import DjangoModelFactory

from authenbite.restaurants.models import (
    Cuisine,
    Restaurant,
    UserPreference,
    UserRestaurantInteraction,
)
from authenbite.users.tests.factories import UserFactory

User = get_user_model()


class CuisineFactory(DjangoModelFactory):
    class Meta:
        model = Cuisine

    name = factory.Faker("word")


fake = Faker()


class RestaurantFactory(DjangoModelFactory):
    class Meta:
        model = Restaurant

    name = factory.Faker("company")
    address = factory.Faker("address")
    location = factory.LazyAttribute(
        lambda _: Point(
            float(fake.longitude()),
            float(fake.latitude()),
        )
    )
    rating = factory.Faker("pyfloat", min_value=1, max_value=5, right_digits=1)
    price_level = factory.Faker("random_int", min=1, max=4)
    adventure_rating = factory.Faker("random_int", min=1, max=10)
    cultural_significance = factory.Faker("random_int", min=1, max=10)
    planning_friendly = factory.Faker("boolean")
    instagram_worthy = factory.Faker("boolean")
    instagram_worthiness = factory.Faker("random_int", min=1, max=10)
    main_image_url = factory.Faker("image_url")

    @factory.post_generation
    def cuisines(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for cuisine in extracted:
                self.cuisines.add(cuisine)


class UserPreferenceFactory(DjangoModelFactory):
    class Meta:
        model = UserPreference

    user = factory.SubFactory(UserFactory)
    preferred_price_level = factory.Faker("random_int", min=1, max=4)
    preferred_rating = factory.Faker(
        "pyfloat", min_value=1, max_value=5, right_digits=1
    )

    @factory.post_generation
    def favorite_cuisines(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for cuisine in extracted:
                self.favorite_cuisines.add(cuisine)


class UserRestaurantInteractionFactory(DjangoModelFactory):
    class Meta:
        model = UserRestaurantInteraction

    user = factory.SubFactory(UserFactory)
    restaurant = factory.SubFactory(RestaurantFactory)
    liked = factory.Faker("boolean")
