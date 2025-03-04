# Generated by Django 4.2.19 on 2025-03-03 09:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Sensors', '0004_alter_sensordata_mac_address'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=50)),
                ('password', models.CharField(max_length=50)),
                ('status', models.FloatField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='sensordata',
            name='mac_address',
        ),
        migrations.AlterField(
            model_name='sensordata',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('mac_address', models.CharField(default='00:00:00:00:00:00', max_length=50)),
                ('name', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=50)),
                ('is_active', models.FloatField(default=1)),
                ('owner_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Sensors.user')),
            ],
        ),
        migrations.AddField(
            model_name='sensordata',
            name='device_id',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='Sensors.device'),
        ),
    ]
