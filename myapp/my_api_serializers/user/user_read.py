from rest_framework import serializers
from django.contrib.auth.models import User
from myapp.models import UserProfile

class UserProfileReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('favorite_pokemon', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
