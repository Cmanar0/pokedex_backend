from django.urls import path
from .views import login_view, logout_view, check_auth
from . import views

urlpatterns = [
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/me/', check_auth, name='check-auth'),
    path('csrf/', views.get_csrf_token, name='csrf-token'),
]
