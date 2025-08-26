from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from auth_routes import verify_token
from datetime import datetime
from database import execute_query, execute_non_query, execute_scalar, insert_and_get_id
# Import your existing Recipe model directly
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import directly to avoid circular imports
from models.recipe import Recipe
from models.user import User

# Check if SECRET_KEY is consistent
from auth_routes import SECRET_KEY
print(f"Recipe routes using SECRET_KEY: {SECRET_KEY[:10]}...")

router = APIRouter(prefix="/recipes", tags=["Recipes"])

# Pydantic models for API responses
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

def recipe_to_dict(recipe: Recipe, current_user_id: int = None) -> dict:
    """Convert Recipe model instance to dictionary for API response"""
    try:
        # Get author name
        from models.user import User
        author = User.get_by_id(recipe.authorid)
        author_name = author.username if author else "Unknown Chef"
        
        # Get likes count
        from database import execute_scalar
        likes_count = execute_scalar(
            "SELECT COUNT(*) FROM Likes WHERE RecipeID = ?",
            (recipe.recipeid,)
        ) or 0
        
        # Check if current user liked/favorited this recipe
        is_liked = False
        is_favorited = False
        
        if current_user_id:
            is_liked = bool(execute_scalar(
                "SELECT 1 FROM Likes WHERE RecipeID = ? AND UserID = ?",
                (recipe.recipeid, current_user_id)
            ))
            
            is_favorited = bool(execute_scalar(
                "SELECT 1 FROM Favorites WHERE RecipeID = ? AND UserID = ?",
                (recipe.recipeid, current_user_id)
            ))
        
        # Format created_at
        created_at_str = recipe.createdat.isoformat() if recipe.createdat else datetime.now().isoformat()
        
        return {
            "recipe_id": recipe.recipeid,
            "title": recipe.title or "Untitled Recipe",
            "description": recipe.description or "",
            "author_name": author_name,
            "author_id": recipe.authorid,
            "image_url": recipe.imageurl,
            "ingredients": recipe.ingredients,
            "instructions": recipe.instructions,
            "raw_ingredients": recipe.rawingredients,
            "servings": recipe.servings,
            "created_at": created_at_str,
            "likes_count": likes_count,
            "is_liked": is_liked,
            "is_favorited": is_favorited
        }
        
    except Exception as e:
        print(f"❌ Error converting recipe to dict: {e}")
        import traceback
        traceback.print_exc()
        # Return basic recipe info even if some data is missing
        return {
            "recipe_id": getattr(recipe, 'recipeid', 0),
            "title": getattr(recipe, 'title', 'Untitled Recipe'),
            "description": getattr(recipe, 'description', ''),
            "author_name": "Unknown Chef",
            "author_id": getattr(recipe, 'authorid', 0),
            "image_url": getattr(recipe, 'imageurl', None),
            "ingredients": getattr(recipe, 'ingredients', None),
            "instructions": getattr(recipe, 'instructions', None),
            "raw_ingredients": getattr(recipe, 'rawingredients', None),
            "servings": getattr(recipe, 'servings', None),
            "created_at": datetime.now().isoformat(),
            "likes_count": 0,
            "is_liked": False,
            "is_favorited": False
        }

@router.get("/test-auth")
async def test_auth_endpoint(current_user: dict = Depends(verify_token)):
    """
    Simple endpoint to test authentication
    """
    return {
        "message": "Authentication successful!",
        "user": current_user['username'],
        "user_id": current_user['userid']
    }

