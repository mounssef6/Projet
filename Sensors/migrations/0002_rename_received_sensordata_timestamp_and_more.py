# Generated by Django 4.2.19 on 2025-03-01 13:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Sensors', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sensordata',
            old_name='received',
            new_name='timestamp',
        ),
        migrations.AddField(
            model_name='sensordata',
            name='pressure',
            field=models.FloatField(default=0.0),
        ),
    ]
