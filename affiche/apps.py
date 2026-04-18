from django.apps import AppConfig

# from core.decorators.register_signals import register_signals



class AfficheConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "affiche"

    # @register_signals()
    # def ready(self) -> None:
    #     pass
