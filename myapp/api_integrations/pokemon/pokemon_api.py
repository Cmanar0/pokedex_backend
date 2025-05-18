import requests
import concurrent.futures
from typing import List, Dict, Optional, Any
from django.core.cache import cache
from .pokemon_serializer import PokemonAPISerializer, EvolutionChainSerializer, TypeSerializer, AbilitySerializer
import logging

BASE_URL = "https://pokeapi.co/api/v2"
POKEMON_URL = f"{BASE_URL}/pokemon"
TYPE_URL = f"{BASE_URL}/type"
ABILITY_URL = f"{BASE_URL}/ability"
REQUEST_TIMEOUT = 5
MAX_CONCURRENT_REQUESTS = 9

# Cache timeouts (in seconds)
CACHE_TIMEOUT = 3600  # 1 hour for base list
DETAIL_CACHE_TIMEOUT = 86400  # 24 hours for individual Pokémon details

logger = logging.getLogger(__name__)


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
    """Fetch detailed information for a specific Pokémon."""
    logger.info(f"Fetching pokemon detail from URL: {pokemon_url}")
    
    # Check cache first
    cache_key = f"pokemon_detail_{pokemon_url}"
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"Using cached data for {pokemon_url}")
        return cached_data
    
    # If not in cache, fetch from API
    data = _make_http_request(pokemon_url)
    if not data:
        logger.error(f"Failed to fetch data for URL: {pokemon_url}")
        return {
            'sprite': None,
            'types': [],
            'abilities': [],
            'height': None,
            'weight': None,
        }

    logger.info(f"Raw API response for {pokemon_url}: {data}")
    
    try:
        serializer = PokemonAPISerializer(data=data)
        if not serializer.is_valid():
            logger.error(f"Serializer validation failed for {pokemon_url}: {serializer.errors}")
            return {
                'sprite': None,
                'types': [],
                'abilities': [],
                'height': None,
                'weight': None,
            }
        
        result = serializer.to_internal_value(data)
        logger.info(f"Processed pokemon data for {pokemon_url}: {result}")
        
        # Cache the result
        cache.set(cache_key, result, DETAIL_CACHE_TIMEOUT)
        return result
    except Exception as e:
        logger.error(f"Error processing pokemon data for {pokemon_url}: {str(e)}")
        return {
            'sprite': None,
            'types': [],
            'abilities': [],
            'height': None,
            'weight': None,
        }


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


def fetch_pokemon_evolution_chain(name: str) -> Optional[Dict]:
    """
    Fetch and return the full evolution chain for the given Pokémon name.
    This involves two API requests:
      1. Get the Pokémon species URL from /pokemon/{name}
      2. Get the evolution_chain URL from the species response
    """
    cache_key = f"evolution_chain_{name.lower()}"
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"Using cached evolution chain for {name}")
        return cached_data

    species_url = f"{BASE_URL}/pokemon-species/{name.lower()}"
    species_data = _make_http_request(species_url)
    if not species_data or 'evolution_chain' not in species_data:
        logger.error(f"Failed to fetch species data for {name}")
        return None

    chain_url = species_data['evolution_chain']['url']
    evolution_data = _make_http_request(chain_url)
    if not evolution_data or 'chain' not in evolution_data:
        logger.error(f"Failed to fetch evolution chain for {name}")
        return None

    try:
        serializer = EvolutionChainSerializer(data=evolution_data['chain'])
        if not serializer.is_valid():
            logger.error(f"Serializer validation failed for evolution chain: {serializer.errors}")
            return None
        
        result = serializer.to_internal_value(evolution_data['chain'])
        cache.set(cache_key, result, DETAIL_CACHE_TIMEOUT)
        logger.info(f"Cached evolution chain for {name}")
        return result
    except Exception as e:
        logger.error(f"Error processing evolution chain data: {str(e)}")
        return None


def fetch_all_types() -> List[Dict[str, Any]]:
    """Fetch all Pokémon types from the PokeAPI."""
    try:
        response = requests.get(f"{BASE_URL}/type")
        response.raise_for_status()
        data = response.json()
        # Only return the names
        return [{"name": type_data["name"]} for type_data in data["results"]]
    except requests.RequestException as e:
        print(f"Error fetching types: {e}")
        return []


import requests
from typing import List, Dict, Any

def fetch_all_abilities() -> List[Dict[str, Any]]:
    """Fetch all Pokémon abilities from the PokeAPI using pagination."""
    abilities = []
    url = f"{BASE_URL}/ability?offset=0&limit=100"

    while url:
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            abilities.extend(data["results"])
            url = data.get("next")  # URL to next page
        except requests.RequestException as e:
            print(f"Error fetching abilities: {e}")
            break

    return [{"name": ability["name"]} for ability in abilities]
