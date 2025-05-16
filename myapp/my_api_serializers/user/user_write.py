from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class UserRegisterWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8,
        error_messages={
            'min_length': 'Password must be at least 8 characters long.',
            'required': 'Password is required.',
            'blank': 'Password cannot be blank.'
        }
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={
            'required': 'Please confirm your password.',
            'blank': 'Password confirmation cannot be blank.'
        }
    )
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'Email is required.',
            'invalid': 'Please enter a valid email address.',
            'blank': 'Email cannot be blank.'
        }
    )
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
            'username': {'required': False}  # We'll set this from email
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "The two password fields didn't match."
            })
        
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            # Convert Django's password validation errors to user-friendly messages
            error_messages = []
            for error in e.messages:
                if "too short" in error.lower():
                    error_messages.append("Password is too short. It must contain at least 8 characters.")
                elif "too common" in error.lower():
                    error_messages.append("This password is too common. Please choose a stronger password.")
                elif "entirely numeric" in error.lower():
                    error_messages.append("Password cannot be entirely numeric.")
                elif "similar to your username" in error.lower():
                    error_messages.append("Password cannot be too similar to your email address.")
                else:
                    error_messages.append(error)
            raise serializers.ValidationError({"password": error_messages})
        
        # Check if email is already in use
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({
                "email": "This email address is already registered. Please use a different email or try logging in."
            })
        
        return attrs

    def create(self, validated_data):
        # Extract profile data
        favorite_pokemon = validated_data.pop('favorite_pokemon', [])
        
        # Remove password2 from user creation
        validated_data.pop('password2')
        
        # Set username to email
        validated_data['username'] = validated_data['email']
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Update profile with favorite pokemon list
        user.profile.favorite_pokemon = favorite_pokemon
        user.profile.save()
        
        return user

class UserLoginWriteSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
