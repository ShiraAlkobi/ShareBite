from .base_model import BaseModel
from database import execute_query, execute_non_query, execute_scalar, insert_and_get_id
import hashlib
from typing import List, Optional, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular import
if TYPE_CHECKING:
    from .recipe import Recipe

class Tag(BaseModel):
    """
    Tag model for categorizing recipes
    
    This model interacts with the Tags table in your SOMEE database
    """
    
    def __init__(self):
        self.tagid = None
        self.tagname = None
        self.recipe_count = 0
    
    @classmethod
    def get_by_id(cls, tag_id: int) -> Optional['Tag']:
        """
        Get tag by ID
        
        Args:
            tag_id (int): Tag ID
            
        Returns:
            Optional[Tag]: Tag instance or None if not found
        """
        try:
            result = execute_query(
                "SELECT * FROM Tags WHERE TagID = ?",
                (tag_id,),
                fetch="one"
            )
            
            if result:
                tag = cls.from_dict(result[0])
                tag.recipe_count = tag._get_recipe_count()
                return tag
            return None
            
        except Exception as e:
            print(f"Error getting tag by ID: {e}")
            return None
    
    @classmethod
    def get_by_name(cls, tag_name: str) -> Optional['Tag']:
        """
        Get tag by name
        
        Args:
            tag_name (str): Tag name
            
        Returns:
            Optional[Tag]: Tag instance or None if not found
        """
        try:
            result = execute_query(
                "SELECT * FROM Tags WHERE TagName = ?",
                (tag_name,),
                fetch="one"
            )
            
            if result:
                tag = cls.from_dict(result[0])
                tag.recipe_count = tag._get_recipe_count()
                return tag
            return None
            
        except Exception as e:
            print(f"Error getting tag by name: {e}")
            return None
    
    @classmethod
    def get_all(cls, limit: int = 50) -> List['Tag']:
        """
        Get all tags with recipe counts
        
        Args:
            limit (int): Maximum number of tags to return
            
        Returns:
            List[Tag]: List of tag instances
        """
        try:
            result = execute_query(
                """SELECT t.TagID, t.TagName, COUNT(rt.RecipeID) as RecipeCount
                   FROM Tags t
                   LEFT JOIN RecipeTags rt ON t.TagID = rt.TagID
                   GROUP BY t.TagID, t.TagName
                   ORDER BY RecipeCount DESC, t.TagName ASC"""
            )
            
            tags = []
            for row in result[:limit]:
                tag = cls()
                tag.tagid = row['TagID']
                tag.tagname = row['TagName']
                tag.recipe_count = row['RecipeCount']
                tags.append(tag)
            
            return tags
            
        except Exception as e:
            print(f"Error getting all tags: {e}")
            return []
    
    @classmethod
    def get_popular(cls, limit: int = 10) -> List['Tag']:
        """
        Get most popular tags by recipe count
        
        Args:
            limit (int): Number of tags to return
            
        Returns:
            List[Tag]: List of popular tag instances
        """
        try:
            result = execute_query(
                """SELECT t.TagID, t.TagName, COUNT(rt.RecipeID) as RecipeCount
                   FROM Tags t
                   JOIN RecipeTags rt ON t.TagID = rt.TagID
                   GROUP BY t.TagID, t.TagName
                   ORDER BY RecipeCount DESC""",
            )
            
            tags = []
            for row in result[:limit]:
                tag = cls()
                tag.tagid = row['TagID']
                tag.tagname = row['TagName']
                tag.recipe_count = row['RecipeCount']
                tags.append(tag)
            
            return tags
            
        except Exception as e:
            print(f"Error getting popular tags: {e}")
            return []
    
    @classmethod
    def get_or_create(cls, tag_name: str) -> Optional['Tag']:
        """
        Get existing tag or create new one
        
        Args:
            tag_name (str): Tag name
            
        Returns:
            Optional[Tag]: Tag instance or None if creation failed
        """
        # Try to get existing tag
        existing_tag = cls.get_by_name(tag_name)
        if existing_tag:
            return existing_tag
        
        # Create new tag
        try:
            tag_id = insert_and_get_id(
                "Tags",
                ["TagName"],
                (tag_name,)
            )
            
            tag = cls()
            tag.tagid = tag_id
            tag.tagname = tag_name
            tag.recipe_count = 0
            
            print(f"Tag created: {tag_name} with ID: {tag_id}")
            return tag
            
        except Exception as e:
            print(f"Error creating tag: {e}")
            return None
    
    def _get_recipe_count(self) -> int:
        """Get number of recipes with this tag"""
        if self.tagid is None:
            return 0
        
        try:
            count = execute_scalar(
                "SELECT COUNT(*) FROM RecipeTags WHERE TagID = ?",
                (self.tagid,)
            )
            return count or 0
            
        except Exception as e:
            print(f"Error getting recipe count for tag: {e}")
            return 0
    
    def get_recipes(self, limit: int = 20):
        """
        Get all recipes with this tag
        
        Args:
            limit (int): Maximum number of recipes to return
            
        Returns:
            List[Recipe]: List of recipe instances
        """
        if self.tagid is None:
            return []
        
        try:
            # Import Recipe only when needed to avoid circular import
            from .recipe import Recipe
            
            result = execute_query(
                """SELECT r.*, u.Username as AuthorUsername
                   FROM Recipes r
                   JOIN Users u ON r.AuthorID = u.UserID
                   JOIN RecipeTags rt ON r.RecipeID = rt.RecipeID
                   WHERE rt.TagID = ?
                   ORDER BY r.CreatedAt DESC""",
                (self.tagid,)
            )
            
            recipes = []
            for row in result[:limit]:
                recipe = Recipe.from_dict(row)
                recipe.author_username = row.get('AuthorUsername')
                recipes.append(recipe)
            
            return recipes
            
        except Exception as e:
            print(f"Error getting recipes for tag: {e}")
            return []