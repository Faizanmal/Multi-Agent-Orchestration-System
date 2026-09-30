from django.apps import AppConfig


class ApiIntegrationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api_integrations"

    def ready(self):
        import sys

        skip_cmds = {
            "migrate",
            "makemigrations",
            "seed_integrations",
            "seed_ai_models",
            "check",
            "collectstatic",
            "test",
            "shell",
            "createsuperuser",
            "showmigrations",
        }
        if any(cmd in sys.argv for cmd in skip_cmds) or any(
            a.startswith("seed_") for a in sys.argv
        ):
            return
        try:
            from .scheduler import start_scheduler

            start_scheduler()
        except Exception as e:  # noqa: BLE001
            import logging

            logging.getLogger(__name__).warning(
                f"Could not start automation scheduler: {e}"
            )
