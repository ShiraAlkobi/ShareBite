"""
Add Recipe Routes - Controller Layer for ShareBite backend

This module provides recipe creation endpoints following MVC architecture.
Controllers handle requests and coordinate with models to return responses.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import shutil
import os
from pathlib import Path
import uuid
from pydantic import BaseModel
from datetime import datetime

# Import models
from models.recipe import Recipe
from models.tag import Tag
from models.user import User

# Import auth
from auth_routes import verify_token

router = APIRouter()

# Pydantic models for request/response
class CreateRecipeRequest(BaseModel):
    title: str
    description: Optional[str] = None
    ingredients: str
    instructions: str
    servings: Optional[int] = 4
    image_url: Optional[str] = None
    tags: Optional[List[str]] = []

class RecipeResponse(BaseModel):
    recipe_id: int
    message: str

class TagResponse(BaseModel):
    tag_name: str
    usage_count: Optional[int] = 0

class TagsListResponse(BaseModel):
    tags: List[TagResponse]

@router.post("/recipes/upload-image")
async def upload_recipe_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_token)
):
    """Upload recipe image - NOTE: This endpoint references cloudinary_gateway which needs to be implemented"""
    try:
        user_id = current_user["userid"]
        
        # NOTE: The original code references cloudinary_gateway which is not available
        # This is a placeholder implementation that should be replaced with actual image upload logic
        
        # For now, save locally (this should be replaced with your image upload service)
        upload_dir = Path("static/recipe_images")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Construct URL (adjust based on your server setup)
        image_url = f"/static/recipe_images/{unique_filename}"
        
        # Log image upload event using model
        upload_event_data = {
            "original_filename": file.filename,
            "saved_filename": unique_filename,
            "file_size_bytes": file_path.stat().st_size,
            "file_type": file.content_type,
            "uploaded_by": current_user["username"],
            "upload_method": "local_storage",
            "timestamp": datetime.now().isoformat()
        }
        Recipe.log_recipe_event(0, user_id, "ImageUploaded", upload_event_data)
        
        print(f"Image uploaded successfully (local): {image_url}")
        return {"image_url": image_url}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading image: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")
    
@router.get("/tags", response_model=TagsListResponse)
async def get_all_tags():
    """Get all available tags for recipes - READ ONLY (no event logging)"""
    try:
        # Use model method (replaces CQRS query)
        tags_result = Tag.get_all_with_usage_count(order_by="usage")
        
        tags = []
        for row in tags_result:
            tags.append(TagResponse(
                tag_name=row["TagName"],
                usage_count=row.get("UsageCount", 0)
            ))
        
        return TagsListResponse(tags=tags)
        
    except Exception as e:
        print(f"Error retrieving tags: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving tags: {str(e)}")

@router.get("/tags/search")
async def search_tags(q: str):
    """Search tags by query string - READ ONLY (no event logging)"""
    try:
        if not q or len(q.strip()) < 1:
            # Return popular tags if no query
            return await get_common_tags()
        
        # Use model method (replaces CQRS SearchTagsQuery)
        tags_result = Tag.search_tags(search_term=q, limit=20)
        
        tags = []
        for row in tags_result:
            tags.append({
                "tag_name": row["TagName"],
                "usage_count": row.get("UsageCount", 0)
            })
        
        return {"tags": tags}
        
    except Exception as e:
        print(f"Error searching tags: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching tags: {str(e)}")

@router.get("/tags/common")
async def get_common_tags():
    """Get most commonly used tags - READ ONLY (no event logging)"""
    try:
        # Use model method (replaces CQRS GetPopularTagsQuery)
        tags_result = Tag.get_popular_tags(limit=20, min_usage=1)
        
        tags = []
        if tags_result:
            for row in tags_result:
                tags.append({
                    "tag_name": row["TagName"],
                    "usage_count": row.get("UsageCount", 0)
                })
        else:
            # Fallback to predefined common tags if database is empty
            tags = Tag.get_common_tags_fallback()
        
        return {"tags": tags}
        
    except Exception as e:
        print(f"Error getting common tags: {e}")
        # Return fallback tags using model
        fallback_tags = Tag.get_common_tags_fallback()
        return {"tags": fallback_tags[:5]}  # Return first 5 as emergency fallback

@router.post("/recipes", response_model=RecipeResponse, status_code=201)
async def create_recipe(
    recipe_data: CreateRecipeRequest,
    current_user: dict = Depends(verify_token)
):
    """Create a new recipe - LOGS Created EVENT"""
    try:
        user_id = current_user["userid"]
        print(f"Creating recipe: {recipe_data.title}")
        
        # Use model method (replaces CQRS CreateRecipeCommand)
        recipe_id = Recipe.create_recipe_with_tags(
            author_id=user_id,
            title=recipe_data.title,
            description=recipe_data.description,
            ingredients=recipe_data.ingredients,
            raw_ingredients=recipe_data.ingredients,
            instructions=recipe_data.instructions,
            servings=recipe_data.servings,
            image_url=recipe_data.image_url,
            tags=recipe_data.tags or []
        )
        
        # Log recipe creation event using model
        creation_event_data = {
            "title": recipe_data.title,
            "description_length": len(recipe_data.description or ""),
            "ingredients_length": len(recipe_data.ingredients),
            "instructions_length": len(recipe_data.instructions),
            "servings": recipe_data.servings,
            "has_image": recipe_data.image_url is not None,
            "tags_count": len(recipe_data.tags or []),
            "tags": recipe_data.tags or [],
            "created_by": current_user["username"],
            "timestamp": datetime.now().isoformat()
        }
        Recipe.log_recipe_event(recipe_id, user_id, "Created", creation_event_data)
        
        return RecipeResponse(
            recipe_id=recipe_id,
            message="Recipe created successfully!"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        print(f"Error creating recipe: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating recipe: {str(e)}")

@router.post("/recipes/{recipe_id}/tags")
async def add_tag_to_recipe(
    recipe_id: int,
    tag_name: str = Form(...),
    current_user: dict = Depends(verify_token)
):
    """Add a tag to a recipe - LOGS TagAdded EVENT"""
    try:
        user_id = current_user["userid"]
        
        # Use model method (replaces CQRS AddTagToRecipeCommand)
        success = Recipe.add_tag_to_recipe(
            recipe_id=recipe_id,
            tag_name=tag_name,
            author_id=user_id
        )
        
        if success:
            # Log tag addition event using model
            tag_event_data = {
                "tag_name": tag_name.strip().lower(),
                "recipe_id": recipe_id,
                "added_by": current_user["username"],
                "timestamp": datetime.now().isoformat()
            }
            Recipe.log_recipe_event(recipe_id, user_id, "TagAdded", tag_event_data)
            
            return {"message": f"Tag '{tag_name}' added to recipe"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add tag")
            
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        print(f"Error adding tag: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding tag: {str(e)}")

@router.delete("/recipes/{recipe_id}/tags/{tag_name}")
async def remove_tag_from_recipe(
    recipe_id: int,
    tag_name: str,
    current_user: dict = Depends(verify_token)
):
    """Remove a tag from a recipe - LOGS TagRemoved EVENT"""
    try:
        user_id = current_user["userid"]
        
        # Use model method (replaces CQRS RemoveTagFromRecipeCommand)
        success = Recipe.remove_tag_from_recipe(
            recipe_id=recipe_id,
            tag_name=tag_name,
            author_id=user_id
        )
        
        if success:
            # Log tag removal event using model
            tag_event_data = {
                "tag_name": tag_name.strip().lower(),
                "recipe_id": recipe_id,
                "removed_by": current_user["username"],
                "timestamp": datetime.now().isoformat()
            }
            Recipe.log_recipe_event(recipe_id, user_id, "TagRemoved", tag_event_data)
            
            return {"message": f"Tag '{tag_name}' removed from recipe"}
        else:
            raise HTTPException(status_code=400, detail="Failed to remove tag")
            
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        print(f"Error removing tag: {e}")
        raise HTTPException(status_code=500, detail=f"Error removing tag: {str(e)}")

# Health check for add recipe functionality
@router.get("/add-recipe/health")
async def add_recipe_health():
    """Health check for add recipe functionality - READ ONLY (no event logging)"""
    return {
        "status": "healthy",
        "endpoints": {
            "create_recipe": "POST /api/v1/recipes",
            "upload_image": "POST /api/v1/recipes/upload-image",
            "get_tags": "GET /api/v1/tags",
            "search_tags": "GET /api/v1/tags/search"
        }
    }