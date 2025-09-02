from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from routes.auth_routes import verify_token
from datetime import datetime, timedelta
from database import execute_query, execute_non_query, execute_scalar, insert_and_get_id , get_database_cursor
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.recipe import Recipe
from models.user import User

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

# יצירת מטמון גלובלי
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
    from_cache: bool = False  # נוסיף אינדיקציה אם הנתונים מהמטמון

# ============= ENDPOINTS =============
# IMPORTANT: Add this route BEFORE the /{recipe_id} route in your recipe_routes.py file
# FastAPI matches routes in order, so more specific paths must come before parameterized ones

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
        
        # Build search query with user-specific like/favorite status
        base_query = """
        SELECT 
            r.RecipeID,
            r.Title,
            r.Description,
            r.Ingredients,
            r.Instructions,
            r.ImageURL,
            r.RawIngredients,
            r.Servings,
            r.CreatedAt,
            r.AuthorID,
            u.Username as AuthorName,
            (SELECT COUNT(*) FROM Likes WHERE RecipeID = r.RecipeID) as LikesCount,
            CASE WHEN EXISTS(SELECT 1 FROM Likes WHERE RecipeID = r.RecipeID AND UserID = ?) 
                 THEN 1 ELSE 0 END as IsLiked,
            CASE WHEN EXISTS(SELECT 1 FROM Favorites WHERE RecipeID = r.RecipeID AND UserID = ?) 
                 THEN 1 ELSE 0 END as IsFavorited
        FROM Recipes r
        JOIN Users u ON r.AuthorID = u.UserID
        WHERE 1=1
        """
        
        # Build WHERE conditions and parameters
        conditions = []
        params = [user_id, user_id]  # For the IsLiked and IsFavorited subqueries
        
        # Search in multiple fields - Enhanced for multi-word queries
        if q and q.strip():
            search_query = q.strip()
            search_terms = search_query.split()
            
            print(f"Search terms: {search_terms}")
            print(f"Original query: '{search_query}'")
            
            if len(search_terms) == 1:
                # Single word search - use original logic
                search_condition = """
                (LOWER(r.Title) LIKE LOWER(?) 
                 OR LOWER(r.Description) LIKE LOWER(?) 
                 OR LOWER(r.Ingredients) LIKE LOWER(?) 
                 OR LOWER(r.RawIngredients) LIKE LOWER(?))
                """
                search_term = f"%{search_query}%"
                conditions.append(search_condition)
                params.extend([search_term, search_term, search_term, search_term])
                print(f"Single word search with term: '{search_term}'")
                
            else:
                # Multi-word search - each word must appear somewhere in the record
                word_conditions = []
                for term in search_terms:
                    word_condition = """
                    (LOWER(r.Title) LIKE LOWER(?) 
                     OR LOWER(r.Description) LIKE LOWER(?) 
                     OR LOWER(r.Ingredients) LIKE LOWER(?) 
                     OR LOWER(r.RawIngredients) LIKE LOWER(?))
                    """
                    word_conditions.append(word_condition)
                    word_term = f"%{term}%"
                    params.extend([word_term, word_term, word_term, word_term])
                
                # All words must be found (AND logic)
                multi_word_condition = "(" + " AND ".join(word_conditions) + ")"
                conditions.append(multi_word_condition)
                print(f"Multi-word search with {len(search_terms)} terms, added {len(search_terms) * 4} parameters")
        
        # Category filter (if provided)
        if category and category.lower() != "all":
            # Assuming you have a category field or want to search in description/title for category
            # You might want to add a Category column to your Recipes table for better filtering
            category_condition = """
            (LOWER(r.Title) LIKE LOWER(?) 
             OR LOWER(r.Description) LIKE LOWER(?))
            """
            conditions.append(category_condition)
            category_term = f"%{category.strip()}%"
            params.extend([category_term, category_term])
        
        # Author filter (if provided)
        if author and author.strip():
            conditions.append("LOWER(u.Username) LIKE LOWER(?)")
            params.append(f"%{author.strip()}%")
        
        # Combine all conditions
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        # Add ordering and pagination (SQL Server syntax)
        base_query += """
        ORDER BY r.CreatedAt DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        params.extend([offset, limit])
        
        print(f"Executing search query with {len(params)} parameters")
        print(f"Original search query: '{q}'")
        print(f"Full query: {base_query}")
        print(f"Parameters: {params}")
        
        # Execute search query
        search_results = execute_query(base_query, tuple(params))
        
        print(f"Found {len(search_results)} recipes matching search criteria")
        
        # Convert results to API format
        recipes = []
        for row in search_results:
            try:
                # Format created_at
                created_at_str = datetime.now().isoformat()
                if row.get('CreatedAt'):
                    if isinstance(row['CreatedAt'], str):
                        created_at_str = row['CreatedAt']
                    else:
                        try:
                            created_at_str = row['CreatedAt'].isoformat()
                        except:
                            created_at_str = str(row['CreatedAt'])
                
                recipe_dict = {
                    "recipe_id": row['RecipeID'],
                    "title": row.get('Title') or "Untitled Recipe",
                    "description": row.get('Description') or "",
                    "author_name": row.get('AuthorName') or "Unknown Chef",
                    "author_id": row['AuthorID'],
                    "image_url": row.get('ImageURL'),
                    "ingredients": row.get('Ingredients'),
                    "instructions": row.get('Instructions'),
                    "raw_ingredients": row.get('RawIngredients'),
                    "servings": row.get('Servings'),
                    "created_at": created_at_str,
                    "likes_count": row.get('LikesCount') or 0,
                    "is_liked": bool(row.get('IsLiked')),
                    "is_favorited": bool(row.get('IsFavorited'))
                }
                recipes.append(recipe_dict)
                
            except Exception as e:
                print(f"Error processing search result row: {e}")
                continue
        
        # Build separate count query without user-specific fields to avoid parameter mismatch
        count_base_query = """
        SELECT COUNT(*)
        FROM Recipes r
        JOIN Users u ON r.AuthorID = u.UserID
        WHERE 1=1
        """
        
        # Add the same conditions as the main query but without user-specific parameters
        count_conditions = []
        count_params = []
        
        # Search in multiple fields - Enhanced count query logic
        if q and q.strip():
            # Split search terms for better matching (same logic as main query)
            search_terms = q.strip().split()
            
            if len(search_terms) == 1:
                # Single word search
                search_condition = """
                (LOWER(r.Title) LIKE LOWER(?) 
                 OR LOWER(r.Description) LIKE LOWER(?) 
                 OR LOWER(r.Ingredients) LIKE LOWER(?) 
                 OR LOWER(r.RawIngredients) LIKE LOWER(?))
                """
                count_conditions.append(search_condition)
                search_term = f"%{q.strip()}%"
                count_params.extend([search_term, search_term, search_term, search_term])
                
            else:
                # Multi-word search - each word must appear somewhere
                word_conditions = []
                for term in search_terms:
                    word_condition = """
                    (LOWER(r.Title) LIKE LOWER(?) 
                     OR LOWER(r.Description) LIKE LOWER(?) 
                     OR LOWER(r.Ingredients) LIKE LOWER(?) 
                     OR LOWER(r.RawIngredients) LIKE LOWER(?))
                    """
                    word_conditions.append(word_condition)
                    word_term = f"%{term}%"
                    count_params.extend([word_term, word_term, word_term, word_term])
                
                # All words must be found (AND logic)
                multi_word_condition = "(" + " AND ".join(word_conditions) + ")"
                count_conditions.append(multi_word_condition)
        
        # Category filter (if provided)
        if category and category.lower() != "all":
            category_condition = """
            (LOWER(r.Title) LIKE LOWER(?) 
             OR LOWER(r.Description) LIKE LOWER(?))
            """
            count_conditions.append(category_condition)
            category_term = f"%{category.strip()}%"
            count_params.extend([category_term, category_term])
        
        # Author filter (if provided)
        if author and author.strip():
            count_conditions.append("LOWER(u.Username) LIKE LOWER(?)")
            count_params.append(f"%{author.strip()}%")
        
        # Combine count conditions
        if count_conditions:
            count_base_query += " AND " + " AND ".join(count_conditions)
        
        total_count = execute_scalar(count_base_query, tuple(count_params)) or 0
        
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
        
        # Cache miss or force refresh - load from database
        print(f"Loading recipes from database for user {user_id}...")
        
        # Enhanced query that gets user-specific like/favorite status
        query = """
        SELECT 
            r.RecipeID,
            r.Title,
            r.Description,
            r.Ingredients,
            r.Instructions,
            r.ImageURL,
            r.RawIngredients,
            r.Servings,
            r.CreatedAt,
            r.AuthorID,
            u.Username as AuthorName,
            (SELECT COUNT(*) FROM Likes WHERE RecipeID = r.RecipeID) as LikesCount,
            CASE WHEN EXISTS(SELECT 1 FROM Likes WHERE RecipeID = r.RecipeID AND UserID = ?) 
                 THEN 1 ELSE 0 END as IsLiked,
            CASE WHEN EXISTS(SELECT 1 FROM Favorites WHERE RecipeID = r.RecipeID AND UserID = ?) 
                 THEN 1 ELSE 0 END as IsFavorited
        FROM Recipes r
        JOIN Users u ON r.AuthorID = u.UserID
        ORDER BY r.CreatedAt DESC
        """
        
        # Load all recipes with user-specific data
        all_recipes_data = execute_query(query, (user_id, user_id))
        
        print(f"Retrieved {len(all_recipes_data)} total recipes from database for user {user_id}")
        
        # Convert to API format
        all_recipes = []
        for row in all_recipes_data:
            try:
                created_at_str = datetime.now().isoformat()
                if row.get('CreatedAt'):
                    if isinstance(row['CreatedAt'], str):
                        created_at_str = row['CreatedAt']
                    else:
                        try:
                            created_at_str = row['CreatedAt'].isoformat()
                        except:
                            created_at_str = str(row['CreatedAt'])
                
                recipe_dict = {
                    "recipe_id": row['RecipeID'],
                    "title": row.get('Title') or "Untitled Recipe",
                    "description": row.get('Description') or "",
                    "author_name": row.get('AuthorName') or "Unknown Chef",
                    "author_id": row['AuthorID'],
                    "image_url": row.get('ImageURL'),
                    "ingredients": row.get('Ingredients'),
                    "instructions": row.get('Instructions'),
                    "raw_ingredients": row.get('RawIngredients'),
                    "servings": row.get('Servings'),
                    "created_at": created_at_str,
                    "likes_count": row.get('LikesCount') or 0,
                    "is_liked": bool(row.get('IsLiked')),
                    "is_favorited": bool(row.get('IsFavorited'))
                }
                all_recipes.append(recipe_dict)
                
            except Exception as e:
                print(f"Error processing recipe row: {e}")
                continue
        
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
    try:
        user_id = current_user['userid']
        
        # Single transaction that checks recipe existence and toggles like
        with get_database_cursor() as cursor:
            # Check if recipe exists and current like status
            cursor.execute("""
                SELECT COUNT(*) as recipe_exists,
                       CASE WHEN EXISTS(SELECT 1 FROM Likes WHERE RecipeID = ? AND UserID = ?) 
                            THEN 1 ELSE 0 END as is_liked
                FROM Recipes 
                WHERE RecipeID = ?
            """, (recipe_id, user_id, recipe_id))
            
            result = cursor.fetchone()
            
            if not result or result.recipe_exists == 0:
                raise HTTPException(status_code=404, detail="Recipe not found")
            
            is_currently_liked = bool(result.is_liked)
            
            # Toggle like in same transaction
            if is_currently_liked:
                cursor.execute("DELETE FROM Likes WHERE RecipeID = ? AND UserID = ?", 
                              (recipe_id, user_id))
                is_liked = False
            else:
                cursor.execute("INSERT INTO Likes (RecipeID, UserID) VALUES (?, ?)", 
                              (recipe_id, user_id))
                is_liked = True
        
        # Update cache
        cache.update_like_status(recipe_id, user_id, is_liked)
        
        return {"is_liked": is_liked, "recipe_id": recipe_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to toggle like")
        
@router.post("/{recipe_id}/favorite")
async def toggle_favorite_recipe(
    recipe_id: int,
    current_user: dict = Depends(verify_token)
):
    """
    Toggle favorite status - optimized with single database transaction
    """
    try:
        user_id = current_user['userid']
        print(f"Toggling favorite for recipe {recipe_id} by user {current_user['username']}")
        
        # Use single database connection for entire operation
        with get_database_cursor() as cursor:
            # Check if recipe exists and get current favorite status in one query
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM Recipes WHERE RecipeID = ?) as recipe_exists,
                    CASE WHEN EXISTS(SELECT 1 FROM Favorites WHERE RecipeID = ? AND UserID = ?) 
                         THEN 1 ELSE 0 END as is_currently_favorited
            """, (recipe_id, recipe_id, user_id))
            
            result = cursor.fetchone()
            
            # Check if recipe exists
            if not result or result[0] == 0:  # recipe_exists is first column
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Recipe not found"
                )
            
            is_currently_favorited = bool(result[1])  # is_currently_favorited is second column
            
            # Toggle favorite status in same transaction
            if is_currently_favorited:
                # Remove favorite
                cursor.execute(
                    "DELETE FROM Favorites WHERE RecipeID = ? AND UserID = ?",
                    (recipe_id, user_id)
                )
                is_favorited = False
                print(f"Removed favorite for recipe {recipe_id}")
            else:
                # Add favorite
                cursor.execute(
                    "INSERT INTO Favorites (RecipeID, UserID) VALUES (?, ?)",
                    (recipe_id, user_id)
                )
                is_favorited = True
                print(f"Added favorite for recipe {recipe_id}")
            
            # Transaction automatically commits when exiting the 'with' block
        
        # Update cache efficiently
        cache.update_favorite_status(recipe_id, user_id, is_favorited)
        
        print(f"Recipe {recipe_id} {'favorited' if is_favorited else 'unfavorited'} - cache updated")
        
        return {"is_favorited": is_favorited, "recipe_id": recipe_id}
        
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
    cache.invalidate()
    return {"message": "Cache cleared successfully"}

