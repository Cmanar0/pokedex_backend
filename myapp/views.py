from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth import authenticate, login, logout
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .serializers import PokemonListResponseSerializer
from .pokemon_api import fetch_pokemon_list, fetch_multiple_pokemon_details
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

@api_view(['GET'])
@permission_classes([AllowAny])
def pokemon_list(request):
    page = max(1, int(request.GET.get('page', 1))) if request.GET.get('page', '').isdigit() else 1
    search = request.GET.get('search', '').strip()
    skip_details = request.GET.get('skip_details', 'false').lower() == 'true'
    limit = 9
    offset = (page - 1) * limit

    base_data = fetch_pokemon_list(offset, limit)
    if not base_data:
        return Response({'error': 'Failed to fetch Pokémon list.'}, status=status.HTTP_502_BAD_GATEWAY)

    raw_list = base_data.get('results', [])

    # Apply search filter
    if search:
        raw_list = [p for p in raw_list if search.lower() in p['name'].lower()]

    if skip_details:
        results = [
            {
                'name': p['name'],
                'sprite': None,
                'types': [],
                'abilities': [],
                'height': None,
                'weight': None,
            } for p in raw_list
        ]
    else:
        urls = [p['url'] for p in raw_list]
        details = fetch_multiple_pokemon_details(urls)
        results = [
            {
                'name': raw_list[i]['name'],
                **details[i]
            } for i in range(len(raw_list))
        ]

    response_data = {
        'count': base_data.get('count', len(results)),
        'next': base_data.get('next'),
        'previous': base_data.get('previous'),
        'results': results,
    }

    serializer = PokemonListResponseSerializer(response_data)
    return Response(serializer.data, status=status.HTTP_200_OK)
