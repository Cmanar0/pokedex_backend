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

def fetch_pokemon_details(pokemon_url):
    """Fetch sprite, types, and abilities for a single Pokemon"""
    try:
        response = requests.get(pokemon_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'sprite': data.get('sprites', {}).get('front_default'),
                'types': [t['type']['name'] for t in data.get('types', [])],
                'abilities': [a['ability']['name'] for a in data.get('abilities', [])],
                'height': data.get('height'),  # in decimeters
                'weight': data.get('weight'),  # in hectograms
            }
    except:
        pass
    return {
        'sprite': None,
        'types': [],
        'abilities': [],
        'height': None,
        'weight': None,
    }

def fetch_pokemon_details_cached(pokemon_url):
    """Fetch Pokemon details with caching"""
    cache_key = f"pokemon_{hashlib.md5(pokemon_url.encode()).hexdigest()}"
    cached_details = cache.get(cache_key)
    
    if cached_details is not None:
        return cached_details
    
    details = fetch_pokemon_details(pokemon_url)
    # Cache for 1 hour
    cache.set(cache_key, details, 3600)
    return details

@api_view(['GET'])
def get_pokemon_list(request):
    skip_details = request.GET.get('skip_details', 'false').lower() == 'true'
    page = int(request.GET.get('page', 1))
    search = request.GET.get('search', '').lower()
    pokemon_type = request.GET.get('type')
    ability = request.GET.get('ability')
    limit = 9
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
        
        if skip_details:
            # Don't fetch details, just return basic data
            results = []
            for pokemon in paginated_pokemon:
                results.append({
                    'name': pokemon['name'],
                    'sprite': None,
                    'types': [],
                    'abilities': [],
                    'height': None,
                    'weight': None,
                })
        else:
            # Fetch details concurrently
            pokemon_urls = [p['url'] for p in paginated_pokemon]
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=9) as executor:
                future_to_index = {executor.submit(fetch_pokemon_details_cached, url): i for i, url in enumerate(pokemon_urls)}
                details_list = [None] * len(pokemon_urls)
                
                for future in concurrent.futures.as_completed(future_to_index):
                    index = future_to_index[future]
                    details_list[index] = future.result()
            
            # Combine data with details
            results = []
            for i, pokemon_data in enumerate(paginated_pokemon):
                details = details_list[i] or {}
                results.append({
                    'name': pokemon_data['name'],
                    'sprite': details.get('sprite'),
                    'types': details.get('types', []),
                    'abilities': details.get('abilities', []),
                    'height': details.get('height'),
                    'weight': details.get('weight'),
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
        
        if skip_details:
            # Don't fetch details, just return basic data
            results = []
            for pokemon in paginated_pokemon:
                results.append({
                    'name': pokemon['name'],
                    'sprite': None,
                    'types': [],
                    'abilities': [],
                    'height': None,
                    'weight': None,
                })
        else:
            # Fetch details concurrently
            pokemon_urls = [p['url'] for p in paginated_pokemon]
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=9) as executor:
                future_to_index = {executor.submit(fetch_pokemon_details_cached, url): i for i, url in enumerate(pokemon_urls)}
                details_list = [None] * len(pokemon_urls)
                
                for future in concurrent.futures.as_completed(future_to_index):
                    index = future_to_index[future]
                    details_list[index] = future.result()
            
            # Combine data with details
            results = []
            for i, pokemon_data in enumerate(paginated_pokemon):
                details = details_list[i] or {}
                results.append({
                    'name': pokemon_data['name'],
                    'sprite': details.get('sprite'),
                    'types': details.get('types', []),
                    'abilities': details.get('abilities', []),
                    'height': details.get('height'),
                    'weight': details.get('weight'),
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
        
        if skip_details:
            # Don't fetch details, just return basic data
            results = []
            for pokemon in pokemon_list:
                results.append({
                    'name': pokemon['name'],
                    'sprite': None,
                    'types': [],
                    'abilities': [],
                    'height': None,
                    'weight': None,
                })
        else:
            # Fetch details concurrently
            pokemon_urls = [p['url'] for p in pokemon_list]
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=9) as executor:
                future_to_index = {executor.submit(fetch_pokemon_details_cached, url): i for i, url in enumerate(pokemon_urls)}
                details_list = [None] * len(pokemon_urls)
                
                for future in concurrent.futures.as_completed(future_to_index):
                    index = future_to_index[future]
                    details_list[index] = future.result()
            
            # Combine data with details
            results = []
            for i, pokemon in enumerate(pokemon_list):
                details = details_list[i] or {}
                results.append({
                    'name': pokemon['name'],
                    'sprite': details.get('sprite'),
                    'types': details.get('types', []),
                    'abilities': details.get('abilities', []),
                    'height': details.get('height'),
                    'weight': details.get('weight'),
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
