from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from authenbite.users.models import Persona, User, UserProfile

from .serializers import PersonaSerializer, UserCreateSerializer, UserSerializer


class PersonaViewSet(ReadOnlyModelViewSet):
    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer
    permission_classes = [AllowAny]  # Allow any user to view personas


class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "username"

    def get_queryset(self, *args, **kwargs):
        assert isinstance(self.request.user.id, int)
        return self.queryset.filter(id=self.request.user.id)

    def get_permissions(self):
        if self.action == "signup":
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(detail=False, methods=["post"])
    def signup(self, request):
        create_serializer = UserCreateSerializer(data=request.data)
        if create_serializer.is_valid():
            try:
                validate_password(create_serializer.validated_data["password"])
            except ValidationError as e:
                return Response(
                    {"password": e.messages}, status=status.HTTP_400_BAD_REQUEST
                )

            user = create_serializer.save()
            user.set_password(create_serializer.validated_data["password"])
            user.save()

            # Create UserProfile
            UserProfile.objects.create(user=user)

            # Use UserSerializer with context for the response
            user_serializer = UserSerializer(user, context={"request": request})
            return Response(user_serializer.data, status=status.HTTP_201_CREATED)
        return Response(create_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def set_persona(self, request):
        user = request.user
        persona = get_object_or_404(Persona, name=request.data.get("persona"))
        user.profile.persona = persona
        user.profile.save()
        return Response({"status": "persona set"})
