from django.core.management.base import BaseCommand

from Multi_model_Intelligence.catalog import seed_default_ai_models


class Command(BaseCommand):
    help = "Seed default AI model configurations (Groq, OpenAI, Anthropic, Google)"

    def handle(self, *args, **options):
        created = seed_default_ai_models()
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(created)} AI model(s)"))
        for model_id in created:
            self.stdout.write(f"  - {model_id}")
