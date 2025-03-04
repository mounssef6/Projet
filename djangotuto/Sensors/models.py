from django.db import models

class User(models.Model):
    id         = models.AutoField(primary_key=True)
    username   = models.CharField(max_length=50)
    password   = models.CharField(max_length=50)
    status     = models.FloatField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.created_at} - user: {self.username} | Status:{self.status}"

class Device(models.Model):
    id          = models.AutoField(primary_key=True)
    mac_address = models.CharField(max_length=50, default='00:00:00:00:00:00')
    ip_address  = models.CharField(max_length=50, default='')
    owner_id    = models.ForeignKey(User, on_delete=models.CASCADE)
    name        = models.CharField(max_length=50)
    description = models.CharField(max_length=50)
    is_active   = models.FloatField(default=1)
    def __str__(self):
        return f"{self.mac_address} - name: {self.name} | status:{self.is_active}"

class SensorData(models.Model):
    id          = models.AutoField(primary_key=True)
    timestamp   = models.DateTimeField(auto_now_add=True)
    temperature = models.FloatField()
    humidity    = models.FloatField()
    pressure    = models.FloatField(default=0.0)
    device_id   = models.ForeignKey(Device, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return f"{self.timestamp}: Temp={self.temperature}°C, Humidity={self.humidity}%, Pressure={self.pressure} hPa"