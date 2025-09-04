"""
Recipe Routes - Controller Layer for ShareBite backend

This module provides recipe endpoints following MVC architecture.
Controllers handle requests and coordinate with models to return responses.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from routes.auth_routes import verify_token
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import models
from models.recipe import Recipe
from models.user import User
from models.like import Like
from models.favorite import Favorite

from routes.auth_routes import SECRET_KEY
print(f"Recipe routes using SECRET_KEY: {SECRET_KEY[:10]}...")

router = APIRouter(prefix="/recipes", tags=["Recipes"])

# ============= CACHE IMPLEMENTATION =============
class RecipeCache:
    """
    Fixed Write-Through Cache for recipes with proper user separation
    """
    def __init__(self):
        self.recipes_data = None  # Base recipe data (without user-specific info)
        self.recipes_lookup = {}  # recipe_id -> recipe dict for fast access
        self.timestamp = None
        self.duration = timedelta(minutes=10)
        self.current_user_id = None  # Track which user's data we're caching
        self.user_likes = set()  # Current user's likes
        self.user_favorites = set()  # Current user's favorites
        
    def is_valid(self) -> bool:
        """Check if cache is valid"""
        if self.recipes_data is None or self.timestamp is None:
            return False
        return datetime.now() - self.timestamp < self.duration
    
    def is_user_valid(self, user_id: int) -> bool:
        """Check if cache is valid for specific user"""
        return self.is_valid() and self.current_user_id == user_id
    
    def get_recipes(self, user_id: int, limit: int, offset: int) -> Optional[List[Dict]]:
        """
        Get recipes from cache if valid for this user
        """
        if not self.is_user_valid(user_id):
            print(f"Cache invalid for user {user_id} (current user: {self.current_user_id})")
            return None
        
        # Get paginated recipes
        recipes = []
        for i in range(offset, min(offset + limit, len(self.recipes_data))):
            if i < len(self.recipes_data):
                recipe = self.recipes_data[i].copy()  # Copy to avoid modifying original
                
                # Apply user-specific states
                recipe['is_liked'] = recipe['recipe_id'] in self.user_likes
                recipe['is_favorited'] = recipe['recipe_id'] in self.user_favorites
                
                recipes.append(recipe)
        
        print(f"Returning {len(recipes)} recipes from cache for user {user_id}")
        return recipes
    
    def update_cache(self, recipes: List[Dict], user_id: int):
        """Update cache with new recipe list and user-specific data"""
        print(f"Updating cache for user {user_id} with {len(recipes)} recipes")
        
        # Store base recipe data (without user-specific states)
        self.recipes_data = []
        self.recipes_lookup = {}
        self.user_likes = set()
        self.user_favorites = set()
        
        for recipe in recipes:
            # Store base recipe data
            base_recipe = recipe.copy()
            # Remove user-specific data from base storage
            base_recipe['is_liked'] = False
            base_recipe['is_favorited'] = False
            
            self.recipes_data.append(base_recipe)
            self.recipes_lookup[recipe['recipe_id']] = base_recipe
            
            # Store user-specific states separately
            if recipe.get('is_liked'):
                self.user_likes.add(recipe['recipe_id'])
            if recipe.get('is_favorited'):
                self.user_favorites.add(recipe['recipe_id'])
        
        self.current_user_id = user_id
        self.timestamp = datetime.now()
        print(f"Cache updated: {len(self.user_likes)} likes, {len(self.user_favorites)} favorites")
    
    def update_like_status(self, recipe_id: int, user_id: int, is_liked: bool):
        """Update like status for specific user"""
        print(f"Updating like cache: recipe {recipe_id}, user {user_id}, liked: {is_liked}")
        
        # Update base recipe likes count using O(1) lookup
        if recipe_id in self.recipes_lookup:
            recipe = self.recipes_lookup[recipe_id]
            current_count = recipe.get('likes_count', 0)
            
            # Check if this user's like state is changing
            user_currently_likes = recipe_id in self.user_likes
            
            if is_liked and not user_currently_likes:
                # User is liking (wasn't liked before)
                recipe['likes_count'] = current_count + 1
                self.user_likes.add(recipe_id)
            elif not is_liked and user_currently_likes:
                # User is unliking (was liked before) 
                recipe['likes_count'] = max(0, current_count - 1)
                self.user_likes.discard(recipe_id)
            
            print(f"Updated recipe {recipe_id}: likes_count={recipe['likes_count']}, user_likes={is_liked}")
        
        # Verify user context
        if self.current_user_id != user_id:
            print(f"Warning: Like update for user {user_id} but cache is for user {self.current_user_id}")
    
    def update_favorite_status(self, recipe_id: int, user_id: int, is_favorited: bool):
        """Update favorite status for specific user"""
        print(f"Updating favorite cache: recipe {recipe_id}, user {user_id}, favorited: {is_favorited}")
        
        if is_favorited:
            self.user_favorites.add(recipe_id)
        else:
            self.user_favorites.discard(recipe_id)
        
        # Verify user context
        if self.current_user_id != user_id:
            print(f"Warning: Favorite update for user {user_id} but cache is for user {self.current_user_id}")
    
    def invalidate(self):
        """Clear cache completely"""
        self.recipes_data = None
        self.recipes_lookup = {}
        self.user_likes = set()
        self.user_favorites = set()
        self.current_user_id = None
        self.timestamp = None
        print("Cache invalidated completely")
    
    def invalidate_for_user(self, user_id: int):
        """Invalidate cache if it belongs to specific user"""
        if self.current_user_id == user_id:
            self.invalidate()
            print(f"Cache invalidated for user {user_id}")
        else:
            print(f"Cache not invalidated - belongs to user {self.current_user_id}, not {user_id}")

# Create global cache instance
cache = RecipeCache()

# ============= PYDANTIC MODELS =============
class RecipeResponse(BaseModel):
    recipe_id: int
    title: str
    description: str
    author_name: str
    author_id: int
    image_url: Optional[str] = None
    ingredients: Optional[str] = None
    instructions: Optional[str] = None
    raw_ingredients: Optional[str] = None
    servings: Optional[int] = None
    created_at: str
    likes_count: int = 0
    is_liked: bool = False
    is_favorited: bool = False

class RecipeListResponse(BaseModel):
    recipes: List[RecipeResponse]
    total_count: int
    limit: int
    offset: int
    from_cache: bool = False

# ============= ENDPOINTS =============

@router.get("/search", response_model=RecipeListResponse)
async def search_recipes(
    q: str = Query(..., description="Search query for recipe title, description, or ingredients"),
    category: Optional[str] = Query(None, description="Filter by category (breakfast, lunch, dinner, dessert, snacks)"),
    author: Optional[str] = Query(None, description="Filter by author name"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(verify_token)
):
    """
    Search recipes with filters and pagination
    Searches in title, description, ingredients, and raw_ingredients
    """
    try:
        user_id = current_user['userid']
        print(f"Searching recipes for user: {current_user['username']} (ID: {user_id})")
        print(f"Query: '{q}', Category: {category}, Author: {author}")
        
        # Log search event using model
        search_event_data = {
            "search_query": q,
            "category": category,
            "author": author,
            "limit": limit,
            "offset": offset
        }
        Recipe.log_recipe_event(0, user_id, "Searched", search_event_data)
        
        # Search recipes using model
        search_result = Recipe.search_recipes_with_filters(
            user_id=user_id,
            query=q,
            category=category,
            author=author,
            limit=limit,
            offset=offset
        )
        
        recipes = search_result["recipes"]
        total_count = search_result["total_count"]
        
        print(f"Returning {len(recipes)} search results (total: {total_count})")
        
        return RecipeListResponse(
            recipes=recipes,
            total_count=total_count,
            limit=limit,
            offset=offset,
            from_cache=False
        )
        
    except Exception as e:
        print(f"Error searching recipes: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search recipes: {str(e)}"
        )
        
@router.get("", response_model=RecipeListResponse)
async def get_recipes(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    force_refresh: bool = Query(False, description="Force refresh from database"),
    current_user: dict = Depends(verify_token)
):
    """
    Get paginated list of recipes with user-aware caching
    """
    try:
        user_id = current_user['userid']
        print(f"Getting recipes for user: {current_user['username']} (ID: {user_id}) (limit: {limit}, offset: {offset})")
        
        # Log view event (only if not from cache and not forced refresh)
        if force_refresh or not cache.is_user_valid(user_id):
            view_event_data = {
                "limit": limit,
                "offset": offset,
                "force_refresh": force_refresh
            }
            Recipe.log_recipe_event(0, user_id, "ViewedList", view_event_data)
        
        # Check if we need to refresh due to user change or force refresh
        if not force_refresh:
            cached_recipes = cache.get_recipes(user_id, limit, offset)
            if cached_recipes is not None:
                print(f"Returning {len(cached_recipes)} recipes from cache for user {user_id}")
                
                # Get total count from cache
                total_count = len(cache.recipes_data) if cache.recipes_data else 0
                
                return RecipeListResponse(
                    recipes=cached_recipes,
                    total_count=total_count,
                    limit=limit,
                    offset=offset,
                    from_cache=True
                )
        
        # Cache miss or force refresh - load from database using model
        print(f"Loading recipes from database for user {user_id}...")
        
        all_recipes = Recipe.get_all_with_user_interactions(user_id)
        
        print(f"Retrieved {len(all_recipes)} total recipes from database for user {user_id}")
        
        # Update cache with user-specific data
        cache.update_cache(all_recipes, user_id)
        
        # Return paginated results
        paginated_recipes = all_recipes[offset:offset + limit]
        
        print(f"Returning {len(paginated_recipes)} recipes (page {offset//limit + 1}) for user {user_id}")
        
        return RecipeListResponse(
            recipes=paginated_recipes,
            total_count=len(all_recipes),
            limit=limit,
            offset=offset,
            from_cache=False
        )
        
    except Exception as e:
        print(f"Error getting recipes: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recipes: {str(e)}"
        )
    
@router.post("/{recipe_id}/like")
async def toggle_like_recipe(recipe_id: int, current_user: dict = Depends(verify_token)):
    """Toggle like status on a recipe - optimized with single database transaction"""
    try:
        user_id = current_user['userid']
        
        # Toggle like using model (optimized version with transaction)
        result = Like.toggle_like_with_transaction(user_id, recipe_id)
        
        if "error" in result:
            if result["error"] == "Recipe not found":
                raise HTTPException(status_code=404, detail="Recipe not found")
            else:
                raise HTTPException(status_code=500, detail=result["error"])
        
        # Log the like/unlike event using model
        like_event_data = {
            "previous_state": result["previous_state"],
            "new_state": result["is_liked"],
            "timestamp": datetime.now().isoformat()
        }
        Recipe.log_recipe_event(recipe_id, user_id, result["action_type"], like_event_data)
        
        # Update cache
        cache.update_like_status(recipe_id, user_id, result["is_liked"])
        
        return {"is_liked": result["is_liked"], "recipe_id": recipe_id}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error toggling like: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle like")
        
@router.post("/{recipe_id}/favorite")
async def toggle_favorite_recipe(
    recipe_id: int,
    current_user: dict = Depends(verify_token)
):
    """
    Toggle favorite status - using model methods
    """
    try:
        user_id = current_user['userid']
        print(f"Toggling favorite for recipe {recipe_id} by user {current_user['username']}")
        
        # Check if recipe exists using model
        if not Recipe.recipe_exists(recipe_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )
        
        # Toggle favorite using model
        result = Favorite.toggle_favorite(user_id, recipe_id)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        # Log the favorite/unfavorite event using model
        favorite_event_data = {
            "previous_state": result["previous_state"],
            "new_state": result["is_favorited"],
            "timestamp": datetime.now().isoformat()
        }
        Recipe.log_recipe_event(recipe_id, user_id, result["action_type"], favorite_event_data)
        
        # Update cache efficiently
        cache.update_favorite_status(recipe_id, user_id, result["is_favorited"])
        
        print(f"Recipe {recipe_id} {'favorited' if result['is_favorited'] else 'unfavorited'} - cache updated")
        
        return {"is_favorited": result["is_favorited"], "recipe_id": recipe_id}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error toggling favorite: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle favorite"
        )
    
@router.post("/cache/clear")
async def clear_cache(current_user: dict = Depends(verify_token)):
    """
    Clear the cache manually (admin function)
    """
    user_id = current_user['userid']
    
    # Log cache clear event using model
    cache_event_data = {
        "action": "cache_cleared",
        "timestamp": datetime.now().isoformat(),
        "user_role": "admin"
    }
    Recipe.log_recipe_event(0, user_id, "CacheCleared", cache_event_data)
    
    cache.invalidate()
    return {"message": "Cache cleared successfully"}

@router.get("/user/stats")
async def get_user_stats(current_user: dict = Depends(verify_token)):
    """Get current user's recipe statistics"""
    try:
        user_id = current_user['userid']
        print(f"Getting stats for user: {current_user['username']}")
        
        # Log stats view event using model
        stats_event_data = {
            "stats_requested": ["recipes_created", "total_likes_received", "total_favorites_received", "recipes_liked", "recipes_favorited"],
            "timestamp": datetime.now().isoformat()
        }
        Recipe.log_recipe_event(0, user_id, "ViewedStats", stats_event_data)
        
        # Get comprehensive stats using model
        stats = User.get_comprehensive_user_stats(user_id)
        
        print(f"User stats: {stats}")
        return stats
        
    except Exception as e:
        print(f"Error getting user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )

@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe_by_id(
    recipe_id: int,
    current_user: dict = Depends(verify_token)
):
    """
    Get a specific recipe by ID with user-specific like/favorite status
    """
    try:
        user_id = current_user['userid']
        print(f"Getting recipe {recipe_id} for user: {current_user['username']} (ID: {user_id})")
        
        # Log recipe view event using model
        view_event_data = {
            "viewed_by": current_user['username'],
            "timestamp": datetime.now().isoformat(),
            "access_method": "direct_id"
        }
        Recipe.log_recipe_event(recipe_id, user_id, "Viewed", view_event_data)
        
        # Get recipe with user interactions using model
        recipe_data = Recipe.get_recipe_with_user_interactions(recipe_id, user_id)
        
        if not recipe_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe with ID {recipe_id} not found"
            )
        
        print(f"Retrieved recipe: {recipe_data.get('title', 'Untitled')}")
        
        # Build response
        recipe_response = RecipeResponse(
            recipe_id=recipe_data['recipe_id'],
            title=recipe_data['title'],
            description=recipe_data['description'],
            author_name=recipe_data['author_name'],
            author_id=recipe_data['author_id'],
            image_url=recipe_data['image_url'],
            ingredients=recipe_data['ingredients'],
            instructions=recipe_data['instructions'],
            raw_ingredients=recipe_data['raw_ingredients'],
            servings=recipe_data['servings'],
            created_at=recipe_data['created_at'],
            likes_count=recipe_data['likes_count'],
            is_liked=recipe_data['is_liked'],
            is_favorited=recipe_data['is_favorited']
        )
        
        print(f"Returning recipe details for: {recipe_response.title}")
        return recipe_response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting recipe by ID: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recipe: {str(e)}"
        )