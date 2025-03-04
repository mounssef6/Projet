from django.urls import path
from .views import sensor_data_get, sensor_data_post, user_info_get, device_info_get, user_register,  device_latest_value, sensor_data_interval
urlpatterns = [
    path('get/data', sensor_data_get, name='sensor_data_get'),
    path('post/data', sensor_data_post, name='sensor_data_post'),
    path('post/user', user_register, name='user_register'),
    path('get/user', user_info_get , name='user_info_get'),
    path('get/device', device_info_get , name='device_info_get'),
    path('get/device/latest', device_latest_value, name='device_info_get'),
    path('get/device/intervall', sensor_data_interval , name='sensor_data_interval'),
]