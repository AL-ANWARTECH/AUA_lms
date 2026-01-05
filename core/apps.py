from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'AUA Learning Management System'

    def ready(self):
        """
        Import signals when the app is ready.
        This ensures that event listeners (like sending notifications 
        when a grade is saved) are registered correctly.
        """
        import core.signals