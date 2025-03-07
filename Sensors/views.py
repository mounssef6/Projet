import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from .models import SensorData, User, Device
from django.utils import timezone
from django.shortcuts import render
from datetime import timedelta
from datetime import datetime
from django.shortcuts import get_object_or_404
from collections import defaultdict




# ===============================
# Sensor Data Endpoints
# ===============================

@csrf_exempt
def sensor_data_post(request):
    """
    POST endpoint: Receives sensor data in JSON format and creates a SensorData record.
    If the device (by mac_address) does not exist, it is created only the first time.
    """
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body.
            data = json.loads(request.body.decode('utf-8'))
            temperature = data.get('temperature')
            humidity = data.get('humidity')
            pressure = data.get('pressure')
            mac_address = data.get('mac_address')
            
            # Validate that all required values are provided.
            if temperature is None or humidity is None or pressure is None:
                return JsonResponse({
                    'success': False,
                    'message': 'Missing temperature, humidity, or pressure data'
                }, status=200)
            
            # Look up the device by its MAC address. If not found, create it.
            try:
                device = Device.objects.get(mac_address=mac_address)
            except Device.DoesNotExist:
                # Create a new device record with the provided mac_address.
                default_user = User.objects.first()  # Assumes a default user exists.
                if not default_user:
                    return JsonResponse({
                        'success': False,
                        'message': 'No default user found to assign the new device.'
                    }, status=200)
                device = Device.objects.create(
                    mac_address=mac_address,
                    owner_id=default_user,
                    name=f"Device {mac_address}",
                    description="Auto-created device",
                    is_active=1
                )
            
            # Create a new sensor reading entry.
            reading = SensorData.objects.create(
                temperature=temperature,
                humidity=humidity,
                pressure=pressure,
                device_id=device
            )
            
            # Return a JSON response with the stored data.
            return JsonResponse({
                'success': True,
                'data': {
                    'timestamp': reading.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'temperature': reading.temperature,
                    'humidity': reading.humidity,
                    'pressure': reading.pressure,
                    'device': {
                        'mac_address': device.mac_address,
                        'name': device.name,
                    }
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=200)
    else:
        return JsonResponse({
            'success': False,
            'message': 'Only POST requests are allowed'
        }, status=200)

# Make sure you have a function that buckets a timestamp into a 10-minute interval.
def bucket_timestamp(ts):
    # Example implementation: Round down to the nearest 10 minutes.
    minute = (ts.minute // 10) * 10
    return ts.replace(minute=minute, second=0, microsecond=0)

def sensor_data_get(request):
    """
    GET endpoint: Retrieves sensor readings from the past 2 hours, buckets them
    into 10-minute intervals, and returns a JSON response with the following structure:

    {
      "success": true,
      "data": {
         <device_id>: {
           "temperature": {
             "2025-03-06 03:00": 34.5,
             ...
           },
           "humidity": {
             "2025-03-06 03:00": 1139.5,
             ...
           },
           "pressure": {
             "2025-03-06 03:00": 406,
             ...
           }
         },
         <other_device_id>: { ... }
      }
    }
    """
    if request.method == 'GET':
        now = timezone.now()
        start_time = now - timedelta(hours=2)

        # Optionally filter by device using GET parameter (e.g., ?mac_address=xx:xx:xx)
        mac_address = request.GET.get('mac_address')
        sensor_readings = SensorData.objects.filter(timestamp__gte=start_time, timestamp__lte=now)
        if mac_address:
            sensor_readings = sensor_readings.filter(device_id__mac_address=mac_address)

        # Group sensor readings by device id and then by bucket timestamp.
        device_data = defaultdict(lambda: defaultdict(lambda: {
            'temperature': [],
            'humidity': [],
            'pressure': []
        }))

        for reading in sensor_readings:
            device_key = reading.device_id.id  # Using device id as the key.
            bucket_dt = bucket_timestamp(reading.timestamp)
            bucket_key = bucket_dt.strftime('%Y-%m-%d %H:%M')
            device_data[device_key][bucket_key]['temperature'].append(reading.temperature)
            device_data[device_key][bucket_key]['humidity'].append(reading.humidity)
            device_data[device_key][bucket_key]['pressure'].append(reading.pressure)

        # Compute the average for each bucket for each device.
        data = {}
        for device_key, buckets in device_data.items():
            temperature_data = {}
            humidity_data = {}
            pressure_data = {}
            for bucket_key, measurements in buckets.items():
                if measurements['temperature']:
                    temperature_data[bucket_key] = sum(measurements['temperature']) / len(measurements['temperature'])
                if measurements['humidity']:
                    humidity_data[bucket_key] = sum(measurements['humidity']) / len(measurements['humidity'])
                if measurements['pressure']:
                    pressure_data[bucket_key] = sum(measurements['pressure']) / len(measurements['pressure'])
            data[device_key] = {
                "temperature": temperature_data,
                "humidity": humidity_data,
                "pressure": pressure_data,
            }

        return JsonResponse({
            "success": True,
            "data": data
        })
    else:
        return JsonResponse({
            "success": False,
            "message": "Only GET requests are allowed"
        }, status=405)


# ===============================
# User Endpoints
# ===============================

def user_info_get(request):
    """
    GET endpoint: Retrieves and returns all user records in JSON format.
    """
    if request.method == 'GET':
        users = User.objects.all()
        user_info = [
            {
                'id': user.id,
                'username': user.username,
                'status': user.status,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for user in users
        ]
        return JsonResponse({
            'success': True,
            'user_info': user_info
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Only GET requests are allowed'
        }, status=200)

# ===============================
# Device Info Endpoint
# ===============================

def device_info_get(request):
    """
    GET endpoint: Retrieves and returns device records in JSON format.
    If an 'id' query parameter is provided, only the device with that id is returned.
    """
    if request.method == 'GET':
        device_id = request.GET.get('id')  # Get the 'id' parameter from the URL
        if device_id:
            # Fetch the specific device. If not found, return a 404 error.
            device = get_object_or_404(Device, id=device_id)
            device_info = {
                'id': device.id,
                'mac_address': device.mac_address,
                'owner': device.owner_id.username,
                'name': device.name,
                'description': device.description,
                'is_active': device.is_active,
            }
        else:
            # If no id is provided, retrieve all devices.
            devices = Device.objects.all()
            device_info = [
                {
                    'id': device.id,
                    'mac_address': device.mac_address,
                    'owner': device.owner_id.username,
                    'name': device.name,
                    'description': device.description,
                    'is_active': device.is_active,
                }
                for device in devices
            ]
        # Return the results with the key "data"
        return JsonResponse({
            'success': True,
            'data': device_info
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Only GET requests are allowed'
        }, status=200)


def device_latest_value(request):
    """
    GET endpoint: Retrieves for each device the two most recent sensor readings.
    If a query parameter 'id' is provided (e.g., ?id=3), only that device's readings
    are returned. The JSON response includes:
      - esp_id: The device's id.
      - esp_name: The device's name.
      - ip_address: The device's IP address (if available; otherwise "N/A").
      - status: The device's active status.
      - current_value: The most recent sensor reading (timestamp, temperature, humidity, pressure).
      - previous_value: The second most recent sensor reading (if available).
    """
    if request.method == 'GET':
        # Check if an 'id' parameter was passed; if so, filter by that device id.
        device_id = request.GET.get('id')
        if device_id:
            devices = Device.objects.filter(id=device_id)
        else:
            devices = Device.objects.all()

        result = []
        for device in devices:
            # Fetch the two most recent sensor readings for this device.
            readings = SensorData.objects.filter(device_id=device).order_by('-timestamp')[:2]

            current_value = {}
            previous_value = {}
            if readings:
                current = readings[0]
                current_value = {
                    "timestamp": current.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    "temperature": current.temperature,
                    "humidity": current.humidity,
                    "pressure": current.pressure,
                }
                if len(readings) > 1:
                    previous = readings[1]
                    previous_value = {
                        "timestamp": previous.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        "temperature": previous.temperature,
                        "humidity": previous.humidity,
                        "pressure": previous.pressure,
                    }

            # Get the IP address if it exists, otherwise return "N/A"
            ip_address = getattr(device, 'ip_address', "N/A")

            result.append({
                "esp_id": device.id,          # <-- Added device id
                "esp_name": device.name,
                "ip_address": ip_address,
                "status": device.is_active,
                "current_value": current_value,
                "previous_value": previous_value
            })

        return JsonResponse({
            "success": True,
            "data": result
        })
    else:
        return JsonResponse({
            "success": False,
            "message": "Only GET requests are allowed"
        }, status=200)



def sensor_data_interval(request):
    """
    GET endpoint: Retrieves sensor data readings within a specified time interval.
    By default, if no query parameters are provided, it returns readings for the last 24 hours.
    Optional query parameters:
      - start: The start time in 'YYYY-MM-DD HH:MM:SS' format.
      - end: The end time in 'YYYY-MM-DD HH:MM:SS' format.
    
    Returns a JSON response containing sensor readings ordered by timestamp,
    along with the time interval used.
    """
    if request.method == 'GET':
        # Retrieve query parameters
        start_time_str = request.GET.get('start')
        end_time_str = request.GET.get('end')
        
        # Use provided parameters if available; otherwise default to the last 24 hours.
        if start_time_str and end_time_str:
            try:
                start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid date format. Use YYYY-MM-DD HH:MM:SS'
                }, status=200)
        else:
            # Default to last 24 hours if no parameters are provided.
            end_time = timezone.now()
            start_time = end_time - timedelta(hours=24)
        
        # Retrieve sensor readings within the specified time interval.
        sensor_readings = SensorData.objects.filter(timestamp__gte=start_time, timestamp__lte=end_time).order_by('timestamp')
        
        data = [
            {
                'id': reading.id,
                'timestamp': reading.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'temperature': reading.temperature,
                'humidity': reading.humidity,
                'pressure': reading.pressure,
                'device': {
                    'mac_address': reading.device_id.mac_address,
                    'name': reading.device_id.name,
                }
            }
            for reading in sensor_readings
        ]
        
        return JsonResponse({
            'success': True,
             'time_interval': {
                'start': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            },
            'data': data,
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Only GET requests are allowed'
        }, status=200)

def sensor_data_last_seven(request):
    """
    GET endpoint: Returns the last seven sensor data records for a device whose
    id is provided via the query parameter 'id' (e.g. ?id=2).
    The returned JSON includes temperature, humidity, pressure, and timestamp.
    All numeric values are rounded to two decimal places.
    """
    if request.method == 'GET':
        device_id = request.GET.get('id')  # Retrieve the id from the query parameters
        if not device_id:
            return JsonResponse({
                'success': False,
                'message': 'Please provide a device id using the query parameter "id"'
            }, status=400)
        
        # Ensure the device exists (or return a 404 if it doesn’t)
        device = get_object_or_404(Device, id=device_id)
        
        # Filter sensor data for the device and order by descending timestamp
        sensor_records = SensorData.objects.filter(device_id=device).order_by('-timestamp')[:7]
        
        # Convert the QuerySet to a list of dictionaries with the required fields
        data = list(sensor_records.values('temperature', 'humidity', 'pressure', 'timestamp'))
        
        # Round numeric values to two decimal places
        for record in data:
            record['temperature'] = round(record['temperature'], 2)
            record['humidity'] = round(record['humidity'], 2)
            record['pressure'] = round(record['pressure'], 2)
        
        return JsonResponse({
            'success': True,
            'data': data
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Only GET requests are allowed'
        }, status=405)

# Assuming you have imported your SensorData model from your app's models.
# from yourapp.models import SensorData

def bucket_timestamp(ts):
    """
    Floors a datetime object to the nearest 10 minutes.
    For example, 09:34 becomes 09:30.
    """
    floored_minute = (ts.minute // 10) * 10
    return ts.replace(minute=floored_minute, second=0, microsecond=0)

def chart_view(request):
    """
    GET endpoint that returns sensor readings in 10-minute buckets over the past 24 hours.
    
    Optional query parameters:
      - id: Device ID to filter sensor readings (e.g., ?id=2)
      - data: Measurement type to return (e.g., ?data=temp, ?data=humidity, ?data=pressure)
    
    The JSON response is structured as follows:
    
    {
      "success": true,
      "data": {
        "Device 4C:11:AE:11:19:0C": {
          "temperature": {
            "2025-03-06 09:30": 24,
            ...
          },
          "humidity": { ... },
          "pressure": { ... }
        }
      }
    }
    
    If the data parameter is provided, only that measurement type is included.
    By default, the time range is the last 24 hours and every value related to that device is returned.
    """
    if request.method != 'GET':
        return JsonResponse({
            "success": False,
            "message": "Only GET requests are allowed."
        }, status=405)
    
    now = timezone.now()
    # Change the default time range to the last 24 hours.
    start_time = now - timedelta(hours=24)
    
    # Retrieve sensor readings from the past 24 hours.
    sensor_readings = SensorData.objects.filter(timestamp__gte=start_time, timestamp__lte=now)
    
    # Filter by device id if provided (using device's primary key).
    device_id = request.GET.get('id')
    if device_id:
        sensor_readings = sensor_readings.filter(device_id__id=device_id)
    
    # If no readings found, return an error.
    if not sensor_readings.exists():
        return JsonResponse({
            "success": False,
            "message": "No sensor readings found for the given filter."
        }, status=404)
    
    # Determine the device name from the first reading.
    device_name = sensor_readings.first().device_id.name
    
    # Bucket readings into 10-minute intervals.
    buckets = {}
    for reading in sensor_readings:
        bucket_dt = bucket_timestamp(reading.timestamp)
        bucket_key = bucket_dt.strftime('%Y-%m-%d %H:%M')
        if bucket_key not in buckets:
            buckets[bucket_key] = {
                'temperature': [],
                'humidity': [],
                'pressure': []
            }
        buckets[bucket_key]['temperature'].append(reading.temperature)
        buckets[bucket_key]['humidity'].append(reading.humidity)
        buckets[bucket_key]['pressure'].append(reading.pressure)
    
    # Calculate average values for each bucket.
    aggregated = {
        "temperature": {},
        "humidity": {},
        "pressure": {}
    }
    for bucket_key, values in buckets.items():
        if values['temperature']:
            aggregated["temperature"][bucket_key] = sum(values['temperature']) / len(values['temperature'])
        if values['humidity']:
            aggregated["humidity"][bucket_key] = sum(values['humidity']) / len(values['humidity'])
        if values['pressure']:
            aggregated["pressure"][bucket_key] = sum(values['pressure']) / len(values['pressure'])
    
    # Optionally filter which measurement type is returned.
    measurement_filter = request.GET.get('data')
    if measurement_filter:
        measurement_filter = measurement_filter.lower()
        mapping = {
            'temp': 'temperature',
            'temperature': 'temperature',
            'hum': 'humidity',
            'humidity': 'humidity',
            'press': 'pressure',
            'pressure': 'pressure'
        }
        if measurement_filter in mapping:
            key = mapping[measurement_filter]
            aggregated = { key: aggregated.get(key, {}) }
        else:
            return JsonResponse({
                "success": False,
                "message": "Invalid measurement type provided. Use temp, humidity, or pressure."
            }, status=400)
    
    # Build final response data using the device name as the key.
    data = {
        device_name: aggregated
    }
    
    return JsonResponse({
        "success": True,
        "data": data
    })
