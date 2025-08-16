from django.apps import AppConfig


class EnergyDashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'energy_dashboard'
    verbose_name = 'ForgeForward Energy Dashboard'
    
    def ready(self):
        import energy_dashboard.signals