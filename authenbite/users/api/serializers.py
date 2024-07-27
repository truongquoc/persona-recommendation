from rest_framework import serializers

from authenbite.users.models import Persona, User, UserProfile


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "name"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        return value


class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = ["name", "description"]


class UserProfileSerializer(serializers.ModelSerializer):
    persona = PersonaSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "persona",
            "adventure_preference",
            "cultural_interest",
            "planning_detail",
            "travel_frequency",
        ]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        profile = instance.profile

        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()

        return super(UserSerializer, self).update(instance, validated_data)

    class Meta:
        model = User
        fields = ["id", "username", "name", "url", "profile"]

        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "username"}
        }
