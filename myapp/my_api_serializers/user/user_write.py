from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

class UserRegisterWriteSerializer(serializers.ModelSerializer):
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

class UserLoginWriteSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
