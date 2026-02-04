from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("simulator", "0025_calculationrun"),
    ]

    operations = [
        migrations.AddField(
            model_name="landuse",
            name="target_locked",
            field=models.BooleanField(default=False, help_text="Preserve manual target_ha edits from parent cascades"),
        ),
    ]
