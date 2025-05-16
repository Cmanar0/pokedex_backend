from django.urls import path
from .views import (
    login_view, logout_view, check_auth, pokemon_list,
    register_view, user_profile_view, pokemon_detail, update_favorite_pokemon,
    favorite_pokemon_list
)
from . import views

urlpatterns = [
    path('auth/register/', register_view, name='register'),
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/me/', check_auth, name='check-auth'),
    path('csrf/', views.get_csrf_token, name='csrf-token'),
    path('pokemon/favorites/', favorite_pokemon_list, name='favorite-pokemon-list'),
    path('pokemon/<str:name>/', pokemon_detail, name='pokemon-detail'),
    path('pokemon/', pokemon_list, name='pokemon-list'),
    path('profile/', user_profile_view, name='user-profile'),
    path('user/favorite-pokemon/', update_favorite_pokemon, name='update_favorite_pokemon'),
]