@router.get("", response_model=RecipeListResponse)
async def get_recipes(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(verify_token)
):
    """
    Get paginated list of recipes using Recipe model
    """
    try:
        print(f"Getting recipes (limit: {limit}, offset: {offset}) for user: {current_user['username']}")
        
        # Use Recipe model's get_all method
        recipes_list = Recipe.get_all(limit=limit, offset=offset)
        
        print(f"Retrieved {len(recipes_list)} recipes from Recipe.get_all()")
        
        # Convert Recipe objects to API response format
        recipes_data = []
        for recipe in recipes_list:
            try:
                recipe_dict = recipe_to_dict(recipe, current_user['userid'])
                recipes_data.append(recipe_dict)
                print(f"Converted recipe: {recipe_dict['title']}")
            except Exception as e:
                print(f"Error converting recipe {getattr(recipe, 'recipeid', 'unknown')}: {e}")
                continue
        
        # Get total count (you might want to add a count method to Recipe model)
        from database import execute_scalar
        total_count = execute_scalar("SELECT COUNT(*) FROM Recipes") or 0
        
        print(f"Returning {len(recipes_data)} recipes, total: {total_count}")
        
        return RecipeListResponse(
            recipes=recipes_data,
            total_count=total_count,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        print(f"Error getting recipes: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recipes: {str(e)}"
        )

@router.get("/search", response_model=RecipeListResponse)
async def search_recipes(
    q: str = Query(..., min_length=1, description="Search query"),
    category: Optional[str] = Query(None, description="Recipe category filter"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(verify_token)
):
    """
    Search recipes by query and optional filters using Recipe model
    """
    try:
        print(f"🔍 Searching recipes: '{q}' category: {category} for user: {current_user['username']}")
        
        # For now, get all recipes and filter in Python
        # TODO: Add search method to Recipe model for better performance
        all_recipes = Recipe.get_all(limit=100)  # Get more recipes for search
        
        # Filter recipes based on search query
        matching_recipes = []
        search_term_lower = q.lower()
        
        for recipe in all_recipes:
            # Search in title, description, and ingredients
            title_match = search_term_lower in (recipe.title or "").lower()
            desc_match = search_term_lower in (recipe.description or "").lower()
            ingredients_match = search_term_lower in (recipe.ingredients or "").lower()
            
            if title_match or desc_match or ingredients_match:
                matching_recipes.append(recipe)
        
        # Apply category filter if provided
        if category and category.lower() not in ["all recipes", "all"]:
            category_filtered = []
            category_lower = category.lower()
            
            for recipe in matching_recipes:
                # Check if category appears in title or description
                title_match = category_lower in (recipe.title or "").lower()
                desc_match = category_lower in (recipe.description or "").lower()
                
                if title_match or desc_match:
                    category_filtered.append(recipe)
            
            matching_recipes = category_filtered
        
        # Apply pagination
        total_count = len(matching_recipes)
        paginated_recipes = matching_recipes[offset:offset + limit]
        
        # Convert to API response format
        recipes_data = []
        for recipe in paginated_recipes:
            try:
                recipe_dict = recipe_to_dict(recipe, current_user['userid'])
                recipes_data.append(recipe_dict)
            except Exception as e:
                print(f"❌ Error converting recipe {getattr(recipe, 'recipeid', 'unknown')}: {e}")
                continue
        
        print(f"✅ Found {len(recipes_data)} recipes matching '{q}' (total: {total_count})")
        
        return RecipeListResponse(
            recipes=recipes_data,
            total_count=total_count,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        print(f"❌ Error searching recipes: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search recipes: {str(e)}"
        )

# Import the CQRS commands and queries at the top of your file
from commands.recipes_commands import ToggleLikeCommand
from queries.recipes_queries import GetRecipeByIdQuery

@router.post("/{recipe_id}/like")
async def toggle_like_recipe(
    recipe_id: int,
    current_user: dict = Depends(verify_token)
):
    """
    Toggle like status for a recipe using CQRS pattern
    """
    try:
        print(f"❤️ Toggling like for recipe {recipe_id} by user {current_user['username']}")
        
        # Use Query to check if recipe exists
        recipe_query = GetRecipeByIdQuery()
        recipe = recipe_query.execute(recipe_id)
        
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )
        
        # Use Command to toggle like (includes all business logic + event logging)
        like_command = ToggleLikeCommand()
        result = like_command.execute(
            user_id=current_user['userid'],
            recipe_id=recipe_id
        )
        
        # The command returns: {"is_liked": bool, "total_likes": int}
        action = "liked" if result["is_liked"] else "unliked"
        print(f"✅ Recipe {recipe_id} {action} by user {current_user['username']}")
        
        return {
            "is_liked": result["is_liked"],
            "recipe_id": recipe_id,
            "total_likes": result["total_likes"]
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        # Command validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"❌ Error toggling like: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle like"
        )

@router.post("/{recipe_id}/favorite")
async def toggle_favorite_recipe(
    recipe_id: int,
    current_user: dict = Depends(verify_token)
):
    """
    Toggle favorite status for a recipe using Recipe model
    """
    try:
        print(f"⭐ Toggling favorite for recipe {recipe_id} by user {current_user['username']}")
        
        # Check if recipe exists using Recipe model
        recipe = Recipe.get_by_id(recipe_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )
        
        # Check if already favorited
        from database import execute_scalar, execute_non_query
        existing_favorite = execute_scalar(
            "SELECT 1 FROM Favorites WHERE RecipeID = ? AND UserID = ?",
            (recipe_id, current_user['userid'])
        )
        
        if existing_favorite:
            # Remove favorite
            execute_non_query(
                "DELETE FROM Favorites WHERE RecipeID = ? AND UserID = ?",
                (recipe_id, current_user['userid'])
            )
            is_favorited = False
            action = "unfavorited"
        else:
            # Add favorite
            execute_non_query(
                "INSERT INTO Favorites (RecipeID, UserID) VALUES (?, ?)",
                (recipe_id, current_user['userid'])
            )
            is_favorited = True
            action = "favorited"
        
        print(f"✅ Recipe {recipe_id} {action} by user {current_user['username']}")
        
        return {"is_favorited": is_favorited, "recipe_id": recipe_id}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error toggling favorite: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle favorite"
        )

@router.get("/user/stats")
async def get_user_stats(current_user: dict = Depends(verify_token)):
    """
    Get current user's recipe statistics
    """
    try:
        print(f"📊 Getting stats for user: {current_user['username']}")
        
        user_id = current_user['userid']
        
        # Get recipes created
        recipes_created = execute_scalar(
            "SELECT COUNT(*) FROM Recipes WHERE AuthorID = ?",
            (user_id,)
        ) or 0
        
        # Get total likes received on user's recipes
        total_likes_received = execute_scalar(
            """SELECT COUNT(*) FROM Likes l
               JOIN Recipes r ON l.RecipeID = r.RecipeID
               WHERE r.AuthorID = ?""",
            (user_id,)
        ) or 0
        
        # Get total favorites received on user's recipes
        total_favorites_received = execute_scalar(
            """SELECT COUNT(*) FROM Favorites f
               JOIN Recipes r ON f.RecipeID = r.RecipeID
               WHERE r.AuthorID = ?""",
            (user_id,)
        ) or 0
        
        # Get recipes liked by user
        recipes_liked = execute_scalar(
            "SELECT COUNT(*) FROM Likes WHERE UserID = ?",
            (user_id,)
        ) or 0
        
        # Get recipes favorited by user
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
        print(f"❌ Error getting user stats: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )