from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("simulator", "0026_landuse_target_locked"),
    ]

    operations = [
        migrations.CreateModel(
            name="Formula",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=50, unique=True)),
                ("expression", models.TextField()),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["key"],
            },
        ),
        migrations.CreateModel(
            name="FormulaVariable",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("variable_name", models.CharField(max_length=50)),
                (
                    "source_type",
                    models.CharField(
                        choices=[
                            ("landuse_status", "LandUse status_ha"),
                            ("landuse_target", "LandUse target_ha"),
                            ("renewable_status", "RenewableData status_value"),
                            ("renewable_target", "RenewableData target_value"),
                            ("verbrauch_status", "VerbrauchData status"),
                            ("verbrauch_ziel", "VerbrauchData ziel"),
                            ("literal", "Literal number"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "source_key",
                    models.CharField(
                        help_text="Code or value used to resolve the data (e.g., LU_2.1, 1.4, or literal).",
                        max_length=100,
                    ),
                ),
                (
                    "default_value",
                    models.FloatField(blank=True, help_text="Fallback if the source cannot be resolved.", null=True),
                ),
                (
                    "formula",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="variables",
                        to="simulator.formula",
                    ),
                ),
            ],
            options={
                "ordering": ["formula__key", "variable_name"],
                "unique_together": {("formula", "variable_name")},
            },
        ),
        migrations.AddField(
            model_name="landuse",
            name="status_formula_key",
            field=models.CharField(
                blank=True, help_text="Formula key to calculate status_ha", max_length=50, null=True
            ),
        ),
        migrations.AddField(
            model_name="landuse",
            name="target_formula_key",
            field=models.CharField(
                blank=True, help_text="Formula key to calculate target_ha", max_length=50, null=True
            ),
        ),
    ]
