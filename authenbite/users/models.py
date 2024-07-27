from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# In your models.py file


class User(AbstractUser):
    """
    Default custom user model for authenbite.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})


class Persona(models.Model):
    ESCAPIST = "ES"
    LEARNER = "LR"
    PLANNER = "PL"
    DREAMER = "DR"

    PERSONA_CHOICES = [
        (ESCAPIST, "Escapist"),
        (LEARNER, "Learner"),
        (PLANNER, "Planner"),
        (DREAMER, "Dreamer"),
    ]

    name = models.CharField(max_length=2, choices=PERSONA_CHOICES, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.get_name_display()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    persona = models.ForeignKey(
        Persona, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Additional fields that might be useful for personalization
    adventure_preference = models.IntegerField(
        default=5, choices=[(i, i) for i in range(1, 11)]
    )  # 1-10 scale
    cultural_interest = models.IntegerField(
        default=5, choices=[(i, i) for i in range(1, 11)]
    )  # 1-10 scale
    planning_detail = models.IntegerField(
        default=5, choices=[(i, i) for i in range(1, 11)]
    )  # 1-10 scale
    travel_frequency = models.IntegerField(
        default=2, choices=[(1, "Rarely"), (2, "Occasionally"), (3, "Frequently")]
    )

    def __str__(self):
        return f"{self.user.username}'s profile"
