"""
Models package for Recipe Sharing Platform

This package contains all database models and utility functions.
Import models and utilities from this package for clean, organized code.

Example usage:
    from models import User, Recipe, Tag, Like, Favorite
    from models import get_trending_recipes, get_recipe_recommendations
    
    # Create a user
    user = User()
    user.username = "chef_master"
    user.save()
    
    # Get trending recipes
    trending = get_trending_recipes(days=7, limit=10)
"""

# models/__init__.py
from .base_model import BaseModel
from .user import User

__all__ = ['BaseModel', 'User']

# # Import all model classes
# from .user import User
# from .recipe import Recipe
# from .tag import Tag
# from .like import Like
# from .favorite import Favorite

# # Import utility functions
# from .utils import (
#     get_trending_recipes,
#     get_recipe_recommendations,
#     get_recent_recipes,
#     get_user_activity_feed,
#     search_users,
#     get_database_statistics
# )

# # Define what gets imported when someone does "from models import *"
# __all__ = [
#     # Base model
#     "BaseModel",
    
#     # Model classes
#     "User",
#     "Recipe", 
#     "Tag",
#     "Like",
#     "Favorite",
    
#     # Utility functions
#     "get_trending_recipes",
#     "get_recipe_recommendations", 
#     "get_recent_recipes",
#     "get_user_activity_feed",
#     "search_users",
#     "get_database_statistics"
# ]

# # Package metadata
# __version__ = "1.0.0"
# __author__ = "Recipe Platform Team"
# __description__ = "Database models for Recipe Sharing Platform"

# # Package-level constants
# DEFAULT_PAGE_SIZE = 20
# MAX_PAGE_SIZE = 100
# DEFAULT_TRENDING_DAYS = 7

# # Validation constants
# MIN_USERNAME_LENGTH = 3
# MAX_USERNAME_LENGTH = 50
# MIN_PASSWORD_LENGTH = 6
# MAX_RECIPE_TITLE_LENGTH = 100
# MAX_RECIPE_DESCRIPTION_LENGTH = 500
# MAX_TAG_NAME_LENGTH = 50

# print("📦 Models package loaded successfully")