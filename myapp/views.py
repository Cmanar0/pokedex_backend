from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_http_methods
import json

@require_POST
def login_view(request):
    data = json.loads(request.body)
    username = data.get('username')
    password = data.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({'message': 'Logged in successfully.'})
    else:
        return JsonResponse({'error': 'Invalid credentials.'}, status=400)

@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({'message': 'Logged out successfully.'})

@ensure_csrf_cookie
@require_http_methods(["GET"])
def get_csrf_token(request):
    return JsonResponse({"message": "CSRF cookie set"})

@require_http_methods(["GET"])
def check_auth(request):
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
            }
        })
    else:
        return JsonResponse({'authenticated': False}, status=401)
