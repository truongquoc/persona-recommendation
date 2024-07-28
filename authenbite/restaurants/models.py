from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import F, Func
from django.utils import timezone

User = get_user_model()


class Cuisine(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class RestaurantManager(models.Manager):
    def open_now(self):
        current_time = timezone.localtime()
        day_name = current_time.strftime("%A")
        current_minutes = current_time.hour * 60 + current_time.minute

        return (
            self.filter(opening_hours__has_key=day_name)
            .annotate(
                start_minutes=Func(
                    F("opening_hours"),
                    day_name,
                    function="jsonb_extract_path_text",
                    output_field=models.IntegerField(),
                ),
                end_minutes=Func(
                    F("opening_hours"),
                    day_name,
                    function="jsonb_extract_path_text",
                    output_field=models.IntegerField(),
                ),
            )
            .filter(start_minutes__lte=current_minutes, end_minutes__gt=current_minutes)
        )


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
    vegan_options = models.BooleanField(default=False)
    # New fields for opening hours and review summary
    review_summary = models.TextField(blank=True, null=True)
    opening_hours = models.JSONField(null=True, blank=True)
    opening_hours_display = models.TextField(blank=True, null=True)

    objects = RestaurantManager()

    def is_open(self, current_time=None):
        if not self.opening_hours:
            return False

        if current_time is None:
            current_time = timezone.localtime()

        day_name = current_time.strftime("%A")
        current_minutes = current_time.hour * 60 + current_time.minute

        if day_name in self.opening_hours:
            start_minutes, end_minutes = self.opening_hours[day_name]
            return start_minutes <= current_minutes < end_minutes

        return False

    def set_opening_hours(self, hours_data):
        self.opening_hours = [[] for _ in range(7)]
        days = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        for day_data in hours_data:
            day = days.index(day_data["day"].lower())
            for hour_range in day_data["hours"].split(", "):
                start, end = hour_range.split(" to ")
                start_minutes = self.time_to_minutes(start)
                end_minutes = self.time_to_minutes(end)
                self.opening_hours[day].append([start_minutes, end_minutes, 0])
        self.opening_hours_display = str(hours_data)

    @staticmethod
    def time_to_minutes(time_str):
        t = datetime.strptime(time_str, "%I %p").time()
        return t.hour * 60 + t.minute

    @staticmethod
    def minutes_to_time(minutes):
        return f"{minutes // 60:02d}:{minutes % 60:02d}"

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
