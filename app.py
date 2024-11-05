import os
import json
import bson
from django.conf import settings
from django.urls import path
from django.core.wsgi import get_wsgi_application
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import unquote

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

settings.configure(
    DEBUG=True,
    ROOT_URLCONF=__name__,
    SECRET_KEY='your_secret_key'
)

JSON_FILE_PATH = 'users.json'

def read_json_file():
    with open(JSON_FILE_PATH, 'r') as f:
        return json.load(f)

def write_json_file(data):
    with open(JSON_FILE_PATH, 'w') as f:
        json.dump(data, f, indent=4)

@csrf_exempt
def get_users(request):
    if request.method == 'GET':
        data = read_json_file()
        return JsonResponse({'users': data}, status=200)

    return JsonResponse({'message': 'Method not allowed'}, status=405)

@csrf_exempt
def search_users(request):
    if request.method == 'GET':
        data = read_json_file()
        search_params = request.GET.dict() 

        filtered_users = [
            user for user in data
            if all(
                str(user.get(key, '')).lower() == unquote(value).lower()
                for key, value in search_params.items()
            )
        ]

        return JsonResponse({'users': filtered_users}, status=200)

    return JsonResponse({'message': 'Method not allowed'}, status=405)

@csrf_exempt
def get_user(request, username):
    if request.method == 'GET':
        data = read_json_file()
        user = next((user for user in data if user['username'] == username), None)
        
        if user:
            return JsonResponse(user, status=200)
        else:
            return JsonResponse({'message': 'User not found'}, status=404)

    return JsonResponse({'message': 'Method not allowed'}, status=405)

@csrf_exempt
def create_user(request):
    print("Received request method:", request.method) 
    if request.method == 'POST':
        data = read_json_file()
        new_user = json.loads(request.body)

        required_fields = ['username', 'password', 'admin', 'name', 'date_of_birth', 'email', 'roles', 'courses']

        for field in required_fields:
            if field not in new_user:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)

        if not isinstance(new_user['admin'], bool):
            return JsonResponse({'error': 'Field "admin" must be a boolean.'}, status=400)

        if not isinstance(new_user['roles'], list) or not all(isinstance(role, str) for role in new_user['roles']):
            return JsonResponse({'error': 'Field "roles" must be a list of strings.'}, status=400)

        if not isinstance(new_user['courses'], list) or not all(isinstance(course, str) for course in new_user['courses']):
            return JsonResponse({'error': 'Field "courses" must be a list of strings.'}, status=400)

        if any(user['username'] == new_user['username'] for user in data):
            return JsonResponse({'error': 'Username already exists.'}, status=400)

        new_user['_id'] = {"$oid": str(bson.ObjectId())}

        formatted_user = {
            "_id": new_user['_id'],
            "username": new_user['username'],
            "password": new_user['password'],
            "admin": new_user['admin'],
            "name": new_user['name'],
            "date_of_birth": new_user['date_of_birth'],
            "email": new_user['email'],
            "roles": new_user['roles'],
            "courses": new_user['courses']
        }

        data.append(formatted_user)
        write_json_file(data)
        return JsonResponse(formatted_user, status=201)

    return JsonResponse({'message': 'Method not allowed'}, status=405)

@csrf_exempt
def update_user(request, username):
    if request.method == 'PUT':
        data = read_json_file()
        user = next((user for user in data if user['username'] == username), None)

        if user:
            updated_data = json.loads(request.body)

            required_fields = ['username', 'password', 'admin', 'name', 'date_of_birth', 'email', 'roles', 'courses']

            for field in required_fields:
                if field not in updated_data:
                    return JsonResponse({'error': f'Missing required field: {field}'}, status=400)

            if not isinstance(updated_data['admin'], bool):
                return JsonResponse({'error': 'Field "admin" must be a boolean.'}, status=400)

            if not isinstance(updated_data['roles'], list) or not all(isinstance(role, str) for role in updated_data['roles']):
                return JsonResponse({'error': 'Field "roles" must be a list of strings.'}, status=400)

            if not isinstance(updated_data['courses'], list) or not all(isinstance(course, str) for course in updated_data['courses']):
                return JsonResponse({'error': 'Field "courses" must be a list of strings.'}, status=400)

            if updated_data['username'] != username and any(u['username'] == updated_data['username'] for u in data):
                return JsonResponse({'error': 'Username already exists.'}, status=400)

            user.update({
                "username": updated_data['username'],
                "password": updated_data['password'],
                "admin": updated_data['admin'],
                "name": updated_data['name'],
                "date_of_birth": updated_data['date_of_birth'],
                "email": updated_data['email'],
                "roles": updated_data['roles'],
                "courses": updated_data['courses']
            })

            write_json_file(data)
            return JsonResponse(user, status=200)
        else:
            return JsonResponse({'message': 'User not found'}, status=404)

    return JsonResponse({'message': 'Method not allowed'}, status=405)

@csrf_exempt
def delete_user(request, username):
    if request.method == 'DELETE':
        data = read_json_file()
        user = next((user for user in data if user['username'] == username), None)

        if user:
            data.remove(user)
            write_json_file(data)
            return JsonResponse({'message': 'User deleted successfully'}, status=200) 
        else:
            return JsonResponse({'error': 'User not found'}, status=404)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

# Define URLs
urlpatterns = [
    path('api/v1.0/users/', get_users),  # GET all users
    path('api/v1.0/users/search/', search_users),  # Search users based on query params
    path('api/v1.0/users/new/', create_user),  # POST to create a new user
    path('api/v1.0/users/<str:username>/', get_user),  # GET single user by username
    path('api/v1.0/users/<str:username>/edit/', update_user),  # PUT to update a user
    path('api/v1.0/users/<str:username>/remove/', delete_user),  # DELETE a user
]

application = get_wsgi_application()

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'runserver'])
