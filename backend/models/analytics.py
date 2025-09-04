from .base_model import BaseModel
from database import execute_query, execute_non_query, execute_scalar, insert_and_get_id
from typing import List, Dict, Any, Tuple
from datetime import datetime
import json

class Analytics(BaseModel):
    """
    Analytics model for handling analytics-related database operations
    
    This model handles tag distribution, recipe popularity analytics, and event logging
    """
    
    @classmethod
    def get_user_tag_distribution(cls, user_id: int) -> List[Dict[str, Any]]:
        """
        Get tag distribution for user's recipes
        
        Args:
            user_id (int): User ID
            
        Returns:
            List[Dict]: Tag distribution data with recipe counts
        """
        try:
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
            
            return execute_query(tag_query, (user_id,))
            
        except Exception as e:
            print(f"Error getting user tag distribution: {e}")
            return []
    
    @classmethod
    def get_global_tag_distribution(cls) -> List[Dict[str, Any]]:
        """
        Get global tag distribution across all recipes
        
        Returns:
            List[Dict]: Global tag distribution data
        """
        try:
            tag_query = """
            SELECT 
                t.TagName,
                COUNT(rt.RecipeID) as RecipeCount
            FROM Tags t
            JOIN RecipeTags rt ON t.TagID = rt.TagID
            GROUP BY t.TagID, t.TagName
            ORDER BY COUNT(rt.RecipeID) DESC
            """
            
            return execute_query(tag_query)
            
        except Exception as e:
            print(f"Error getting global tag distribution: {e}")
            return []
    
    @classmethod
    def get_user_popular_recipes(cls, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most popular recipes by likes count for a user
        
        Args:
            user_id (int): User ID
            limit (int): Maximum number of recipes to return
            
        Returns:
            List[Dict]: Popular recipes data
        """
        try:
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
            OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
            """
            
            return execute_query(popularity_query, (user_id, limit))
            
        except Exception as e:
            print(f"Error getting user popular recipes: {e}")
            return []
    
    @classmethod
    def get_global_popular_recipes(cls, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most popular recipes globally by likes count
        
        Args:
            limit (int): Maximum number of recipes to return
            
        Returns:
            List[Dict]: Popular recipes data
        """
        try:
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
            OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
            """
            
            return execute_query(popularity_query, (limit,))
            
        except Exception as e:
            print(f"Error getting global popular recipes: {e}")
            return []
    
    @classmethod
    def get_user_recipe_stats(cls, user_id: int) -> Tuple[int, int]:
        """
        Get total recipe and tag counts for a user
        
        Args:
            user_id (int): User ID
            
        Returns:
            Tuple[int, int]: (total_recipes, total_tags)
        """
        try:
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
            
            return total_recipes, total_tags
            
        except Exception as e:
            print(f"Error getting user recipe stats: {e}")
            return 0, 0
    
    @classmethod
    def get_global_recipe_stats(cls) -> Tuple[int, int]:
        """
        Get global recipe and tag counts
        
        Returns:
            Tuple[int, int]: (total_recipes, total_tags)
        """
        try:
            total_recipes = execute_scalar("SELECT COUNT(*) FROM Recipes") or 0
            total_tags = execute_scalar("SELECT COUNT(*) FROM Tags") or 0
            
            return total_recipes, total_tags
            
        except Exception as e:
            print(f"Error getting global recipe stats: {e}")
            return 0, 0
    
    @classmethod
    def log_analytics_event(cls, user_id: int, action_type: str, event_data: dict = None):
        """
        Log an analytics event to the RecipeEvents table for event sourcing
        Note: We use recipe_id = 0 for analytics-related events since they're not recipe-specific
        
        Args:
            user_id (int): ID of the user performing the action
            action_type (str): Type of action (AnalyticsViewed, etc.)
            event_data (Dict): Additional data to store as JSON
        """
        try:
            # Convert event_data to JSON string if provided
            event_data_json = json.dumps(event_data) if event_data else None
            
            # Insert event into RecipeEvents table (using RecipeID = 0 for analytics events)
            execute_non_query(
                """INSERT INTO RecipeEvents (RecipeID, UserID, ActionType, EventData) 
                   VALUES (?, ?, ?, ?)""",
                (0, user_id, action_type, event_data_json)
            )
            
            print(f"Analytics event logged: {action_type} - User {user_id}")
            
        except Exception as e:
            print(f"Failed to log analytics event: {e}")
            # Don't raise exception - event logging failure shouldn't break the main operation