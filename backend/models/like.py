from .base_model import BaseModel
from database import execute_query, execute_non_query, execute_scalar, insert_and_get_id, get_database_cursor
import hashlib
from typing import Optional, Dict, Any

class Like(BaseModel):
    """
    Like model for tracking user likes on recipes
    
    This model interacts with the Likes table in your SOMEE database
    """
    
    def __init__(self):
        self.userid = None
        self.recipeid = None
        self.createdat = None
    
    @classmethod
    def add_like(cls, user_id: int, recipe_id: int) -> bool:
        """
        Add a like for a recipe by a user
        
        Args:
            user_id (int): User ID
            recipe_id (int): Recipe ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if like already exists
            existing = execute_scalar(
                "SELECT COUNT(*) FROM Likes WHERE UserID = ? AND RecipeID = ?",
                (user_id, recipe_id)
            )
            
            if existing > 0:
                print("Like already exists")
                return True
            
            # Add like
            rows_affected = execute_non_query(
                "INSERT INTO Likes (UserID, RecipeID) VALUES (?, ?)",
                (user_id, recipe_id)
            )
            
            return rows_affected > 0
            
        except Exception as e:
            print(f"Error adding like: {e}")
            return False
    
    @classmethod
    def remove_like(cls, user_id: int, recipe_id: int) -> bool:
        """
        Remove a like for a recipe by a user
        
        Args:
            user_id (int): User ID
            recipe_id (int): Recipe ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            rows_affected = execute_non_query(
                "DELETE FROM Likes WHERE UserID = ? AND RecipeID = ?",
                (user_id, recipe_id)
            )
            
            return rows_affected > 0
            
        except Exception as e:
            print(f"Error removing like: {e}")
            return False
    
    @classmethod
    def is_liked_by_user(cls, user_id: int, recipe_id: int) -> bool:
        """
        Check if recipe is liked by user
        
        Args:
            user_id (int): User ID
            recipe_id (int): Recipe ID
            
        Returns:
            bool: True if liked, False otherwise
        """
        try:
            count = execute_scalar(
                "SELECT COUNT(*) FROM Likes WHERE UserID = ? AND RecipeID = ?",
                (user_id, recipe_id)
            )
            
            return count > 0
            
        except Exception as e:
            print(f"Error checking like status: {e}")
            return False
    
    # ============= METHODS FROM USER_ROUTES =============
    
    @classmethod
    def toggle_like(cls, user_id: int, recipe_id: int) -> Dict[str, Any]:
        """
        Toggle like status on a recipe
        
        Args:
            user_id (int): User ID
            recipe_id (int): Recipe ID
            
        Returns:
            Dict: Result with like status and total count
        """
        try:
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
            
            return {
                "success": True,
                "is_liked": new_status,
                "total_likes": total_likes,
                "action_type": action_type,
                "previous_state": is_liked
            }
            
        except Exception as e:
            print(f"Error toggling recipe like: {e}")
            return {"error": "Failed to toggle recipe like"}
    
    # ============= NEW METHODS FROM RECIPE_ROUTES =============
    
    @classmethod
    def toggle_like_with_transaction(cls, user_id: int, recipe_id: int) -> Dict[str, Any]:
        """
        Toggle like status using single database transaction (optimized version from recipe_routes)
        
        Args:
            user_id (int): User ID
            recipe_id (int): Recipe ID
            
        Returns:
            Dict: Result with like status
        """
        try:
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
                    return {"error": "Recipe not found"}
                
                is_currently_liked = bool(result.is_liked)
                
                # Toggle like in same transaction
                if is_currently_liked:
                    cursor.execute("DELETE FROM Likes WHERE RecipeID = ? AND UserID = ?", 
                                  (recipe_id, user_id))
                    is_liked = False
                    action_type = "Unliked"
                else:
                    cursor.execute("INSERT INTO Likes (RecipeID, UserID) VALUES (?, ?)", 
                                  (recipe_id, user_id))
                    is_liked = True
                    action_type = "Liked"
            
            return {
                "success": True,
                "is_liked": is_liked,
                "action_type": action_type,
                "previous_state": is_currently_liked
            }
            
        except Exception as e:
            print(f"Error toggling like with transaction: {e}")
            return {"error": "Failed to toggle like"}
    
    @classmethod
    def get_total_likes(cls, recipe_id: int) -> int:
        """
        Get total number of likes for a recipe
        
        Args:
            recipe_id (int): Recipe ID
            
        Returns:
            int: Total number of likes
        """
        try:
            count = execute_scalar(
                "SELECT COUNT(*) FROM Likes WHERE RecipeID = ?",
                (recipe_id,)
            )
            return count or 0
            
        except Exception as e:
            print(f"Error getting total likes: {e}")
            return 0