from .base_model import BaseModel
from database import execute_query, execute_non_query, execute_scalar, insert_and_get_id
import hashlib
from typing import List, Optional, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular import
if TYPE_CHECKING:
    from .tag import Tag

class Recipe(BaseModel):
    """
    Recipe model representing recipes in the platform
    
    This model interacts with the Recipes table in your SOMEE database
    """
    
    def __init__(self):
        self.recipeid = None
        self.authorid = None
        self.title = None
        self.description = None
        self.ingredients = None
        self.instructions = None
        self.imageurl = None
        self.rawingredients = None
        self.servings = None
        self.createdat = None
        
        # Additional properties (not stored in DB)
        self.author_username = None
        self.tags = []
        self.likes_count = 0
        self.favorites_count = 0
    
    @classmethod
    def get_by_id(cls, recipe_id: int) -> Optional['Recipe']:
        """
        Get recipe by ID with additional information
        
        Args:
            recipe_id (int): Recipe ID
            
        Returns:
            Optional[Recipe]: Recipe instance or None if not found
        """
        try:
            result = execute_query(
                """SELECT r.*, u.Username as AuthorUsername
                   FROM Recipes r
                   JOIN Users u ON r.AuthorID = u.UserID
                   WHERE r.RecipeID = ?""",
                (recipe_id,),
                fetch="one"
            )
            
            if result:
                recipe = cls.from_dict(result[0])
                recipe.author_username = result[0].get('AuthorUsername')
                
                # Get tags
                recipe.tags = recipe._get_tags()
                
                # Get counts
                recipe.likes_count = recipe._get_likes_count()
                recipe.favorites_count = recipe._get_favorites_count()
                
                return recipe
            return None
            
        except Exception as e:
            print(f"Error getting recipe by ID: {e}")
            return None
    
    @classmethod
    def get_by_author(cls, author_id: int, limit: int = 10) -> List['Recipe']:
        """
        Get recipes by author
        
        Args:
            author_id (int): Author user ID
            limit (int): Maximum number of recipes to return
            
        Returns:
            List[Recipe]: List of recipe instances
        """
        try:
            result = execute_query(
                """SELECT r.*, u.Username as AuthorUsername
                   FROM Recipes r
                   JOIN Users u ON r.AuthorID = u.UserID
                   WHERE r.AuthorID = ?
                   ORDER BY r.CreatedAt DESC""",
                (author_id,)
            )
            
            recipes = []
            for row in result[:limit]:
                recipe = cls.from_dict(row)
                recipe.author_username = row.get('AuthorUsername')
                recipes.append(recipe)
            
            return recipes
            
        except Exception as e:
            print(f"Error getting recipes by author: {e}")
            return []
    
    @classmethod
    def get_all(cls, limit: int = 20, offset: int = 0) -> List['Recipe']:
        """
        Get all recipes with pagination
        
        Args:
            limit (int): Maximum number of recipes to return
            offset (int): Number of recipes to skip
            
        Returns:
            List[Recipe]: List of recipe instances
        """
        try:
            result = execute_query(
                """SELECT r.*, u.Username as AuthorUsername
                   FROM Recipes r
                   JOIN Users u ON r.AuthorID = u.UserID
                   ORDER BY r.CreatedAt DESC
                   OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
                (offset, limit)
            )
            
            recipes = []
            for row in result:
                recipe = cls.from_dict(row)
                recipe.author_username = row.get('AuthorUsername')
                recipes.append(recipe)
            
            return recipes
            
        except Exception as e:
            print(f"Error getting all recipes: {e}")
            return []
    
    @classmethod
    def search(cls, query: str, tags: List[str] = None, limit: int = 20) -> List['Recipe']:
        """
        Search recipes by title, description, or tags
        
        Args:
            query (str): Search query string
            tags (List[str]): List of tag names to filter by
            limit (int): Maximum number of results
            
        Returns:
            List[Recipe]: List of recipe instances
        """
        try:
            base_query = """
                SELECT DISTINCT r.*, u.Username as AuthorUsername
                FROM Recipes r
                JOIN Users u ON r.AuthorID = u.UserID
            """
            
            conditions = []
            params = []
            
            # Add text search
            if query:
                conditions.append("(r.Title LIKE ? OR r.Description LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])
            
            # Add tag filtering
            if tags:
                placeholders = ",".join(["?" for _ in tags])
                base_query += f"""
                    JOIN RecipeTags rt ON r.RecipeID = rt.RecipeID
                    JOIN Tags t ON rt.TagID = t.TagID
                """
                conditions.append(f"t.TagName IN ({placeholders})")
                params.extend(tags)
            
            # Build final query
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            
            base_query += " ORDER BY r.CreatedAt DESC"
            
            result = execute_query(base_query, tuple(params))
            
            recipes = []
            for row in result[:limit]:
                recipe = cls.from_dict(row)
                recipe.author_username = row.get('AuthorUsername')
                recipes.append(recipe)
            
            return recipes
            
        except Exception as e:
            print(f"Error searching recipes: {e}")
            return []
    
    def save(self) -> bool:
        """
        Save recipe to database (create or update)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.recipeid is None:
                # Create new recipe
                recipe_id = insert_and_get_id(
                    "Recipes",
                    ["AuthorID", "Title", "Description", "Ingredients", 
                     "Instructions", "ImageURL", "RawIngredients", "Servings"],
                    (self.authorid, self.title, self.description, self.ingredients,
                     self.instructions, self.imageurl, self.rawingredients, self.servings)
                )
                self.recipeid = recipe_id
                print(f"Recipe created with ID: {recipe_id}")
                return True
            else:
                # Update existing recipe
                rows_affected = execute_non_query(
                    """UPDATE Recipes 
                       SET Title = ?, Description = ?, Ingredients = ?,
                           Instructions = ?, ImageURL = ?, RawIngredients = ?, Servings = ?
                       WHERE RecipeID = ?""",
                    (self.title, self.description, self.ingredients, self.instructions,
                     self.imageurl, self.rawingredients, self.servings, self.recipeid)
                )
                print(f"Recipe updated, {rows_affected} rows affected")
                return rows_affected > 0
                
        except Exception as e:
            print(f"Error saving recipe: {e}")
            return False
    
    def delete(self) -> bool:
        """
        Delete recipe from database
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.recipeid is None:
                return False
            
            rows_affected = execute_non_query(
                "DELETE FROM Recipes WHERE RecipeID = ?",
                (self.recipeid,)
            )
            
            print(f"Recipe deleted, {rows_affected} rows affected")
            return rows_affected > 0
            
        except Exception as e:
            print(f"Error deleting recipe: {e}")
            return False
    
    def _get_tags(self) -> List[str]:
        """Get tags for this recipe"""
        if self.recipeid is None:
            return []
        
        try:
            result = execute_query(
                """SELECT t.TagName FROM Tags t
                   JOIN RecipeTags rt ON t.TagID = rt.TagID
                   WHERE rt.RecipeID = ?""",
                (self.recipeid,)
            )
            
            return [row['TagName'] for row in result]
            
        except Exception as e:
            print(f"Error getting recipe tags: {e}")
            return []
    
    def _get_likes_count(self) -> int:
        """Get number of likes for this recipe"""
        if self.recipeid is None:
            return 0
        
        try:
            count = execute_scalar(
                "SELECT COUNT(*) FROM Likes WHERE RecipeID = ?",
                (self.recipeid,)
            )
            return count or 0
            
        except Exception as e:
            print(f"Error getting likes count: {e}")
            return 0
    
    def _get_favorites_count(self) -> int:
        """Get number of favorites for this recipe"""
        if self.recipeid is None:
            return 0
        
        try:
            count = execute_scalar(
                "SELECT COUNT(*) FROM Favorites WHERE RecipeID = ?",
                (self.recipeid,)
            )
            return count or 0
            
        except Exception as e:
            print(f"Error getting favorites count: {e}")
            return 0
    
    def add_tag(self, tag_name: str) -> bool:
        """
        Add a tag to this recipe
        
        Args:
            tag_name (str): Tag name to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.recipeid is None:
            return False
        
        try:
            # Import Tag only when needed to avoid circular import
            from .tag import Tag
            
            # Get or create tag
            tag = Tag.get_or_create(tag_name)
            if not tag:
                return False
            
            # Check if association already exists
            existing = execute_scalar(
                "SELECT COUNT(*) FROM RecipeTags WHERE RecipeID = ? AND TagID = ?",
                (self.recipeid, tag.tagid)
            )
            
            if existing > 0:
                print(f"Tag '{tag_name}' already associated with recipe")
                return True
            
            # Create association
            rows_affected = execute_non_query(
                "INSERT INTO RecipeTags (RecipeID, TagID) VALUES (?, ?)",
                (self.recipeid, tag.tagid)
            )
            
            return rows_affected > 0
            
        except Exception as e:
            print(f"Error adding tag to recipe: {e}")
            return False
    
    def remove_tag(self, tag_name: str) -> bool:
        """
        Remove a tag from this recipe
        
        Args:
            tag_name (str): Tag name to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.recipeid is None:
            return False
        
        try:
            rows_affected = execute_non_query(
                """DELETE FROM RecipeTags 
                   WHERE RecipeID = ? AND TagID = (
                       SELECT TagID FROM Tags WHERE TagName = ?
                   )""",
                (self.recipeid, tag_name)
            )
            
            return rows_affected > 0
            
        except Exception as e:
            print(f"Error removing tag from recipe: {e}")
            return False