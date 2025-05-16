"""
Serializers for Pokemon API responses.

Serializers in DRF handle:
- Converting complex data types (like Django models) to Python data types
- Validating incoming data
- Rendering data in various formats (JSON, XML, etc.)
- Consistent data formatting across the application
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile


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


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('favorite_pokemon', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    favorite_pokemon = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list
    )

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name',
                 'favorite_pokemon')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'email': {'required': False}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        # Extract profile data
        favorite_pokemon = validated_data.pop('favorite_pokemon', [])
        
        # Remove password2 from user creation
        validated_data.pop('password2')
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Update profile with favorite pokemon list
        user.profile.favorite_pokemon = favorite_pokemon
        user.profile.save()
        
        return user 