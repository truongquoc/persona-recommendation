from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

User = get_user_model()


class Cuisine(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Restaurant(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255)
    location = models.PointField(srid=4326, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True)
    price_level = models.IntegerField(
        choices=[(1, "$"), (2, "$$"), (3, "$$$"), (4, "$$$$"), (5, "$$$$$")], null=True
    )
    cuisines = models.ManyToManyField(Cuisine)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    adventure_rating = models.IntegerField(
        default=5, validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    cultural_significance = models.IntegerField(
        default=5, validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    planning_friendly = models.BooleanField(default=False)
    instagram_worthy = models.BooleanField(default=False)
    instagram_worthiness = models.IntegerField(
        default=5, validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    main_image_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def latitude(self):
        return self.location.y if self.location else None

    @property
    def longitude(self):
        return self.location.x if self.location else None


class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    favorite_cuisines = models.ManyToManyField(Cuisine)
    preferred_price_level = models.IntegerField(
        choices=[(1, "$"), (2, "$$"), (3, "$$$"), (4, "$$$$"), (5, "$$$$$")], null=True
    )
    preferred_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True)

    def __str__(self):
        return f"{self.user.username}'s preferences"


class UserRestaurantInteraction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    liked = models.BooleanField(null=True)
    visited = models.BooleanField(default=False)
    user_rating = models.IntegerField(
        choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], null=True
    )
    interaction_date = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "restaurant")

    def __str__(self):
        return f"{self.user.username}'s interaction with {self.restaurant.name}"
