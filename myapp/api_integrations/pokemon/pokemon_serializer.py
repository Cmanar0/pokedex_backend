"""
Serializers for Pokemon API data transformation.

These serializers handle the transformation of raw data from the PokeAPI
into our application's expected format.
"""

from rest_framework import serializers


class PokemonAPISerializer(serializers.Serializer):
    """
    Serializer for raw Pokemon data from the PokeAPI.
    This ensures the incoming data matches our expected structure.
    """
    sprites = serializers.DictField(required=False)
    types = serializers.ListField(required=False)
    abilities = serializers.ListField(required=False)
    height = serializers.IntegerField(required=False)
    weight = serializers.IntegerField(required=False)

    def to_internal_value(self, data):
        """
        Transform the raw API data into our expected format.
        """
        if not data:
            return {
                'sprite': None,
                'types': [],
                'abilities': [],
                'height': None,
                'weight': None,
            }

        return {
            'sprite': data.get('sprites', {}).get('front_default'),
            'types': [t['type']['name'] for t in data.get('types', [])],
            'abilities': [a['ability']['name'] for a in data.get('abilities', [])],
            'height': data.get('height'),
            'weight': data.get('weight'),
        }


class EvolutionChainSerializer(serializers.Serializer):
    """
    Serializer for Pokemon evolution chain data from the PokeAPI.
    This ensures the evolution chain data matches our expected structure.
    """
    species = serializers.DictField(required=True)
    evolves_to = serializers.ListField(required=True)

    def to_internal_value(self, data):
        """
        Transform the raw evolution chain data into our expected format.
        """
        if not data:
            return {
                'name': None,
                'evolves_to': []
            }

        def parse_chain(chain_node):
            species = chain_node['species']['name']
            evolves_to = chain_node['evolves_to']
            return {
                'name': species,
                'evolves_to': [parse_chain(evo) for evo in evolves_to] if evolves_to else []
            }

        return parse_chain(data)


class TypeSerializer(serializers.Serializer):
    name = serializers.CharField()


class AbilitySerializer(serializers.Serializer):
    name = serializers.CharField() 