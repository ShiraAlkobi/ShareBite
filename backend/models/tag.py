from .base_model import BaseModel
from database import execute_query, execute_non_query, execute_scalar, insert_and_get_id
import hashlib
from typing import List, Optional, TYPE_CHECKING, Dict, Any

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
    
    # ============= NEW METHODS FROM ADD_RECIPE_ROUTES =============
    
    @classmethod
    def get_all_with_usage_count(cls, order_by: str = "usage", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all tags with usage counts (CQRS-style query execution)
        
        Args:
            order_by (str): Ordering method ("usage", "name", etc.)
            limit (int): Maximum number of tags to return
            
        Returns:
            List[Dict]: List of tag dictionaries with usage counts
        """
        try:
            if order_by == "usage":
                order_clause = "ORDER BY UsageCount DESC, t.TagName ASC"
            elif order_by == "name":
                order_clause = "ORDER BY t.TagName ASC"
            else:
                order_clause = "ORDER BY UsageCount DESC, t.TagName ASC"
            
            query = f"""
                SELECT t.TagID, t.TagName, COUNT(rt.RecipeID) as UsageCount
                FROM Tags t
                LEFT JOIN RecipeTags rt ON t.TagID = rt.TagID
                GROUP BY t.TagID, t.TagName
                {order_clause}
            """
            
            result = execute_query(query)
            
            tags = []
            for row in result[:limit]:
                tags.append({
                    "TagID": row['TagID'],
                    "TagName": row['TagName'],
                    "UsageCount": row['UsageCount']
                })
            
            return tags
            
        except Exception as e:
            print(f"Error getting all tags with usage count: {e}")
            return []
    
    @classmethod
    def search_tags(cls, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search tags by name (CQRS-style query execution)
        
        Args:
            search_term (str): Search term for tag names
            limit (int): Maximum number of results to return
            
        Returns:
            List[Dict]: List of matching tag dictionaries
        """
        try:
            query = """
                SELECT t.TagID, t.TagName, COUNT(rt.RecipeID) as UsageCount
                FROM Tags t
                LEFT JOIN RecipeTags rt ON t.TagID = rt.TagID
                WHERE LOWER(t.TagName) LIKE LOWER(?)
                GROUP BY t.TagID, t.TagName
                ORDER BY UsageCount DESC, t.TagName ASC
            """
            
            search_pattern = f"%{search_term}%"
            result = execute_query(query, (search_pattern,))
            
            tags = []
            for row in result[:limit]:
                tags.append({
                    "TagID": row['TagID'],
                    "TagName": row['TagName'],
                    "UsageCount": row['UsageCount']
                })
            
            return tags
            
        except Exception as e:
            print(f"Error searching tags: {e}")
            return []
    
    @classmethod
    def get_popular_tags(cls, limit: int = 20, min_usage: int = 1) -> List[Dict[str, Any]]:
        """
        Get popular tags with minimum usage (CQRS-style query execution)
        
        Args:
            limit (int): Maximum number of tags to return
            min_usage (int): Minimum usage count to include
            
        Returns:
            List[Dict]: List of popular tag dictionaries
        """
        try:
            query = """
                SELECT t.TagID, t.TagName, COUNT(rt.RecipeID) as UsageCount
                FROM Tags t
                JOIN RecipeTags rt ON t.TagID = rt.TagID
                GROUP BY t.TagID, t.TagName
                HAVING COUNT(rt.RecipeID) >= ?
                ORDER BY UsageCount DESC, t.TagName ASC
            """
            
            result = execute_query(query, (min_usage,))
            
            tags = []
            for row in result[:limit]:
                tags.append({
                    "TagID": row['TagID'],
                    "TagName": row['TagName'],
                    "UsageCount": row['UsageCount']
                })
            
            return tags
            
        except Exception as e:
            print(f"Error getting popular tags: {e}")
            return []
    
    @classmethod
    def get_common_tags_fallback(cls) -> List[Dict[str, Any]]:
        """
        Get fallback common tags when database is empty
        
        Returns:
            List[Dict]: List of predefined common tag dictionaries
        """
        common_tags = [
            "vegetarian", "vegan", "gluten-free", "dairy-free", "keto",
            "quick", "easy", "healthy", "comfort-food", "dessert",
            "breakfast", "lunch", "dinner", "snack", "appetizer",
            "main-course", "side-dish", "soup", "salad", "pasta"
        ]
        
        return [{"tag_name": tag, "usage_count": 0} for tag in common_tags]
    
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