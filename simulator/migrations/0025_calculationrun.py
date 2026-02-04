from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("simulator", "0024_wsdata_ladezustand_abs"),
    ]

    operations = [
        migrations.CreateModel(
            name="CalculationRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("duration_ms", models.PositiveIntegerField()),
                ("summary", models.JSONField(blank=True, default=dict)),
                ("triggered_by", models.CharField(blank=True, max_length=150, null=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