# שאר הפונקציות נשארות כמו שהן...
@router.get("/user/stats")
async def get_user_stats(current_user: dict = Depends(verify_token)):
    """Get current user's recipe statistics"""
    try:
        print(f"📊 Getting stats for user: {current_user['username']}")
        
        user_id = current_user['userid']
        
        recipes_created = execute_scalar(
            "SELECT COUNT(*) FROM Recipes WHERE AuthorID = ?",
            (user_id,)
        ) or 0
        
        total_likes_received = execute_scalar(
            """SELECT COUNT(*) FROM Likes l
               JOIN Recipes r ON l.RecipeID = r.RecipeID
               WHERE r.AuthorID = ?""",
            (user_id,)
        ) or 0
        
        total_favorites_received = execute_scalar(
            """SELECT COUNT(*) FROM Favorites f
               JOIN Recipes r ON f.RecipeID = r.RecipeID
               WHERE r.AuthorID = ?""",
            (user_id,)
        ) or 0
        
        recipes_liked = execute_scalar(
            "SELECT COUNT(*) FROM Likes WHERE UserID = ?",
            (user_id,)
        ) or 0
        
        recipes_favorited = execute_scalar(
            "SELECT COUNT(*) FROM Favorites WHERE UserID = ?",
            (user_id,)
        ) or 0
        
        stats = {
            "recipes_created": recipes_created,
            "total_likes_received": total_likes_received,
            "total_favorites_received": total_favorites_received,
            "recipes_liked": recipes_liked,
            "recipes_favorited": recipes_favorited
        }
        
        print(f"✅ User stats: {stats}")
        return stats
        
    except Exception as e:
        print(f"Error getting user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )
    # Add this to your recipe_routes.py file

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
        
        # Query to get recipe with user-specific like/favorite status
        query = """
        SELECT 
            r.RecipeID,
            r.Title,
            r.Description,
            r.Ingredients,
            r.Instructions,
            r.ImageURL,
            r.RawIngredients,
            r.Servings,
            r.CreatedAt,
            r.AuthorID,
            u.Username as AuthorName,
            (SELECT COUNT(*) FROM Likes WHERE RecipeID = r.RecipeID) as LikesCount,
            CASE WHEN EXISTS(SELECT 1 FROM Likes WHERE RecipeID = r.RecipeID AND UserID = ?) 
                 THEN 1 ELSE 0 END as IsLiked,
            CASE WHEN EXISTS(SELECT 1 FROM Favorites WHERE RecipeID = r.RecipeID AND UserID = ?) 
                 THEN 1 ELSE 0 END as IsFavorited
        FROM Recipes r
        JOIN Users u ON r.AuthorID = u.UserID
        WHERE r.RecipeID = ?
        """
        
        # Execute query
        recipe_data = execute_query(query, (user_id, user_id, recipe_id), fetch="one")
        
        if not recipe_data or len(recipe_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe with ID {recipe_id} not found"
            )
        
        # Get the first (and only) result
        row = recipe_data[0]
        
        print(f"Retrieved recipe: {row.get('Title', 'Untitled')}")
        
        # Format created_at
        created_at_str = datetime.now().isoformat()
        if row.get('CreatedAt'):
            if isinstance(row['CreatedAt'], str):
                created_at_str = row['CreatedAt']
            else:
                try:
                    created_at_str = row['CreatedAt'].isoformat()
                except:
                    created_at_str = str(row['CreatedAt'])
        
        # Build response
        recipe_response = RecipeResponse(
            recipe_id=row['RecipeID'],
            title=row.get('Title') or "Untitled Recipe",
            description=row.get('Description') or "",
            author_name=row.get('AuthorName') or "Unknown Chef",
            author_id=row['AuthorID'],
            image_url=row.get('ImageURL'),
            ingredients=row.get('Ingredients'),
            instructions=row.get('Instructions'),
            raw_ingredients=row.get('RawIngredients'),
            servings=row.get('Servings'),
            created_at=created_at_str,
            likes_count=row.get('LikesCount') or 0,
            is_liked=bool(row.get('IsLiked')),
            is_favorited=bool(row.get('IsFavorited'))
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
    
