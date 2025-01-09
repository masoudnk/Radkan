from django.apps import AppConfig


class EmployerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'employer'

    def ready(self):
        import employer.signals
def get_this_app_name():
    return EmployerConfig.name