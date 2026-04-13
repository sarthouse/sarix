from django.apps import AppConfig


class InventoryConfig(AppConfig):
    name = 'apps.inventory'

    def ready(self):
        import apps.inventory.signals  # noqa
