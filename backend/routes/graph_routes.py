from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Dict, Any
from routes.auth_routes import verify_token
from database import execute_query, execute_scalar
from datetime import datetime

router = APIRouter(prefix="/analytics", tags=["Analytics"])

class TagAnalyticsData(BaseModel):
    tag_name: str
    recipe_count: int
    percentage: float

class RecipePopularityData(BaseModel):
    recipe_id: int
    title: str
    author_name: str
    likes_count: int

class AnalyticsResponse(BaseModel):
    tag_distribution: List[TagAnalyticsData]
    popular_recipes: List[RecipePopularityData]
    total_recipes: int
    total_tags: int

@router.get("/user/{user_id}", response_model=AnalyticsResponse)
async def get_user_analytics(
    user_id: int,
    current_user: dict = Depends(verify_token)
):
    """
    Get analytics data for a specific user including:
    1. Recipe distribution by tags (top 10 + others)
    2. Most popular recipes by likes count (top 10)
    """
    try:
        # Verify user can access this data (either their own or public analytics)
        if current_user["userid"] != user_id:
            # For now, allow access to other users' analytics
            # You could add privacy controls here
            pass
        
        print(f"Getting analytics for user: {user_id}")
        
        # Get tag distribution for user's recipes
        tag_query = """
        SELECT 
            t.TagName,
            COUNT(rt.RecipeID) as RecipeCount
        FROM Tags t
        JOIN RecipeTags rt ON t.TagID = rt.TagID
        JOIN Recipes r ON rt.RecipeID = r.RecipeID
        WHERE r.AuthorID = ?
        GROUP BY t.TagID, t.TagName
        ORDER BY COUNT(rt.RecipeID) DESC
        """
        
        tag_results = execute_query(tag_query, (user_id,))
        
        # Calculate total recipes for percentage calculation
        total_recipes_with_tags = sum(row["RecipeCount"] for row in tag_results)
        
        # Process tag distribution (top 10 + others)
        tag_distribution = []
        other_count = 0
        
        for i, row in enumerate(tag_results):
            if i < 10:  # Top 10 tags
                percentage = (row["RecipeCount"] / total_recipes_with_tags * 100) if total_recipes_with_tags > 0 else 0
                tag_distribution.append(TagAnalyticsData(
                    tag_name=row["TagName"],
                    recipe_count=row["RecipeCount"],
                    percentage=round(percentage, 1)
                ))
            else:  # Combine remaining as "Others"
                other_count += row["RecipeCount"]
        
        # Add "Others" category if there are more than 10 tags
        if other_count > 0:
            other_percentage = (other_count / total_recipes_with_tags * 100) if total_recipes_with_tags > 0 else 0
            tag_distribution.append(TagAnalyticsData(
                tag_name="Others",
                recipe_count=other_count,
                percentage=round(other_percentage, 1)
            ))
        
        # Get most popular recipes by likes count
        popularity_query = """
        SELECT 
            r.RecipeID,
            r.Title,
            u.Username as AuthorName,
            COUNT(l.UserID) as LikesCount
        FROM Recipes r
        JOIN Users u ON r.AuthorID = u.UserID
        LEFT JOIN Likes l ON r.RecipeID = l.RecipeID
        WHERE r.AuthorID = ?
        GROUP BY r.RecipeID, r.Title, u.Username
        ORDER BY COUNT(l.UserID) DESC
        OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY
        """
        
        popularity_results = execute_query(popularity_query, (user_id,))
        
        popular_recipes = []
        for row in popularity_results:
            popular_recipes.append(RecipePopularityData(
                recipe_id=row["RecipeID"],
                title=row["Title"],
                author_name=row["AuthorName"],
                likes_count=row["LikesCount"]
            ))
        
        # Get total statistics
        total_recipes = execute_scalar(
            "SELECT COUNT(*) FROM Recipes WHERE AuthorID = ?",
            (user_id,)
        ) or 0
        
        total_tags = execute_scalar(
            """SELECT COUNT(DISTINCT t.TagID) 
               FROM Tags t
               JOIN RecipeTags rt ON t.TagID = rt.TagID
               JOIN Recipes r ON rt.RecipeID = r.RecipeID
               WHERE r.AuthorID = ?""",
            (user_id,)
        ) or 0
        
        print(f"Analytics data retrieved: {len(tag_distribution)} tag categories, {len(popular_recipes)} popular recipes")
        
        return AnalyticsResponse(
            tag_distribution=tag_distribution,
            popular_recipes=popular_recipes,
            total_recipes=total_recipes,
            total_tags=total_tags
        )
        
    except Exception as e:
        print(f"Error getting analytics: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics data: {str(e)}"
        )

