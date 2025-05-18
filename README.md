# Pokédex Backend

A Django-based backend service for the Pokédex application that provides Pokémon data from the PokéAPI. This repo serves as a backend part of a showcase project that integrates with the PokéAPI to provide a set of features for displaying and interaction with Pokemon. It includes user authentication, profile management, and detailed Pokémon information retrieval with advanced filtering capabilities.

## Features

- Fetch Pokémon list with pagination
- Get detailed Pokémon information
- Search Pokémon by name
- Filter Pokémon by type and abilities
- Get all available types and abilities
- User authentication and profile management
- Favorite Pokémon management

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Make and apply migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Run the development server:
```bash
python manage.py runserver
```

## API Documentation
The API will be available at http://localhost:8000


## Implementation Notes

### Key Features and Solutions

1. **Authentication System**
   - Custom user registration and login views
   - Session-based authentication with CSRF protection

2. **User Profile Features**
   - Favorite Pokémon management with add/remove functionality
   - Profile data serialization
   - Nested user and profile data structure

3. **API Integration**
   - Error handling for external API calls
   - Proper response formatting and status code handling

4. **Security Measures**
   - CSRF protection for all POST requests
   - Authentication requirements for endpoints

5. **Performance Optimizations**
   - Pagination to handle large datasets (loading more data on scroll)
   - Caching strategies for frequently accessed data
