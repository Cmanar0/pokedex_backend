from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_http_methods
from rest_framework.decorators import api_view
import json
import requests

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
def get_pokemon_list(request):
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
        
        results = []
        for pokemon_data in paginated_pokemon:
            detail_response = requests.get(pokemon_data['url'])
            sprite = None
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                sprite = detail_data.get('sprites', {}).get('front_default')
            
            results.append({
                'name': pokemon_data['name'],
                'url': pokemon_data['url'],
                'sprite': sprite
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
        
        results = []
        for pokemon_data in paginated_pokemon:
            detail_response = requests.get(pokemon_data['url'])
            sprite = None
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                sprite = detail_data.get('sprites', {}).get('front_default')
            
            results.append({
                'name': pokemon_data['name'],
                'url': pokemon_data['url'],
                'sprite': sprite
            })
        
        return JsonResponse({
            'count': total_count,
            'next': next_url,
            'previous': previous_url,
            'results': results
        })
    
    # Default case: fetch from main pokemon endpoint
    else:
        list_url = f'https://pokeapi.co/api/v2/pokemon?offset={offset}&limit={limit}'
        response = requests.get(list_url)
        
        if response.status_code != 200:
            return JsonResponse({'error': 'Failed to fetch Pokemon list'}, status=500)
        
        data = response.json()
        
        # Fetch sprites for each Pokemon and apply search filter
        results = []
        for pokemon in data['results']:
            # Apply search filter
            if search and search not in pokemon['name'].lower():
                continue
                
            # Get Pokemon details to fetch sprite
            detail_response = requests.get(pokemon['url'])
            sprite = None
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                sprite = detail_data.get('sprites', {}).get('front_default')
            
            results.append({
                'name': pokemon['name'],
                'url': pokemon['url'],
                'sprite': sprite
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
