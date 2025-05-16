import requests
import concurrent.futures
from django.core.cache import cache
import hashlib
from typing import List, Dict, Optional
from .pokemon_serializer import PokemonAPISerializer

BASE_URL = "https://pokeapi.co/api/v2/pokemon"
CACHE_TIMEOUT = 3600
REQUEST_TIMEOUT = 5
MAX_CONCURRENT_REQUESTS = 9


def _make_http_request(url: str) -> Optional[Dict]:
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        return response.json() if response.status_code == 200 else None
    except:
        return None


def _generate_cache_key(url: str) -> str:
    return f"pokeapi_{hashlib.md5(url.encode()).hexdigest()}"


def fetch_with_cache(url: str) -> Optional[Dict]:
    cache_key = _generate_cache_key(url)
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    data = _make_http_request(url)
    if data is not None:
        cache.set(cache_key, data, CACHE_TIMEOUT)

    return data


def fetch_pokemon_list(offset: int = 0, limit: int = 9) -> Optional[Dict]:
    url = f"{BASE_URL}?offset={offset}&limit={limit}"
    return fetch_with_cache(url)


def fetch_pokemon_detail(pokemon_url: str) -> Dict:
    data = fetch_with_cache(pokemon_url)
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
