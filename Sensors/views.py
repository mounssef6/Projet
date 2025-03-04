import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from .models import SensorData, User, Device
from django.utils import timezone
from django.shortcuts import render

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


def sensor_data_get(request):
    """
    GET endpoint: Retrieves and returns all sensor readings in JSON format.
    """
    if request.method == 'GET':
        sensor_readings = SensorData.objects.all().order_by('-timestamp')
        sensor_data = [
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
            'data': sensor_data
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Only GET requests are allowed'
        }, status=200)


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


@csrf_exempt
def user_register(request):
    """
    POST endpoint: Creates a new user with a hashed password.
    Expects JSON data with 'username' and 'password'.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            username = data.get('username')
            password = data.get('password')
            if not username or not password:
                return JsonResponse({
                    'success': False,
                    'message': 'Username and password are required'
                }, status=200)
            
            # Hash the password using Django's make_password.
            hashed_password = make_password(password)
            
            # Create a new user record.
            user = User.objects.create(
                username=username,
                password=hashed_password,
                status=True  # Or adjust according to your logic.
            )
            
            return JsonResponse({
                'success': True,
                'message': 'User created successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                }
            }, status=201)
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


# ===============================
# Device Info Endpoint
# ===============================

def device_info_get(request):
    """
    GET endpoint: Retrieves and returns all device records in JSON format.
    """
    if request.method == 'GET':
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
        return JsonResponse({
            'success': True,
            'device': device_info
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Only GET requests are allowed'
        }, status=200)

def device_latest_value(request):
    """
    GET endpoint: Retrieves for each device the two most recent sensor readings.
    Returns a JSON object that contains:
      - esp_name: The device's name.
      - ip_address: The device's IP address (if available; otherwise "N/A").
      - status: The device's active status.
      - current_value: A dict containing the most recent sensor reading details (timestamp, temperature, humidity, pressure).
      - previous_value: A dict containing the second most recent sensor reading details (if available).
    """
    if request.method == 'GET':
        devices = Device.objects.all()
        result = []
        for device in devices:
            # Fetch the two most recent sensor readings.
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
            # Assume the Device model may have an ip_address field.
            ip_address = getattr(device, 'ip_address', "N/A")
            
            result.append({
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

from datetime import datetime, timedelta
from django.utils import timezone
from django.http import JsonResponse

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

def index(request):
    # Fetch data from the database
    readings = SensorData.objects.all().order_by('-timestamp')
    context = {
        'current_time': timezone.now(),
        'readings': readings
    }
    return render(request, 'Sensors/index.html', context)
