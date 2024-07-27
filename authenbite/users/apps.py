from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "authenbite.users"

    def ready(self):
        try:
            import authenbite.users.signals  # noqa: F401
        except ImportError:
            pass
