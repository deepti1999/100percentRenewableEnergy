from django.apps import AppConfig


class SimulatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'simulator'
    
    def ready(self):
        """Register signals when app is ready"""
        import os
        if not os.environ.get('DISABLE_SIGNALS'):
            import simulator.signals  # This will register the signal handlers
