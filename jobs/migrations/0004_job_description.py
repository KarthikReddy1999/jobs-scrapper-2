from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0003_scraperstate_worker_pid"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
    ]
