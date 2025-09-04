from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Dict, Any
from routes.auth_routes import verify_token
from models.analytics import Analytics
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
    Get analytics data for a specific user - READ ONLY but logs analytics access
    """
    try:
        # Verify user can access this data (either their own or public analytics)
        if current_user["userid"] != user_id:
            # For now, allow access to other users' analytics
            # You could add privacy controls here
            pass
        
        print(f"Getting analytics for user: {user_id}")
        
        # Log analytics access event using Analytics model
        analytics_event_data = {
            "analytics_type": "user_specific",
            "target_user_id": user_id,
            "requested_by_user_id": current_user["userid"],
            "requested_by_username": current_user["username"],
            "is_own_analytics": current_user["userid"] == user_id,
            "timestamp": datetime.now().isoformat()
        }
        Analytics.log_analytics_event(current_user["userid"], "AnalyticsViewed", analytics_event_data)
        
        # Get tag distribution for user's recipes using Analytics model
        tag_results = Analytics.get_user_tag_distribution(user_id)
        
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
        
        # Get most popular recipes by likes count using Analytics model
        popularity_results = Analytics.get_user_popular_recipes(user_id, 10)
        
        popular_recipes = []
        for row in popularity_results:
            popular_recipes.append(RecipePopularityData(
                recipe_id=row["RecipeID"],
                title=row["Title"],
                author_name=row["AuthorName"],
                likes_count=row["LikesCount"]
            ))
        
        # Get total statistics using Analytics model
        total_recipes, total_tags = Analytics.get_user_recipe_stats(user_id)
        
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
    Get global analytics across all recipes in the platform - READ ONLY but logs analytics access
    """
    try:
        print("Getting global analytics")
        
        # Log global analytics access event using Analytics model
        analytics_event_data = {
            "analytics_type": "global",
            "requested_by_user_id": current_user["userid"],
            "requested_by_username": current_user["username"],
            "timestamp": datetime.now().isoformat()
        }
        Analytics.log_analytics_event(current_user["userid"], "GlobalAnalyticsViewed", analytics_event_data)
        
        # Get global tag distribution using Analytics model
        tag_results = Analytics.get_global_tag_distribution()
        
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
        
        # Get most popular recipes globally using Analytics model
        popularity_results = Analytics.get_global_popular_recipes(10)
        
        popular_recipes = []
        for row in popularity_results:
            popular_recipes.append(RecipePopularityData(
                recipe_id=row["RecipeID"],
                title=row["Title"],
                author_name=row["AuthorName"],
                likes_count=row["LikesCount"]
            ))
        
        # Get total statistics using Analytics model
        total_recipes, total_tags = Analytics.get_global_recipe_stats()
        
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