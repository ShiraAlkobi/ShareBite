from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import shutil
import os
from pathlib import Path
import uuid
from pydantic import BaseModel

# Import your CQRS commands and queries
from commands.recipes_commands import CreateRecipeCommand, AddTagToRecipeCommand, RemoveTagFromRecipeCommand
from queries.recipes_queries import SearchRecipesQuery, GetRecipeByIdQuery
from queries.tags_queries import GetAllTagsQuery, SearchTagsQuery, GetPopularTagsQuery
from database import execute_query, execute_scalar
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
    """Upload a recipe image and return the URL"""
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/bmp"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type. Allowed: JPEG, PNG, GIF, BMP")
        
        # Validate file size (10MB max)
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")
        
        # Create uploads directory if it doesn't exist
        uploads_dir = Path("uploads/recipes")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = uploads_dir / unique_filename
        
        # Save file
        with file_path.open("wb") as buffer:
            buffer.write(file_content)
        
        # Return URL that can be accessed by your app
        image_url = f"/uploads/recipes/{unique_filename}"
        
        print(f"Image uploaded successfully: {image_url}")
        return {"image_url": image_url}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading image: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")
    

@router.get("/tags", response_model=TagsListResponse)
async def get_all_tags():
    """Get all available tags for recipes using your GetAllTagsQuery"""
    try:
        # Use your CQRS query pattern
        query = GetAllTagsQuery()
        tags_result = query.execute(order_by="usage")
        
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
    """Search tags by query string using your SearchTagsQuery"""
    try:
        if not q or len(q.strip()) < 1:
            # Return popular tags if no query
            return await get_common_tags()
        
        # Use your CQRS SearchTagsQuery
        query = SearchTagsQuery()
        tags_result = query.execute(search_term=q, limit=20)
        
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

# # Mock auth dependency - replace with your actual one
# async def get_current_user():
#     """
#     Replace this with your actual authentication dependency
#     Should return user data with user_id
#     """
#     return {"user_id": 1, "username": "test_user"}  # Mock user

@router.get("/tags", response_model=TagsListResponse)
async def get_all_tags():
    """Get all available tags for recipes using your CQRS queries"""
    try:
        # Use direct database query since you don't have a specific tag query yet
        # But this follows your CQRS pattern by keeping queries separate
        tags_query = """
            SELECT t.TagName, COUNT(rt.RecipeID) as usage_count
            FROM Tags t
            LEFT JOIN RecipeTags rt ON t.TagID = rt.TagID
            GROUP BY t.TagID, t.TagName
            ORDER BY usage_count DESC, t.TagName ASC
        """
        
        tags_result = execute_query(tags_query)
        
        tags = []
        if tags_result:
            for row in tags_result:
                tags.append(TagResponse(
                    tag_name=row["TagName"],
                    usage_count=row.get("usage_count", 0)
                ))
        
        return TagsListResponse(tags=tags)
        
    except Exception as e:
        print(f"Error retrieving tags: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving tags: {str(e)}")

@router.get("/tags/search")
async def search_tags(q: str):
    """Search tags by query string using your database pattern"""
    try:
        if not q or len(q.strip()) < 1:
            # Return common tags if no query
            return await get_common_tags()
        
        # Use SearchRecipesQuery pattern but for tags
        search_query = """
            SELECT t.TagName, COUNT(rt.RecipeID) as usage_count
            FROM Tags t
            LEFT JOIN RecipeTags rt ON t.TagID = rt.TagID
            WHERE t.TagName LIKE ?
            GROUP BY t.TagID, t.TagName
            ORDER BY usage_count DESC, t.TagName ASC
            LIMIT 20
        """
        
        tags_result = execute_query(search_query, (f"%{q.lower()}%",))
        
        tags = []
        if tags_result:
            for row in tags_result:
                tags.append({
                    "tag_name": row["TagName"],
                    "usage_count": row.get("usage_count", 0)
                })
        
        return {"tags": tags}
        
    except Exception as e:
        print(f"Error searching tags: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching tags: {str(e)}")

@router.get("/tags/common")
async def get_common_tags():
    """Get most commonly used tags using your GetPopularTagsQuery"""
    try:
        # Use your CQRS GetPopularTagsQuery
        query = GetPopularTagsQuery()
        tags_result = query.execute(limit=20, min_usage=1)
        
        tags = []
        if tags_result:
            for row in tags_result:
                tags.append({
                    "tag_name": row["TagName"],
                    "usage_count": row.get("UsageCount", 0)
                })
        else:
            # Fallback to predefined common tags if database is empty
            common_tags = [
                "vegetarian", "vegan", "gluten-free", "dairy-free", "keto",
                "quick", "easy", "healthy", "comfort-food", "dessert",
                "breakfast", "lunch", "dinner", "snack", "appetizer",
                "main-course", "side-dish", "soup", "salad", "pasta"
            ]
            tags = [{"tag_name": tag, "usage_count": 0} for tag in common_tags]
        
        return {"tags": tags}
        
    except Exception as e:
        print(f"Error getting common tags: {e}")
        # Return fallback tags
        fallback_tags = ["vegetarian", "quick", "easy", "healthy", "dessert"]
        return {"tags": [{"tag_name": tag, "usage_count": 0} for tag in fallback_tags]}

@router.post("/recipes", response_model=RecipeResponse, status_code=201)  # Added status_code=201
async def create_recipe(
    recipe_data: CreateRecipeRequest,
    current_user: dict = Depends(verify_token)
):
    """Create a new recipe using CQRS command"""
    try:
        print(f"Creating recipe: {recipe_data.title}")
        
        # Use your existing CreateRecipeCommand
        command = CreateRecipeCommand()
        
        recipe_id = command.execute(
            author_id=current_user["userid"],
            title=recipe_data.title,
            description=recipe_data.description,
            ingredients=recipe_data.ingredients,
            raw_ingredients=recipe_data.ingredients,
            instructions=recipe_data.instructions,
            servings=recipe_data.servings,
            image_url=recipe_data.image_url,
            tags=recipe_data.tags or []
        )
        
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
    """Add a tag to a recipe"""
    try:
        from commands.recipes_commands import AddTagToRecipeCommand
        
        command = AddTagToRecipeCommand()
        success = command.execute(
            recipe_id=recipe_id,
            tag_name=tag_name,
            author_id=current_user["user_id"]
        )
        
        if success:
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
    """Remove a tag from a recipe"""
    try:
        from commands.recipes_commands import RemoveTagFromRecipeCommand
        
        command = RemoveTagFromRecipeCommand()
        success = command.execute(
            recipe_id=recipe_id,
            tag_name=tag_name,
            author_id=current_user["user_id"]
        )
        
        if success:
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
    """Health check for add recipe functionality"""
    return {
        "status": "healthy",
        "endpoints": {
            "create_recipe": "POST /api/v1/recipes",
            "upload_image": "POST /api/v1/recipes/upload-image",
            "get_tags": "GET /api/v1/tags",
            "search_tags": "GET /api/v1/tags/search"
        }
    }