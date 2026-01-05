from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logistic_api.users'
    label = 'users'

    def ready(self):
        # from . import signals
        pass
