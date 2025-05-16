"""
Read serializers for Pokemon API responses.

These serializers handle formatting the response data from the Pokemon API
into a consistent structure for the frontend.
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


class PokemonListSerializer(serializers.Serializer):
    """
    Serializer for Pokemon list items.
    
    This defines the structure of each Pokemon in the list response.
    Using a serializer ensures consistent formatting and makes it easy
    to add/remove fields or change validation rules.
    """
    name = serializers.CharField(max_length=100)
    sprite = serializers.URLField(allow_null=True, required=False)
    types = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list
    )
    abilities = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list
    )
    height = serializers.IntegerField(allow_null=True, required=False)
    weight = serializers.IntegerField(allow_null=True, required=False)


class PokemonListResponseSerializer(serializers.Serializer):
    """
    Serializer for the complete Pokemon list response.
    
    This wraps the paginated results with metadata like count, next, previous.
    """
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True, required=False)
    previous = serializers.URLField(allow_null=True, required=False)
    results = PokemonListSerializer(many=True) 