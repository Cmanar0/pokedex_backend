from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from .serializers import PokemonListResponseSerializer, UserSerializer, LoginSerializer, RegisterSerializer
from .pokemon_api import fetch_pokemon_list, fetch_multiple_pokemon_details
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    try:
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return Response({
                    'message': 'Logged in successfully.',
                    'user': UserSerializer(user).data
                })
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Log the user in after successful registration
        login(request, user)
        return Response({
            'message': 'User registered successfully.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({'message': 'Logged out successfully.'})

@api_view(['GET'])
@permission_classes([AllowAny])
def get_csrf_token(request):
    return Response({"message": "CSRF cookie set"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_auth(request):
    return Response({
        'authenticated': True,
        'user': UserSerializer(request.user).data
    })

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
