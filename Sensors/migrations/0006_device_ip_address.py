# Generated by Django 4.2.19 on 2025-03-03 12:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Sensors', '0005_user_remove_sensordata_mac_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='ip_address',
            field=models.CharField(default='', max_length=50),
        ),
    ]
