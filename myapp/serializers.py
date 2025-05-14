"""
Serializers for Pokemon API responses.

Serializers in DRF handle:
- Converting complex data types (like Django models) to Python data types
- Validating incoming data
- Rendering data in various formats (JSON, XML, etc.)
- Consistent data formatting across the application
"""

from rest_framework import serializers


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