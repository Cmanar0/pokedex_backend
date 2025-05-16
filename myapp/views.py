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
from .api_integrations.pokemon.pokemon_api import (
    fetch_pokemon_list,
    fetch_multiple_pokemon_details,
    fetch_pokemon_by_type,
    fetch_pokemon_by_ability,
    fetch_pokemon_detail,
    POKEMON_URL
)
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
    serializer = UserRegisterWriteSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.create(serializer.validated_data)
        login(request, user)
        return Response({
            'message': 'User registered successfully.',
            'user': {
                **UserReadSerializer(user).data,
                'profile': UserProfileReadSerializer(user.profile).data
            }
        }, status=status.HTTP_201_CREATED)
    logger.error(f"Registration validation errors: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
def pokemon_list(request):
    # Parse query parameters
    page = int(request.GET.get('page', 1))
    search = request.GET.get('search', '').strip().lower()
    pokemon_type = request.GET.get('type', '').strip().lower()
    ability = request.GET.get('ability', '').strip().lower()
    limit = 9
    offset = (page - 1) * limit

    # Start with full base list
    base_data = fetch_pokemon_list(offset=0, limit=1000)
    if not base_data:
        return Response({'error': 'Failed to fetch Pokémon list.'}, status=status.HTTP_502_BAD_GATEWAY)

    pokemon_list = base_data['results']

    # Apply search filter
    if search:
        pokemon_list = [p for p in pokemon_list if search in p['name'].lower()]

    # Apply type filter
    if pokemon_type:
        type_filtered = fetch_pokemon_by_type(pokemon_type)
        if type_filtered is None:
            return Response({'error': 'Failed to fetch Pokémon by type.'}, status=status.HTTP_502_BAD_GATEWAY)
        pokemon_list = [p for p in pokemon_list if p['name'] in type_filtered]

    # Apply ability filter
    if ability:
        ability_filtered = fetch_pokemon_by_ability(ability)
        if ability_filtered is None:
            return Response({'error': 'Failed to fetch Pokémon by ability.'}, status=status.HTTP_502_BAD_GATEWAY)
        pokemon_list = [p for p in pokemon_list if p['name'] in ability_filtered]

    # Calculate total count before pagination
    total_count = len(pokemon_list)

    # Apply pagination
    paginated_list = pokemon_list[offset:offset + limit]

    # Fetch details for paginated results
    urls = [p['url'] for p in paginated_list]
    details = fetch_multiple_pokemon_details(urls)
    
    # Combine the data
    results = [
        {
            'name': paginated_list[i]['name'],
            **details[i]
        } for i in range(len(paginated_list))
    ]

    # Build next/previous URLs
    next_url = None
    if offset + limit < total_count:
        next_url = f"?page={page + 1}&limit={limit}"
        if search: next_url += f"&search={search}"
        if pokemon_type: next_url += f"&type={pokemon_type}"
        if ability: next_url += f"&ability={ability}"
    
    previous_url = None
    if page > 1:
        previous_url = f"?page={page - 1}&limit={limit}"
        if search: previous_url += f"&search={search}"
        if pokemon_type: previous_url += f"&type={pokemon_type}"
        if ability: previous_url += f"&ability={ability}"

    return Response({
        'count': total_count,
        'next': next_url,
        'previous': previous_url,
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

@api_view(['GET'])
@permission_classes([AllowAny])
@handle_api_errors
def pokemon_detail(request, name):
    """Fetch detailed information for a specific Pokémon."""
    url = f"{POKEMON_URL}/{name.lower()}"
    result = fetch_pokemon_detail(url)
    
    if not result or not result.get('sprite'):
        return Response(
            {'error': f'Pokémon {name} not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    result['name'] = name
    return Response(result)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@handle_api_errors
@require_authentication
def update_favorite_pokemon(request):
    """Add or remove a Pokémon from the user's favorites."""
    pokemon_name = request.data.get('pokemon_name')
    if not pokemon_name:
        return Response(
            {'error': 'Pokemon name is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    profile = request.user.profile
    if pokemon_name in profile.favorite_pokemon:
        profile.favorite_pokemon.remove(pokemon_name)
        action = 'removed from'
    else:
        profile.favorite_pokemon.append(pokemon_name)
        action = 'added to'
    
    profile.save()

    return Response({
        'message': f'Pokemon {pokemon_name} {action} favorites.',
        'favorite_pokemon': profile.favorite_pokemon
    })
