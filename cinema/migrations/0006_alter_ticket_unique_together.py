# Generated by Django 4.1 on 2024-04-17 23:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cinema', '0005_alter_ticket_unique_together'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='ticket',
            unique_together={('movie_session', 'row', 'seat')},
        ),
    ]
