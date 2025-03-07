from django.urls import path
from .views import sensor_data_get, sensor_data_post, user_info_get, device_info_get,  device_latest_value, sensor_data_interval, sensor_data_last_seven, chart_view
urlpatterns = [
    path('get/data', sensor_data_get, name='sensor_data_get'),
    path('post/data', sensor_data_post, name='sensor_data_post'),
    path('get/user', user_info_get , name='user_info_get'),
    path('get/device', device_info_get , name='device_info_get'),
    path('get/data/latest', device_latest_value, name='device_info_get'),
    path('get/data/intervall', sensor_data_interval , name='sensor_data_interval'),
    path('get/data/latesthistory', sensor_data_last_seven, name='sensor_data_last_seven'),
    path('get/chart/quellechart', chart_view, name='chart_view'),

]