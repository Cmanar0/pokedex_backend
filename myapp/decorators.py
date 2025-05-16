from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)

def handle_api_errors(view_func):
    """
    A decorator to handle common API errors and provide consistent error responses.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            # Log the error
            logger.error(f"Error in {view_func.__name__}: {str(e)}")
            
            # Return appropriate error response
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    return wrapper

def require_authentication(view_func):
    """
    A decorator to ensure the user is authenticated and return user data.
    Automatically adds user and profile data to the response.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get the original response
        response = view_func(request, *args, **kwargs)
        
        # If the response is a dict and doesn't already have user data, add it
        if isinstance(response.data, dict) and 'user' not in response.data:
            from .my_api_serializers.user.user_read import UserReadSerializer, UserProfileReadSerializer
            user_data = UserReadSerializer(request.user).data
            profile_data = UserProfileReadSerializer(request.user.profile).data
            
            response.data = {
                **response.data,
                'user': {
                    **user_data,
                    'profile': profile_data
                }
            }
        
        return response
    return wrapper

def validate_with_serializer(serializer_class):
    """
    A decorator to validate request data using a serializer.
    Automatically handles validation errors and returns appropriate responses.
    
    Args:
        serializer_class: The DRF serializer class to use for validation
        
    Example:
        @validate_with_serializer(UserLoginWriteSerializer)
        def login_view(request):
            # Access validated data via request.validated_data
            username = request.validated_data['username']
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            serializer = serializer_class(data=request.data)
            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Add validated data to request
            request.validated_data = serializer.validated_data
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def paginate_response(limit=9):
    """
    A decorator to handle pagination of list responses.
    Automatically adds pagination metadata to the response.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get pagination parameters
            page = max(1, int(request.GET.get('page', 1))) if request.GET.get('page', '').isdigit() else 1
            offset = (page - 1) * limit
            
            # Add pagination info to request
            request.pagination = {
                'page': page,
                'limit': limit,
                'offset': offset
            }
            
            # Get the original response
            response = view_func(request, *args, **kwargs)
            
            # If the response is a dict and contains results, add pagination metadata
            if isinstance(response.data, dict) and 'results' in response.data:
                total_count = response.data.get('count', len(response.data['results']))
                total_pages = (total_count + limit - 1) // limit
                
                response.data.update({
                    'pagination': {
                        'current_page': page,
                        'total_pages': total_pages,
                        'total_items': total_count,
                        'items_per_page': limit,
                        'has_next': page < total_pages,
                        'has_previous': page > 1
                    }
                })
            
            return response
        return wrapper
    return decorator 