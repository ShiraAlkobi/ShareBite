from .base_model import BaseModel
from database import execute_query, execute_non_query, execute_scalar, insert_and_get_id
import hashlib
from typing import Optional

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
            print(f"❌ Error adding like: {e}")
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
            print(f"❌ Error removing like: {e}")
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
            print(f"❌ Error checking like status: {e}")
            return False