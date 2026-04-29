from django.apps import AppConfig

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'

    # Cette fonction dit à Django d'écouter les signaux au démarrage
    def ready(self):
        import chat.signals