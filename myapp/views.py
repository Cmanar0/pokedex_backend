from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.contrib.auth import authenticate, login, logout
from .my_api_serializers.user.user_read import UserReadSerializer, UserProfileReadSerializer
from .my_api_serializers.user.user_write import UserRegisterWriteSerializer, UserLoginWriteSerializer
from .api_integrations.pokemon.pokemon_api import fetch_pokemon_list, fetch_multiple_pokemon_details
from .models import UserProfile
from .decorators import handle_api_errors, require_authentication, validate_with_serializer, paginate_response
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
@handle_api_errors
@validate_with_serializer(UserLoginWriteSerializer)
def login_view(request):
    username = request.validated_data['username']
    password = request.validated_data['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return Response({
            'message': 'Logged in successfully.',
            'user': {
                **UserReadSerializer(user).data,
                'profile': UserProfileReadSerializer(user.profile).data
            }
        })
    return Response({'error': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
@handle_api_errors
@validate_with_serializer(UserRegisterWriteSerializer)
def register_view(request):
    user = request.validated_data.save()
    login(request, user)
    return Response({
        'message': 'User registered successfully.',
        'user': {
            **UserReadSerializer(user).data,
            'profile': UserProfileReadSerializer(user.profile).data
        }
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@handle_api_errors
def logout_view(request):
    logout(request)
    return Response({'message': 'Logged out successfully.'})

@api_view(['GET'])
@permission_classes([AllowAny])
@handle_api_errors
def get_csrf_token(request):
    return Response({"message": "CSRF cookie set"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@handle_api_errors
@require_authentication
def check_auth(request):
    return Response({'authenticated': True})

@api_view(['GET'])
@permission_classes([AllowAny])
@handle_api_errors
@paginate_response(limit=9)
def pokemon_list(request):
    search = request.GET.get('search', '').strip()
    skip_details = request.GET.get('skip_details', 'false').lower() == 'true'
    
    base_data = fetch_pokemon_list(
        request.pagination['offset'],
        request.pagination['limit']
    )
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

    return Response({
        'count': base_data.get('count', len(results)),
        'next': base_data.get('next'),
        'previous': base_data.get('previous'),
        'results': results,
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@handle_api_errors
@require_authentication
def user_profile_view(request):
    """
    Get the authenticated user's profile with nested user data.
    Each field is explicitly defined for better clarity and control.
    """
    user_data = UserReadSerializer(request.user).data
    profile_data = UserProfileReadSerializer(request.user.profile).data

    return Response({
        'user': {
            'id': user_data['id'],
            'username': user_data['username'],
            'email': user_data['email'],
            'first_name': user_data['first_name'],
            'last_name': user_data['last_name'],
            'profile': {
                'favorite_pokemon': profile_data['favorite_pokemon'],
                'created_at': profile_data['created_at'],
                'updated_at': profile_data['updated_at']
            }
        }
    })
