import requests
import concurrent.futures
from typing import List, Dict, Optional
from .pokemon_serializer import PokemonAPISerializer

BASE_URL = "https://pokeapi.co/api/v2"
POKEMON_URL = f"{BASE_URL}/pokemon"
TYPE_URL = f"{BASE_URL}/type"
ABILITY_URL = f"{BASE_URL}/ability"
REQUEST_TIMEOUT = 5
MAX_CONCURRENT_REQUESTS = 9


def _make_http_request(url: str) -> Optional[Dict]:
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        return response.json() if response.status_code == 200 else None
    except:
        return None


def fetch_pokemon_list(offset: int = 0, limit: int = 9) -> Optional[Dict]:
    """
    Fetch Pokémon list from PokeAPI with pagination.
    The PokeAPI supports pagination through offset and limit parameters.
    """
    url = f"{POKEMON_URL}?offset={offset}&limit={limit}"
    return _make_http_request(url)


def fetch_pokemon_by_type(type_name: str) -> Optional[List[str]]:
    """Fetch all Pokémon of a specific type."""
    url = f"{TYPE_URL}/{type_name.lower()}"
    data = _make_http_request(url)
    if not data:
        return None
    return [p['pokemon']['name'] for p in data.get('pokemon', [])]


def fetch_pokemon_by_ability(ability_name: str) -> Optional[List[str]]:
    """Fetch all Pokémon with a specific ability."""
    url = f"{ABILITY_URL}/{ability_name.lower()}"
    data = _make_http_request(url)
    if not data:
        return None
    return [p['pokemon']['name'] for p in data.get('pokemon', [])]


def fetch_pokemon_detail(pokemon_url: str) -> Dict:
    data = _make_http_request(pokemon_url)
    serializer = PokemonAPISerializer(data=data)
    return serializer.to_internal_value(data)


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
                    'sprite': None, 'types': [], 'abilities': [],
                    'height': None, 'weight': None
                }

    return results
