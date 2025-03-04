from django.contrib import admin
from .models import SensorData, Device, User # Import your model

# Register your models here.
admin.site.register(SensorData)
admin.site.register(Device)
admin.site.register(User)