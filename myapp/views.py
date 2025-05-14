from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_http_methods
from rest_framework.decorators import api_view
import json
import requests
import concurrent.futures
from django.core.cache import cache
import hashlib

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

def fetch_pokemon_sprite(pokemon_url):
    """Fetch sprite for a single Pokemon"""
    try:
        response = requests.get(pokemon_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('sprites', {}).get('front_default')
    except:
        pass
    return None

def fetch_pokemon_sprite_cached(pokemon_url):
    """Fetch sprite with caching"""
    cache_key = f"sprite_{hashlib.md5(pokemon_url.encode()).hexdigest()}"
    cached_sprite = cache.get(cache_key)
    
    if cached_sprite is not None:
        return cached_sprite
    
    sprite = fetch_pokemon_sprite(pokemon_url)
    # Cache for 1 hour
    cache.set(cache_key, sprite, 3600)
    return sprite

@api_view(['GET'])
def get_pokemon_list(request):
    skip_sprites = request.GET.get('skip_sprites', 'false').lower() == 'true'
    page = int(request.GET.get('page', 1))
    search = request.GET.get('search', '').lower()
    pokemon_type = request.GET.get('type')
    ability = request.GET.get('ability')
    limit = 10
    offset = (page - 1) * limit
    
    # Handle type filtering
    if pokemon_type:
        type_url = f'https://pokeapi.co/api/v2/type/{pokemon_type.lower()}'
        type_response = requests.get(type_url)
        if type_response.status_code != 200:
            return JsonResponse({'error': f'Type "{pokemon_type}" not found'}, status=404)
        
        type_data = type_response.json()
        all_pokemon = [p['pokemon'] for p in type_data['pokemon']]
        
        # Apply search filter if provided
        if search:
            all_pokemon = [p for p in all_pokemon if search in p['name'].lower()]
        
        # Manual pagination
        total_count = len(all_pokemon)
        start_idx = offset
        end_idx = offset + limit
        paginated_pokemon = all_pokemon[start_idx:end_idx]
        
        # Build pagination URLs
        next_url = None
        previous_url = None
        if end_idx < total_count:
            next_url = f"?page={page + 1}"
            if search:
                next_url += f"&search={search}"
            if pokemon_type:
                next_url += f"&type={pokemon_type}"
        if start_idx > 0:
            previous_url = f"?page={page - 1}"
            if search:
                previous_url += f"&search={search}"
            if pokemon_type:
                previous_url += f"&type={pokemon_type}"
        
        if skip_sprites:
            # Don't fetch sprites, just return basic data
            results = []
            for pokemon in paginated_pokemon:
                results.append({
                    'name': pokemon['name'],
                    'url': pokemon['url'],
                    'sprite': None
                })
        else:
            # Fetch sprites concurrently
            pokemon_urls = [p['url'] for p in paginated_pokemon]
            sprites = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_index = {executor.submit(fetch_pokemon_sprite_cached, url): i for i, url in enumerate(pokemon_urls)}
                sprites = [None] * len(pokemon_urls)
                
                for future in concurrent.futures.as_completed(future_to_index):
                    index = future_to_index[future]
                    sprites[index] = future.result()
            
            # Combine data with sprites
            results = []
            for i, pokemon_data in enumerate(paginated_pokemon):
                results.append({
                    'name': pokemon_data['name'],
                    'url': pokemon_data['url'],
                    'sprite': sprites[i]
                })
        
        return JsonResponse({
            'count': total_count,
            'next': next_url,
            'previous': previous_url,
            'results': results
        })
    
    # Handle ability filtering
    elif ability:
        ability_url = f'https://pokeapi.co/api/v2/ability/{ability.lower()}'
        ability_response = requests.get(ability_url)
        if ability_response.status_code != 200:
            return JsonResponse({'error': f'Ability "{ability}" not found'}, status=404)
        
        ability_data = ability_response.json()
        all_pokemon = [p['pokemon'] for p in ability_data['pokemon']]
        
        # Apply search filter if provided
        if search:
            all_pokemon = [p for p in all_pokemon if search in p['name'].lower()]
        
        # Manual pagination
        total_count = len(all_pokemon)
        start_idx = offset
        end_idx = offset + limit
        paginated_pokemon = all_pokemon[start_idx:end_idx]
        
        # Build pagination URLs
        next_url = None
        previous_url = None
        if end_idx < total_count:
            next_url = f"?page={page + 1}"
            if search:
                next_url += f"&search={search}"
            if ability:
                next_url += f"&ability={ability}"
        if start_idx > 0:
            previous_url = f"?page={page - 1}"
            if search:
                previous_url += f"&search={search}"
            if ability:
                previous_url += f"&ability={ability}"
        
        if skip_sprites:
            # Don't fetch sprites, just return basic data
            results = []
            for pokemon in paginated_pokemon:
                results.append({
                    'name': pokemon['name'],
                    'url': pokemon['url'],
                    'sprite': None
                })
        else:
            # Fetch sprites concurrently
            pokemon_urls = [p['url'] for p in paginated_pokemon]
            sprites = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_index = {executor.submit(fetch_pokemon_sprite_cached, url): i for i, url in enumerate(pokemon_urls)}
                sprites = [None] * len(pokemon_urls)
                
                for future in concurrent.futures.as_completed(future_to_index):
                    index = future_to_index[future]
                    sprites[index] = future.result()
            
            # Combine data with sprites
            results = []
            for i, pokemon_data in enumerate(paginated_pokemon):
                results.append({
                    'name': pokemon_data['name'],
                    'url': pokemon_data['url'],
                    'sprite': sprites[i]
                })
        
        return JsonResponse({
            'count': total_count,
            'next': next_url,
            'previous': previous_url,
            'results': results
        })
    
    # Default case with concurrent sprite fetching
    else:
        list_url = f'https://pokeapi.co/api/v2/pokemon?offset={offset}&limit={limit}'
        response = requests.get(list_url)
        
        if response.status_code != 200:
            return JsonResponse({'error': 'Failed to fetch Pokemon list'}, status=500)
        
        data = response.json()
        
        # Filter by search if provided
        pokemon_list = data['results']
        if search:
            pokemon_list = [p for p in pokemon_list if search in p['name'].lower()]
        
        if skip_sprites:
            # Don't fetch sprites, just return basic data
            results = []
            for pokemon in pokemon_list:
                results.append({
                    'name': pokemon['name'],
                    'url': pokemon['url'],
                    'sprite': None
                })
        else:
            # Fetch sprites concurrently
            pokemon_urls = [p['url'] for p in pokemon_list]
            sprites = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_index = {executor.submit(fetch_pokemon_sprite_cached, url): i for i, url in enumerate(pokemon_urls)}
                sprites = [None] * len(pokemon_urls)
                
                for future in concurrent.futures.as_completed(future_to_index):
                    index = future_to_index[future]
                    sprites[index] = future.result()
            
            # Combine data with sprites
            results = []
            for i, pokemon in enumerate(pokemon_list):
                results.append({
                    'name': pokemon['name'],
                    'url': pokemon['url'],
                    'sprite': sprites[i]
                })
        
        # Adjust pagination URLs to include search parameter
        next_url = data['next']
        previous_url = data['previous']
        if search:
            if next_url:
                next_url += f"&search={search}"
            if previous_url:
                previous_url += f"&search={search}"
        
        return JsonResponse({
            'count': data['count'],
            'next': next_url,
            'previous': previous_url,
            'results': results
        })
