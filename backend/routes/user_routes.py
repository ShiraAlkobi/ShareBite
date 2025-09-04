"""
Profile Routes - Controller Layer for ShareBite backend

This module provides profile endpoints following MVC architecture.
Controllers handle requests and coordinate with models to return responses.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# Import your existing auth verification
from auth_routes import verify_token

# Import models
from models.user import User
from models.recipe import Recipe
from models.like import Like
from models.favorite import Favorite

# Create router
router = APIRouter(prefix="/users", tags=["Profile"])
security = HTTPBearer()

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

# Routes
@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(user_id: int):
    """Get user profile information by ID - READ ONLY (no event logging)"""
    try:
        # Get user data from model
        user_data = User.get_profile_data(user_id)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Get user statistics from model
        stats = User.get_user_stats(user_id)
        
        return UserProfileResponse(
            userid=int(user_data["UserID"]),
            username=str(user_data["Username"]),
            email=str(user_data["Email"]),
            profilepicurl=user_data.get("ProfilePicURL"),
            bio=user_data.get("Bio"),
            createdat=str(user_data.get("CreatedAt")) if user_data.get("CreatedAt") else None,
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
        # Prepare data for model
        update_data = {}
        if profile_data.username is not None:
            update_data['username'] = profile_data.username
        if profile_data.email is not None:
            update_data['email'] = profile_data.email
        if profile_data.bio is not None:
            update_data['bio'] = profile_data.bio
        if profile_data.profile_pic_url is not None:
            update_data['profile_pic_url'] = profile_data.profile_pic_url
        
        # Call model method
        result = User.update_profile(user_id, update_data)
        
        if "error" in result:
            if result["error"] == "Username already taken":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            elif result["error"] == "Email already taken":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )
            elif result["error"] == "No fields to update":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update"
                )
            elif result["error"] == "User not found":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result["error"]
                )
        
        # Log user update event
        update_event_data = {
            "updated_fields": result["updated_fields"],
            "updated_by": current_user["username"],
            "timestamp": datetime.now().isoformat(),
            "has_username_change": "username" in result["updated_fields"],
            "has_email_change": "email" in result["updated_fields"]
        }
        User.log_user_event(user_id, "UserUpdated", update_event_data)
        
        updated_user = result["user"]
        
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
        # Get recipes from model
        result = Recipe.get_user_recipes_with_interactions(
            user_id, current_user["userid"], limit, offset
        )
        
        # Add username to recipes (since it's not available in the model)
        for recipe in result["recipes"]:
            recipe["author_username"] = current_user["username"]
        
        return result
        
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
        # Get favorites from model
        result = Recipe.get_user_favorites_with_interactions(
            user_id, current_user["userid"], limit, offset
        )
        
        return result
        
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
        
        # Check if recipe exists using model
        if not Recipe.recipe_exists(recipe_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )
        
        # Toggle like using model
        result = Like.toggle_like(user_id, recipe_id)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        # Log the like/unlike event
        like_event_data = {
            "previous_state": result["previous_state"],
            "new_state": result["is_liked"],
            "total_likes_after": result["total_likes"],
            "timestamp": datetime.now().isoformat()
        }
        User.log_user_event(user_id, result["action_type"], like_event_data)
        
        return {
            "is_liked": result["is_liked"],
            "total_likes": result["total_likes"]
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
        
        # Log the favorite/unfavorite event
        favorite_event_data = {
            "previous_state": result["previous_state"],
            "new_state": result["is_favorited"],
            "total_favorites_after": result["total_favorites"],
            "timestamp": datetime.now().isoformat()
        }
        User.log_user_event(user_id, result["action_type"], favorite_event_data)
        
        return {
            "is_favorited": result["is_favorited"],
            "total_favorites": result["total_favorites"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error toggling recipe favorite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle recipe favorite"
        )