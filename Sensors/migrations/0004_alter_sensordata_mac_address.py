# Generated by Django 4.2.19 on 2025-03-01 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Sensors', '0003_sensordata_mac_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sensordata',
            name='mac_address',
            field=models.CharField(default='00:00:00:00:00:00', max_length=17, null=True),
        ),
    ]
