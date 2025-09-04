"""
Profile Routes - Integrated with existing ShareBite backend

This module provides profile endpoints that work with your existing auth system
and database structure.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

# Import your existing auth verification
from auth_routes import verify_token

# Import your existing database functions
from database import execute_query, execute_non_query, execute_scalar, insert_and_get_id

# Create router
router = APIRouter(prefix="/users", tags=["Profile"])
security = HTTPBearer()

# ============= EVENT SOURCING HELPER =============
def log_user_event(user_id: int, action_type: str, event_data: Dict = None):
    """
    Log a user event to the RecipeEvents table for event sourcing
    Note: We use recipe_id = 0 for user-related events since it's not recipe-specific
    
    Args:
        user_id (int): ID of the user performing the action
        action_type (str): Type of action (UserRegistered, UserUpdated, UserLoggedIn, etc.)
        event_data (Dict): Additional data to store as JSON
    """
    try:
        # Convert event_data to JSON string if provided
        event_data_json = json.dumps(event_data) if event_data else None
        
        # Insert event into RecipeEvents table (using RecipeID = 0 for user events)
        execute_non_query(
            """INSERT INTO RecipeEvents (RecipeID, UserID, ActionType, EventData) 
               VALUES (?, ?, ?, ?)""",
            (0, user_id, action_type, event_data_json)
        )
        
        print(f"📝 User event logged: {action_type} - User {user_id}")
        
    except Exception as e:
        print(f"⚠️ Failed to log user event: {e}")
        # Don't raise exception - event logging failure shouldn't break the main operation

# Pydantic models
class UserProfileResponse(BaseModel):
    userid: int
    username: str
    email: str
    profilepicurl: Optional[str] = None
    bio: Optional[str] = None
    createdat: Optional[str] = None
    recipes_count: int = 0
    total_likes_received: int = 0
    total_favorites_received: int = 0

class RecipeResponse(BaseModel):
    recipe_id: int
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    created_at: Optional[str] = None
    likes_count: int = 0
    favorites_count: int = 0
    author_username: str = ""
    is_liked: bool = False
    is_favorited: bool = False

class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    profile_pic_url: Optional[str] = None

class ToggleResponse(BaseModel):
    is_liked: Optional[bool] = None
    is_favorited: Optional[bool] = None
    total_likes: Optional[int] = None
    total_favorites: Optional[int] = None

# Helper functions
def get_user_stats(user_id: int) -> Dict[str, int]:
    """Get user statistics"""
    try:
        recipes_count = execute_scalar(
            "SELECT COUNT(*) FROM Recipes WHERE AuthorID = ?", 
            (user_id,)
        ) or 0
        
        total_likes = execute_scalar(
            """SELECT COUNT(*) FROM Likes l
               JOIN Recipes r ON l.RecipeID = r.RecipeID
               WHERE r.AuthorID = ?""",
            (user_id,)
        ) or 0
        
        total_favorites = execute_scalar(
            """SELECT COUNT(*) FROM Favorites f
               JOIN Recipes r ON f.RecipeID = r.RecipeID
               WHERE r.AuthorID = ?""",
            (user_id,)
        ) or 0
        
        return {
            "recipes_count": recipes_count,
            "total_likes_received": total_likes,
            "total_favorites_received": total_favorites
        }
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return {
            "recipes_count": 0,
            "total_likes_received": 0,
            "total_favorites_received": 0
        }

def get_user_interactions(user_id: int, recipe_ids: List[int]) -> Dict[int, Dict[str, bool]]:
    """Check user's likes/favorites for given recipes"""
    if not recipe_ids:
        return {}
    
    try:
        # Get likes
        placeholders = ",".join(["?" for _ in recipe_ids])
        likes_query = f"""
            SELECT RecipeID FROM Likes 
            WHERE UserID = ? AND RecipeID IN ({placeholders})
        """
        
        liked_recipes = execute_query(likes_query, [user_id] + recipe_ids)
        liked_ids = {row['RecipeID'] for row in liked_recipes}
        
        # Get favorites
        favorites_query = f"""
            SELECT RecipeID FROM Favorites 
            WHERE UserID = ? AND RecipeID IN ({placeholders})
        """
        
        favorited_recipes = execute_query(favorites_query, [user_id] + recipe_ids)
        favorited_ids = {row['RecipeID'] for row in favorited_recipes}
        
        # Build result
        result = {}
        for recipe_id in recipe_ids:
            result[recipe_id] = {
                "is_liked": recipe_id in liked_ids,
                "is_favorited": recipe_id in favorited_ids
            }
        
        return result
        
    except Exception as e:
        print(f"Error getting user interactions: {e}")
        return {recipe_id: {"is_liked": False, "is_favorited": False} for recipe_id in recipe_ids}

