# Generated by Django 4.1 on 2023-04-04 15:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cinema", "0003_movie_duration"),
    ]

    operations = [
        migrations.AlterField(
            model_name="genre",
            name="name",
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
