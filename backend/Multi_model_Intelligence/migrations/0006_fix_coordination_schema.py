# ruff: noqa
# Make 0006 a no-op if already repaired manually; keep state aligned.
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def fix_tables(apps, schema_editor):
    """Idempotent repair — safe if tables already correct."""
    conn = schema_editor.connection
    with conn.cursor() as cursor:
        if conn.vendor != 'sqlite':
            return
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cursor.fetchall()}

        if 'multimodal_cross_insights' in tables:
            cursor.execute('PRAGMA table_info(multimodal_cross_insights)')
            cols = {r[1] for r in cursor.fetchall()}
            if 'mode' in cols and 'insight_type' not in cols:
                cursor.execute('DROP TABLE multimodal_cross_insights')
                tables.discard('multimodal_cross_insights')

        if (
            'Multi_model_Intelligence_crossmodalinsight' in tables
            and 'multimodal_cross_insights' not in tables
        ):
            cursor.execute(
                'ALTER TABLE "Multi_model_Intelligence_crossmodalinsight" '
                'RENAME TO multimodal_cross_insights'
            )

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='multimodel_coordination_runs'"
        )
        if cursor.fetchone() is None:
            ModelCoordinationRun = apps.get_model('Multi_model_Intelligence', 'ModelCoordinationRun')
            # ``apps`` is the pre-state for SeparateDatabaseAndState, where
            # migration 0005 accidentally assigned this model the cross-modal
            # table name. Create it under its corrected table name instead.
            original_table = ModelCoordinationRun._meta.db_table
            ModelCoordinationRun._meta.db_table = 'multimodel_coordination_runs'
            try:
                schema_editor.create_model(ModelCoordinationRun)
            finally:
                ModelCoordinationRun._meta.db_table = original_table


class Migration(migrations.Migration):

    dependencies = [
        ('Multi_model_Intelligence', '0005_model_coordination_run'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name='ModelCoordinationRun'),
                migrations.CreateModel(
                    name='ModelCoordinationRun',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('mode', models.CharField(choices=[('route', 'Smart Route'), ('collaborative', 'Collaborative'), ('debate', 'Debate / Consensus'), ('pipeline', 'Sequential Pipeline')], max_length=20)),
                        ('prompt', models.TextField()),
                        ('model_ids', models.JSONField(default=list)),
                        ('options', models.JSONField(blank=True, default=dict)),
                        ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                        ('result', models.JSONField(blank=True, default=dict)),
                        ('final_answer', models.TextField(blank=True)),
                        ('duration_ms', models.IntegerField(blank=True, null=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='model_coordination_runs', to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'multimodel_coordination_runs',
                        'ordering': ['-created_at'],
                    },
                ),
                migrations.AlterModelTable(
                    name='crossmodalinsight',
                    table='multimodal_cross_insights',
                ),
            ],
            database_operations=[
                migrations.RunPython(fix_tables, migrations.RunPython.noop),
            ],
        ),
    ]