# Routes
@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(user_id: int):
    """Get user profile information by ID - READ ONLY (no event logging)"""
    try:
        # Get user data
        user_data = execute_query(
            """SELECT UserID, Username, Email, ProfilePicURL, Bio, CreatedAt
               FROM Users WHERE UserID = ?""",
            (user_id,),
            fetch="one"
        )
        
        if not user_data or len(user_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        user = user_data[0]
        
        # Get user statistics
        stats = get_user_stats(user_id)
        
        return UserProfileResponse(
            userid=int(user["UserID"]),
            username=str(user["Username"]),
            email=str(user["Email"]),
            profilepicurl=user.get("ProfilePicURL"),
            bio=user.get("Bio"),
            createdat=str(user.get("CreatedAt")) if user.get("CreatedAt") else None,
            recipes_count=stats["recipes_count"],
            total_likes_received=stats["total_likes_received"],
            total_favorites_received=stats["total_favorites_received"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )

@router.put("/{user_id}")
async def update_user_profile(
    user_id: int,
    profile_data: UpdateProfileRequest,
    current_user: dict = Depends(verify_token)
):
    """Update user profile information - LOGS UserUpdated EVENT"""
    # Check if user is updating their own profile
    if current_user["userid"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    
    try:
        # Build dynamic update query
        update_fields = []
        params = []
        updated_field_names = []
        
        if profile_data.username is not None:
            # Check username uniqueness
            existing = execute_scalar(
                "SELECT COUNT(*) FROM Users WHERE Username = ? AND UserID != ?",
                (profile_data.username, user_id)
            )
            if existing and existing > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            update_fields.append("Username = ?")
            params.append(profile_data.username)
            updated_field_names.append("username")
        
        if profile_data.email is not None:
            # Check email uniqueness
            existing = execute_scalar(
                "SELECT COUNT(*) FROM Users WHERE Email = ? AND UserID != ?",
                (str(profile_data.email), user_id)
            )
            if existing and existing > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )
            update_fields.append("Email = ?")
            params.append(str(profile_data.email))
            updated_field_names.append("email")
        
        if profile_data.bio is not None:
            update_fields.append("Bio = ?")
            params.append(profile_data.bio)
            updated_field_names.append("bio")
        
        if profile_data.profile_pic_url is not None:
            update_fields.append("ProfilePicURL = ?")
            params.append(profile_data.profile_pic_url)
            updated_field_names.append("profile_pic_url")
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Execute update
        query = f"UPDATE Users SET {', '.join(update_fields)} WHERE UserID = ?"
        params.append(user_id)
        
        rows_affected = execute_non_query(query, tuple(params))
        
        if rows_affected == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Log user update event
        update_event_data = {
            "updated_fields": updated_field_names,
            "updated_by": current_user["username"],
            "timestamp": datetime.now().isoformat(),
            "has_username_change": "username" in updated_field_names,
            "has_email_change": "email" in updated_field_names
        }
        log_user_event(user_id, "UserUpdated", update_event_data)
        
        # Get updated user data
        updated_user = execute_query(
            """SELECT UserID, Username, Email, ProfilePicURL, Bio, CreatedAt
               FROM Users WHERE UserID = ?""",
            (user_id,),
            fetch="one"
        )[0]
        
        return {
            "message": "Profile updated successfully",
            "user": {
                "userid": int(updated_user["UserID"]),
                "username": str(updated_user["Username"]),
                "email": str(updated_user["Email"]),
                "profilepicurl": updated_user.get("ProfilePicURL"),
                "bio": updated_user.get("Bio"),
                "createdat": str(updated_user.get("CreatedAt")) if updated_user.get("CreatedAt") else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

@router.get("/{user_id}/recipes")
async def get_user_recipes(
    user_id: int,
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(verify_token)
):
    """Get recipes created by the user - READ ONLY (no event logging)"""
    try:
        # Get user's recipes with engagement counts
        recipes_query = """
            SELECT 
                r.RecipeID,
                r.Title,
                r.Description,
                r.ImageURL,
                r.CreatedAt,
                (SELECT COUNT(*) FROM Likes l WHERE l.RecipeID = r.RecipeID) as LikesCount,
                (SELECT COUNT(*) FROM Favorites f WHERE f.RecipeID = r.RecipeID) as FavoritesCount
            FROM Recipes r
            WHERE r.AuthorID = ?
            ORDER BY r.CreatedAt DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        
        recipes_data = execute_query(recipes_query, (user_id, offset, limit))
        
        # Get user interactions for these recipes
        recipe_ids = [recipe["RecipeID"] for recipe in recipes_data]
        interactions = get_user_interactions(current_user["userid"], recipe_ids)
        
        # Format response
        recipes = []
        for recipe in recipes_data:
            recipe_id = recipe["RecipeID"]
            user_interaction = interactions.get(recipe_id, {"is_liked": False, "is_favorited": False})
            
            recipes.append({
                "recipe_id": recipe_id,
                "title": recipe["Title"],
                "description": recipe.get("Description"),
                "image_url": recipe.get("ImageURL"),
                "created_at": str(recipe.get("CreatedAt")) if recipe.get("CreatedAt") else None,
                "likes_count": recipe.get("LikesCount", 0),
                "favorites_count": recipe.get("FavoritesCount", 0),
                "author_username": current_user["username"],
                "is_liked": user_interaction["is_liked"],
                "is_favorited": user_interaction["is_favorited"]
            })
        
        return {
            "recipes": recipes,
            "total_count": len(recipes),
            "has_more": len(recipes) == limit
        }
        
    except Exception as e:
        print(f"Error getting user recipes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user recipes"
        )

@router.get("/{user_id}/favorites")
async def get_user_favorites(
    user_id: int,
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(verify_token)
):
    """Get recipes favorited by the user - READ ONLY (no event logging)"""
    try:
        favorites_query = """
            SELECT 
                r.RecipeID,
                r.Title,
                r.Description,
                r.ImageURL,
                r.CreatedAt,
                u.Username as AuthorUsername,
                f.CreatedAt as FavoritedAt,
                (SELECT COUNT(*) FROM Likes l WHERE l.RecipeID = r.RecipeID) as LikesCount,
                (SELECT COUNT(*) FROM Favorites ff WHERE ff.RecipeID = r.RecipeID) as FavoritesCount
            FROM Favorites f
            JOIN Recipes r ON f.RecipeID = r.RecipeID
            JOIN Users u ON r.AuthorID = u.UserID
            WHERE f.UserID = ?
            ORDER BY f.CreatedAt DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        
        favorites_data = execute_query(favorites_query, (user_id, offset, limit))
        
        # Get user interactions (likes) for these recipes
        recipe_ids = [recipe["RecipeID"] for recipe in favorites_data]
        interactions = get_user_interactions(current_user["userid"], recipe_ids)
        
        # Format response
        recipes = []
        for recipe in favorites_data:
            recipe_id = recipe["RecipeID"]
            user_interaction = interactions.get(recipe_id, {"is_liked": False, "is_favorited": True})
            
            recipes.append({
                "recipe_id": recipe_id,
                "title": recipe["Title"],
                "description": recipe.get("Description"),
                "image_url": recipe.get("ImageURL"),
                "created_at": str(recipe.get("CreatedAt")) if recipe.get("CreatedAt") else None,
                "likes_count": recipe.get("LikesCount", 0),
                "favorites_count": recipe.get("FavoritesCount", 0),
                "author_username": recipe.get("AuthorUsername", ""),
                "is_liked": user_interaction["is_liked"],
                "is_favorited": True  # Always true for favorites
            })
        
        return {
            "recipes": recipes,
            "total_count": len(recipes),
            "has_more": len(recipes) == limit
        }
        
    except Exception as e:
        print(f"Error getting user favorites: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user favorites"
        )

# Recipe interaction endpoints
@router.post("/recipes/{recipe_id}/toggle-like")
async def toggle_recipe_like(
    recipe_id: int,
    current_user: dict = Depends(verify_token)
):
    """Toggle like status on a recipe - LOGS Liked/Unliked EVENTS"""
    try:
        user_id = current_user["userid"]
        
        # Check if recipe exists
        recipe_exists = execute_scalar(
            "SELECT COUNT(*) FROM Recipes WHERE RecipeID = ?",
            (recipe_id,)
        )
        
        if not recipe_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )
        
        # Check current like status
        is_liked = execute_scalar(
            "SELECT COUNT(*) FROM Likes WHERE UserID = ? AND RecipeID = ?",
            (user_id, recipe_id)
        ) > 0
        
        if is_liked:
            # Remove like
            execute_non_query(
                "DELETE FROM Likes WHERE UserID = ? AND RecipeID = ?",
                (user_id, recipe_id)
            )
            new_status = False
            action_type = "Unliked"
        else:
            # Add like
            execute_non_query(
                "INSERT INTO Likes (UserID, RecipeID) VALUES (?, ?)",
                (user_id, recipe_id)
            )
            new_status = True
            action_type = "Liked"
        
        # Get updated total likes
        total_likes = execute_scalar(
            "SELECT COUNT(*) FROM Likes WHERE RecipeID = ?",
            (recipe_id,)
        ) or 0
        
        # Log the like/unlike event
        like_event_data = {
            "previous_state": is_liked,
            "new_state": new_status,
            "total_likes_after": total_likes,
            "timestamp": datetime.now().isoformat()
        }
        log_user_event(user_id, action_type, like_event_data)
        
        return {
            "is_liked": new_status,
            "total_likes": total_likes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error toggling recipe like: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle recipe like"
        )

@router.post("/recipes/{recipe_id}/toggle-favorite")
async def toggle_recipe_favorite(
    recipe_id: int,
    current_user: dict = Depends(verify_token)
):
    """Toggle favorite status on a recipe - LOGS Favorited/Unfavorited EVENTS"""
    try:
        user_id = current_user["userid"]
        
        # Check if recipe exists
        recipe_exists = execute_scalar(
            "SELECT COUNT(*) FROM Recipes WHERE RecipeID = ?",
            (recipe_id,)
        )
        
        if not recipe_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )
        
        # Check current favorite status
        is_favorited = execute_scalar(
            "SELECT COUNT(*) FROM Favorites WHERE UserID = ? AND RecipeID = ?",
            (user_id, recipe_id)
        ) > 0
        
        if is_favorited:
            # Remove favorite
            execute_non_query(
                "DELETE FROM Favorites WHERE UserID = ? AND RecipeID = ?",
                (user_id, recipe_id)
            )
            new_status = False
            action_type = "Unfavorited"
        else:
            # Add favorite
            execute_non_query(
                "INSERT INTO Favorites (UserID, RecipeID) VALUES (?, ?)",
                (user_id, recipe_id)
            )
            new_status = True
            action_type = "Favorited"
        
        # Get updated total favorites
        total_favorites = execute_scalar(
            "SELECT COUNT(*) FROM Favorites WHERE RecipeID = ?",
            (recipe_id,)
        ) or 0
        
        # Log the favorite/unfavorite event
        favorite_event_data = {
            "previous_state": is_favorited,
            "new_state": new_status,
            "total_favorites_after": total_favorites,
            "timestamp": datetime.now().isoformat()
        }
        log_user_event(user_id, action_type, favorite_event_data)
        
        return {
            "is_favorited": new_status,
            "total_favorites": total_favorites
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error toggling recipe favorite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle recipe favorite"
        )