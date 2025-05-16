import requests
import concurrent.futures
from typing import List, Dict, Optional
from django.core.cache import cache
from .pokemon_serializer import PokemonAPISerializer

BASE_URL = "https://pokeapi.co/api/v2"
POKEMON_URL = f"{BASE_URL}/pokemon"
TYPE_URL = f"{BASE_URL}/type"
ABILITY_URL = f"{BASE_URL}/ability"
REQUEST_TIMEOUT = 5
MAX_CONCURRENT_REQUESTS = 9

# Cache timeouts (in seconds)
CACHE_TIMEOUT = 3600  # 1 hour for base list
DETAIL_CACHE_TIMEOUT = 86400  # 24 hours for individual Pokémon details


def _make_http_request(url: str) -> Optional[Dict]:
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        return response.json() if response.status_code == 200 else None
    except:
        return None


def fetch_pokemon_list(offset: int = 0, limit: int = 9, search: str = None) -> Optional[Dict]:
    """
    Fetch Pokémon list from PokeAPI with pagination and caching.
    The PokeAPI supports pagination through offset and limit parameters.
    """
    # Generate cache key based on parameters
    cache_key = f"pokemon_list_{offset}_{limit}_{search}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data

    url = f"{POKEMON_URL}?offset={offset}&limit={limit}"
    if search:
        url += f"&search={search}"
    
    data = _make_http_request(url)
    if data:
        cache.set(cache_key, data, CACHE_TIMEOUT)
    return data


def fetch_pokemon_by_type(type_name: str) -> Optional[List[str]]:
    """Fetch all Pokémon of a specific type with caching."""
    cache_key = f"pokemon_type_{type_name.lower()}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data

    url = f"{TYPE_URL}/{type_name.lower()}"
    data = _make_http_request(url)
    if not data:
        return None
    
    pokemon_list = [p['pokemon']['name'] for p in data.get('pokemon', [])]
    cache.set(cache_key, pokemon_list, CACHE_TIMEOUT)
    return pokemon_list


def fetch_pokemon_by_ability(ability_name: str) -> Optional[List[str]]:
    """Fetch all Pokémon with a specific ability with caching."""
    cache_key = f"pokemon_ability_{ability_name.lower()}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data

    url = f"{ABILITY_URL}/{ability_name.lower()}"
    data = _make_http_request(url)
    if not data:
        return None
    
    pokemon_list = [p['pokemon']['name'] for p in data.get('pokemon', [])]
    cache.set(cache_key, pokemon_list, CACHE_TIMEOUT)
    return pokemon_list


def fetch_pokemon_detail(pokemon_url: str) -> Dict:
    """Fetch Pokémon details with caching."""
    cache_key = f"pokemon_detail_{pokemon_url}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data

    data = _make_http_request(pokemon_url)
    if not data:
        return {
            'sprite': None,
            'types': [],
            'abilities': [],
            'height': None,
            'weight': None
        }

    serializer = PokemonAPISerializer(data=data)
    result = serializer.to_internal_value(data)
    cache.set(cache_key, result, DETAIL_CACHE_TIMEOUT)
    return result


def fetch_multiple_pokemon_details(pokemon_urls: List[str]) -> List[Dict]:
    if not pokemon_urls:
        return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        future_to_index = {
            executor.submit(fetch_pokemon_detail, url): i
            for i, url in enumerate(pokemon_urls)
        }

        results = [None] * len(pokemon_urls)
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                results[index] = future.result()
            except:
                results[index] = {
                    'sprite': None,
                    'types': [],
                    'abilities': [],
                    'height': None,
                    'weight': None
                }

    return results