@router.get("/global", response_model=AnalyticsResponse)
async def get_global_analytics(
    current_user: dict = Depends(verify_token)
):
    """
    Get global analytics across all recipes in the platform
    """
    try:
        print("Getting global analytics")
        
        # Get global tag distribution
        tag_query = """
        SELECT 
            t.TagName,
            COUNT(rt.RecipeID) as RecipeCount
        FROM Tags t
        JOIN RecipeTags rt ON t.TagID = rt.TagID
        GROUP BY t.TagID, t.TagName
        ORDER BY COUNT(rt.RecipeID) DESC
        """
        
        tag_results = execute_query(tag_query)
        
        # Calculate total recipes for percentage calculation
        total_recipes_with_tags = sum(row["RecipeCount"] for row in tag_results)
        
        # Process tag distribution (top 10 + others)
        tag_distribution = []
        other_count = 0
        
        for i, row in enumerate(tag_results):
            if i < 10:  # Top 10 tags
                percentage = (row["RecipeCount"] / total_recipes_with_tags * 100) if total_recipes_with_tags > 0 else 0
                tag_distribution.append(TagAnalyticsData(
                    tag_name=row["TagName"],
                    recipe_count=row["RecipeCount"],
                    percentage=round(percentage, 1)
                ))
            else:  # Combine remaining as "Others"
                other_count += row["RecipeCount"]
        
        # Add "Others" category if there are more than 10 tags
        if other_count > 0:
            other_percentage = (other_count / total_recipes_with_tags * 100) if total_recipes_with_tags > 0 else 0
            tag_distribution.append(TagAnalyticsData(
                tag_name="Others",
                recipe_count=other_count,
                percentage=round(other_percentage, 1)
            ))
        
        # Get most popular recipes globally
        popularity_query = """
        SELECT 
            r.RecipeID,
            r.Title,
            u.Username as AuthorName,
            COUNT(l.UserID) as LikesCount
        FROM Recipes r
        JOIN Users u ON r.AuthorID = u.UserID
        LEFT JOIN Likes l ON r.RecipeID = l.RecipeID
        GROUP BY r.RecipeID, r.Title, u.Username
        ORDER BY COUNT(l.UserID) DESC
        OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY
        """
        
        popularity_results = execute_query(popularity_query)
        
        popular_recipes = []
        for row in popularity_results:
            popular_recipes.append(RecipePopularityData(
                recipe_id=row["RecipeID"],
                title=row["Title"],
                author_name=row["AuthorName"],
                likes_count=row["LikesCount"]
            ))
        
        # Get total statistics
        total_recipes = execute_scalar("SELECT COUNT(*) FROM Recipes") or 0
        total_tags = execute_scalar("SELECT COUNT(*) FROM Tags") or 0
        
        print(f"Global analytics retrieved: {len(tag_distribution)} tag categories, {len(popular_recipes)} popular recipes")
        
        return AnalyticsResponse(
            tag_distribution=tag_distribution,
            popular_recipes=popular_recipes,
            total_recipes=total_recipes,
            total_tags=total_tags
        )
        
    except Exception as e:
        print(f"Error getting global analytics: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve global analytics data: {str(e)}"
        )