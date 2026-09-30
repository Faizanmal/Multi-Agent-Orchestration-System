# ruff: noqa
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MonthlyUsage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "period",
                    models.DateField(help_text="First day of the metered month"),
                ),
                ("message_count", models.PositiveBigIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="monthly_usage",
                        to="authentication.workspace",
                    ),
                ),
            ],
            options={
                "ordering": ["-period"],
            },
        ),
        migrations.AddConstraint(
            model_name="monthlyusage",
            constraint=models.UniqueConstraint(
                fields=("workspace", "period"),
                name="unique_workspace_usage_period",
            ),
        ),
    ]
