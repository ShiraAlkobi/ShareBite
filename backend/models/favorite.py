from .base_model import BaseModel
from database import execute_query, execute_non_query, execute_scalar, insert_and_get_id
import hashlib
from typing import List
from .recipe import Recipe

class Favorite(BaseModel):
    """
    Favorite model for tracking user favorites on recipes
    
    This model interacts with the Favorites table in your SOMEE database
    """
    
    def __init__(self):
        self.userid = None
        self.recipeid = None
        self.createdat = None
    
    @classmethod
    def add_favorite(cls, user_id: int, recipe_id: int) -> bool:
        """
        Add a favorite for a recipe by a user
        
        Args:
            user_id (int): User ID
            recipe_id (int): Recipe ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if favorite already exists
            existing = execute_scalar(
                "SELECT COUNT(*) FROM Favorites WHERE UserID = ? AND RecipeID = ?",
                (user_id, recipe_id)
            )
            
            if existing > 0:
                print("Favorite already exists")
                return True
            
            # Add favorite
            rows_affected = execute_non_query(
                "INSERT INTO Favorites (UserID, RecipeID) VALUES (?, ?)",
                (user_id, recipe_id)
            )
            
            return rows_affected > 0
            
        except Exception as e:
            print(f"❌ Error adding favorite: {e}")
            return False
    
    @classmethod
    def remove_favorite(cls, user_id: int, recipe_id: int) -> bool:
        """
        Remove a favorite for a recipe by a user
        
        Args:
            user_id (int): User ID
            recipe_id (int): Recipe ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            rows_affected = execute_non_query(
                "DELETE FROM Favorites WHERE UserID = ? AND RecipeID = ?",
                (user_id, recipe_id)
            )
            
            return rows_affected > 0
            
        except Exception as e:
            print(f"❌ Error removing favorite: {e}")
            return False
    
    @classmethod
    def is_favorited_by_user(cls, user_id: int, recipe_id: int) -> bool:
        """
        Check if recipe is favorited by user
        
        Args:
            user_id (int): User ID
            recipe_id (int): Recipe ID
            
        Returns:
            bool: True if favorited, False otherwise
        """
        try:
            count = execute_scalar(
                "SELECT COUNT(*) FROM Favorites WHERE UserID = ? AND RecipeID = ?",
                (user_id, recipe_id)
            )
            
            return count > 0
            
        except Exception as e:
            print(f"❌ Error checking favorite status: {e}")
            return False
    
    @classmethod
    def get_user_favorites(cls, user_id: int, limit: int = 20) -> List[Recipe]:
        """
        Get all favorite recipes for a user
        
        Args:
            user_id (int): User ID
            limit (int): Maximum number of recipes to return
            
        Returns:
            List[Recipe]: List of favorite recipe instances
        """
        try:
            result = execute_query(
                """SELECT r.*, u.Username as AuthorUsername
                   FROM Recipes r
                   JOIN Users u ON r.AuthorID = u.UserID
                   JOIN Favorites f ON r.RecipeID = f.RecipeID
                   WHERE f.UserID = ?
                   ORDER BY f.CreatedAt DESC""",
                (user_id,)
            )
            
            recipes = []
            for row in result[:limit]:
                recipe = Recipe.from_dict(row)
                recipe.author_username = row.get('AuthorUsername')
                recipes.append(recipe)
            
            return recipes
            
        except Exception as e:
            print(f"❌ Error getting user favorites: {e}")
            return []