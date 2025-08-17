from typing import Dict, Any, List, Optional
from datetime import datetime
from database import execute_query, execute_non_query, execute_scalar, insert_and_get_id
import hashlib
import json

class BaseModel:
    """
    Base model class with common functionality
    """
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create model instance from dictionary"""
        instance = cls()
        for key, value in data.items():
            # Convert SQL Server column names to Python attributes
            attr_name = key.lower()
            if hasattr(instance, attr_name):
                setattr(instance, attr_name, value)
        return instance
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result

class User(BaseModel):
    """
    User model representing users in the recipe sharing platform
    
    This model interacts with the Users table in your SOMEE database
    """
    
    def __init__(self):
        self.userid = None
        self.username = None
        self.email = None
        self.passwordhash = None
        self.profilepicurl = None
        self.bio = None
        self.createdat = None
    
    @staticmethod
    def create_password_hash(password: str) -> str:
        """Create password hash using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @classmethod
    def get_by_id(cls, user_id: int) -> Optional['User']:
        """
        Get user by ID
        
        Args:
            user_id (int): User ID
            
        Returns:
            Optional[User]: User instance or None if not found
        """
        try:
            result = execute_query(
                "SELECT * FROM Users WHERE UserID = ?", 
                (user_id,), 
                fetch="one"
            )
            
            if result:
                return cls.from_dict(result[0])
            return None
            
        except Exception as e:
            print(f"❌ Error getting user by ID: {e}")
            return None
    
    @classmethod
    def get_by_username(cls, username: str) -> Optional['User']:
        """
        Get user by username
        
        Args:
            username (str): Username
            
        Returns:
            Optional[User]: User instance or None if not found
        """
        try:
            result = execute_query(
                "SELECT * FROM Users WHERE Username = ?", 
                (username,), 
                fetch="one"
            )
            
            if result:
                return cls.from_dict(result[0])
            return None
            
        except Exception as e:
            print(f"❌ Error getting user by username: {e}")
            return None
    
    @classmethod
    def get_by_email(cls, email: str) -> Optional['User']:
        """
        Get user by email
        
        Args:
            email (str): Email address
            
        Returns:
            Optional[User]: User instance or None if not found
        """
        try:
            result = execute_query(
                "SELECT * FROM Users WHERE Email = ?", 
                (email,), 
                fetch="one"
            )
            
            if result:
                return cls.from_dict(result[0])
            return None
            
        except Exception as e:
            print(f"❌ Error getting user by email: {e}")
            return None
    
    @classmethod
    def get_all(cls, limit: int = 50, offset: int = 0) -> List['User']:
        """
        Get all users with pagination
        
        Args:
            limit (int): Maximum number of users to return
            offset (int): Number of users to skip
            
        Returns:
            List[User]: List of user instances
        """
        try:
            result = execute_query(
                "SELECT * FROM Users ORDER BY CreatedAt DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",
                (offset, limit)
            )
            
            return [cls.from_dict(row) for row in result]
            
        except Exception as e:
            print(f"❌ Error getting all users: {e}")
            return []
    
    def save(self) -> bool:
        """
        Save user to database (create or update)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.userid is None:
                # Create new user
                user_id = insert_and_get_id(
                    "Users",
                    ["Username", "Email", "PasswordHash", "ProfilePicURL", "Bio"],
                    (self.username, self.email, self.passwordhash, self.profilepicurl, self.bio)
                )
                self.userid = user_id
                print(f"✅ User created with ID: {user_id}")
                return True
            else:
                # Update existing user
                rows_affected = execute_non_query(
                    """UPDATE Users 
                       SET Username = ?, Email = ?, PasswordHash = ?, 
                           ProfilePicURL = ?, Bio = ?
                       WHERE UserID = ?""",
                    (self.username, self.email, self.passwordhash, 
                     self.profilepicurl, self.bio, self.userid)
                )
                print(f"✅ User updated, {rows_affected} rows affected")
                return rows_affected > 0
                
        except Exception as e:
            print(f"❌ Error saving user: {e}")
            return False
    
    def delete(self) -> bool:
        """
        Delete user from database
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.userid is None:
                return False
            
            rows_affected = execute_non_query(
                "DELETE FROM Users WHERE UserID = ?",
                (self.userid,)
            )
            
            print(f"✅ User deleted, {rows_affected} rows affected")
            return rows_affected > 0
            
        except Exception as e:
            print(f"❌ Error deleting user: {e}")
            return False
    
    def get_recipes(self, limit: int = 10) -> List['Recipe']:
        """
        Get all recipes created by this user
        
        Args:
            limit (int): Maximum number of recipes to return
            
        Returns:
            List[Recipe]: List of recipe instances
        """
        if self.userid is None:
            return []
        
        return Recipe.get_by_author(self.userid, limit)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get user statistics
        
        Returns:
            Dict[str, Any]: User statistics
        """
        if self.userid is None:
            return {}
        
        try:
            recipe_count = execute_scalar(
                "SELECT COUNT(*) FROM Recipes WHERE AuthorID = ?",
                (self.userid,)
            )
            
            likes_received = execute_scalar(
                """SELECT COUNT(*) FROM Likes l
                   JOIN Recipes r ON l.RecipeID = r.RecipeID
                   WHERE r.AuthorID = ?""",
                (self.userid,)
            )
            
            favorites_received = execute_scalar(
                """SELECT COUNT(*) FROM Favorites f
                   JOIN Recipes r ON f.RecipeID = r.RecipeID
                   WHERE r.AuthorID = ?""",
                (self.userid,)
            )
            
            return {
                "recipes_created": recipe_count or 0,
                "total_likes_received": likes_received or 0,
                "total_favorites_received": favorites_received or 0
            }
            
        except Exception as e:
            print(f"❌ Error getting user stats: {e}")
            return {}

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
            print(f"❌ Error getting recipe by ID: {e}")
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
            print(f"❌ Error getting recipes by author: {e}")
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
            print(f"❌ Error getting all recipes: {e}")
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
            print(f"❌ Error searching recipes: {e}")
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
                print(f"✅ Recipe created with ID: {recipe_id}")
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
                print(f"✅ Recipe updated, {rows_affected} rows affected")
                return rows_affected > 0
                
        except Exception as e:
            print(f"❌ Error saving recipe: {e}")
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
            
            print(f"✅ Recipe deleted, {rows_affected} rows affected")
            return rows_affected > 0
            
        except Exception as e:
            print(f"❌ Error deleting recipe: {e}")
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
            print(f"❌ Error getting recipe tags: {e}")
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
            print(f"❌ Error getting likes count: {e}")
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
            print(f"❌ Error getting favorites count: {e}")
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
            print(f"❌ Error adding tag to recipe: {e}")
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
            print(f"❌ Error removing tag from recipe: {e}")
            return False

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
            print(f"❌ Error getting tag by ID: {e}")
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
            print(f"❌ Error getting tag by name: {e}")
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
            print(f"❌ Error getting all tags: {e}")
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
            print(f"❌ Error getting popular tags: {e}")
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
            
            print(f"✅ Tag created: {tag_name} with ID: {tag_id}")
            return tag
            
        except Exception as e:
            print(f"❌ Error creating tag: {e}")
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
            print(f"❌ Error getting recipe count for tag: {e}")
            return 0
    
    def get_recipes(self, limit: int = 20) -> List[Recipe]:
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
            print(f"❌ Error getting recipes for tag: {e}")
            return []

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

# Utility functions for complex operations
def get_trending_recipes(days: int = 7, limit: int = 10) -> List[Recipe]:
    """
    Get trending recipes based on recent likes and favorites
    
    Args:
        days (int): Number of days to look back
        limit (int): Maximum number of recipes to return
        
    Returns:
        List[Recipe]: List of trending recipe instances
    """
    try:
        result = execute_query(
            """SELECT r.*, u.Username as AuthorUsername,
                      (COUNT(DISTINCT l.UserID) + COUNT(DISTINCT f.UserID)) as TrendingScore
               FROM Recipes r
               JOIN Users u ON r.AuthorID = u.UserID
               LEFT JOIN Likes l ON r.RecipeID = l.RecipeID 
                   AND l.CreatedAt >= DATEADD(day, -?, GETDATE())
               LEFT JOIN Favorites f ON r.RecipeID = f.RecipeID 
                   AND f.CreatedAt >= DATEADD(day, -?, GETDATE())
               GROUP BY r.RecipeID, r.AuthorID, r.Title, r.Description, 
                        r.Ingredients, r.Instructions, r.ImageURL, 
                        r.RawIngredients, r.Servings, r.CreatedAt, u.Username
               ORDER BY TrendingScore DESC, r.CreatedAt DESC""",
            (days, days)
        )
        
        recipes = []
        for row in result[:limit]:
            recipe = Recipe.from_dict(row)
            recipe.author_username = row.get('AuthorUsername')
            recipes.append(recipe)
        
        return recipes
        
    except Exception as e:
        print(f"❌ Error getting trending recipes: {e}")
        return []

def get_recipe_recommendations(user_id: int, limit: int = 10) -> List[Recipe]:
    """
    Get recipe recommendations for a user based on their likes and favorites
    
    Args:
        user_id (int): User ID
        limit (int): Maximum number of recommendations
        
    Returns:
        List[Recipe]: List of recommended recipe instances
    """
    try:
        # Get recipes with similar tags to user's liked/favorited recipes
        result = execute_query(
            """SELECT DISTINCT r.*, u.Username as AuthorUsername
               FROM Recipes r
               JOIN Users u ON r.AuthorID = u.UserID
               JOIN RecipeTags rt ON r.RecipeID = rt.RecipeID
               WHERE rt.TagID IN (
                   SELECT DISTINCT rt2.TagID
                   FROM RecipeTags rt2
                   JOIN Likes l ON rt2.RecipeID = l.RecipeID
                   WHERE l.UserID = ?
                   UNION
                   SELECT DISTINCT rt3.TagID
                   FROM RecipeTags rt3
                   JOIN Favorites f ON rt3.RecipeID = f.RecipeID
                   WHERE f.UserID = ?
               )
               AND r.RecipeID NOT IN (
                   SELECT RecipeID FROM Likes WHERE UserID = ?
                   UNION
                   SELECT RecipeID FROM Favorites WHERE UserID = ?
               )
               AND r.AuthorID != ?
               ORDER BY r.CreatedAt DESC""",
            (user_id, user_id, user_id, user_id, user_id)
        )
        
        recipes = []
        for row in result[:limit]:
            recipe = Recipe.from_dict(row)
            recipe.author_username = row.get('AuthorUsername')
            recipes.append(recipe)
        
        return recipes
        
    except Exception as e:
        print(f"❌ Error getting recipe recommendations: {e}")
        return []

def get_recent_recipes(limit: int = 20) -> List[Recipe]:
    """
    Get most recently created recipes
    
    Args:
        limit (int): Maximum number of recipes to return
        
    Returns:
        List[Recipe]: List of recent recipe instances
    """
    try:
        result = execute_query(
            """SELECT r.*, u.Username as AuthorUsername
               FROM Recipes r
               JOIN Users u ON r.AuthorID = u.UserID
               ORDER BY r.CreatedAt DESC""",
        )
        
        recipes = []
        for row in result[:limit]:
            recipe = Recipe.from_dict(row)
            recipe.author_username = row.get('AuthorUsername')
            recipes.append(recipe)
        
        return recipes
        
    except Exception as e:
        print(f"❌ Error getting recent recipes: {e}")
        return []

def get_user_activity_feed(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get activity feed for a user (their likes, favorites, and recipe creations)
    
    Args:
        user_id (int): User ID
        limit (int): Maximum number of activities to return
        
    Returns:
        List[Dict]: List of activity items with type and data
    """
    try:
        activities = []
        
        # Get user's recipe creations
        recipes = execute_query(
            """SELECT r.*, 'recipe_created' as ActivityType
               FROM Recipes r
               WHERE r.AuthorID = ?
               ORDER BY r.CreatedAt DESC""",
            (user_id,)
        )
        
        for recipe in recipes:
            activities.append({
                "type": "recipe_created",
                "timestamp": recipe['CreatedAt'],
                "data": recipe
            })
        
        # Get user's likes
        likes = execute_query(
            """SELECT r.*, l.CreatedAt as LikedAt, 'recipe_liked' as ActivityType
               FROM Likes l
               JOIN Recipes r ON l.RecipeID = r.RecipeID
               WHERE l.UserID = ?
               ORDER BY l.CreatedAt DESC""",
            (user_id,)
        )
        
        for like in likes:
            activities.append({
                "type": "recipe_liked",
                "timestamp": like['LikedAt'],
                "data": like
            })
        
        # Get user's favorites
        favorites = execute_query(
            """SELECT r.*, f.CreatedAt as FavoritedAt, 'recipe_favorited' as ActivityType
               FROM Favorites f
               JOIN Recipes r ON f.RecipeID = r.RecipeID
               WHERE f.UserID = ?
               ORDER BY f.CreatedAt DESC""",
            (user_id,)
        )
        
        for favorite in favorites:
            activities.append({
                "type": "recipe_favorited",
                "timestamp": favorite['FavoritedAt'],
                "data": favorite
            })
        
        # Sort all activities by timestamp and limit
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:limit]
        
    except Exception as e:
        print(f"❌ Error getting user activity feed: {e}")
        return []

def search_users(query: str, limit: int = 10) -> List[User]:
    """
    Search users by username or bio
    
    Args:
        query (str): Search query
        limit (int): Maximum number of users to return
        
    Returns:
        List[User]: List of user instances
    """
    try:
        result = execute_query(
            """SELECT * FROM Users 
               WHERE Username LIKE ? OR Bio LIKE ?
               ORDER BY Username ASC""",
            (f"%{query}%", f"%{query}%")
        )
        
        users = []
        for row in result[:limit]:
            user = User.from_dict(row)
            users.append(user)
        
        return users
        
    except Exception as e:
        print(f"❌ Error searching users: {e}")
        return []

def get_database_statistics() -> Dict[str, Any]:
    """
    Get comprehensive database statistics
    
    Returns:
        Dict[str, Any]: Database statistics
    """
    try:
        stats = {}
        
        # Basic counts
        stats['total_users'] = execute_scalar("SELECT COUNT(*) FROM Users") or 0
        stats['total_recipes'] = execute_scalar("SELECT COUNT(*) FROM Recipes") or 0
        stats['total_tags'] = execute_scalar("SELECT COUNT(*) FROM Tags") or 0
        stats['total_likes'] = execute_scalar("SELECT COUNT(*) FROM Likes") or 0
        stats['total_favorites'] = execute_scalar("SELECT COUNT(*) FROM Favorites") or 0
        
        # Recent activity (last 7 days)
        stats['recent_users'] = execute_scalar(
            "SELECT COUNT(*) FROM Users WHERE CreatedAt >= DATEADD(day, -7, GETDATE())"
        ) or 0
        
        stats['recent_recipes'] = execute_scalar(
            "SELECT COUNT(*) FROM Recipes WHERE CreatedAt >= DATEADD(day, -7, GETDATE())"
        ) or 0
        
        stats['recent_likes'] = execute_scalar(
            "SELECT COUNT(*) FROM Likes WHERE CreatedAt >= DATEADD(day, -7, GETDATE())"
        ) or 0
        
        # Top stats
        most_active_user = execute_query(
            """SELECT TOP 1 u.Username, COUNT(r.RecipeID) as RecipeCount
               FROM Users u
               LEFT JOIN Recipes r ON u.UserID = r.AuthorID
               GROUP BY u.UserID, u.Username
               ORDER BY RecipeCount DESC""",
            fetch="one"
        )
        
        if most_active_user:
            stats['most_active_user'] = {
                'username': most_active_user[0]['Username'],
                'recipe_count': most_active_user[0]['RecipeCount']
            }
        
        most_popular_tag = execute_query(
            """SELECT TOP 1 t.TagName, COUNT(rt.RecipeID) as RecipeCount
               FROM Tags t
               LEFT JOIN RecipeTags rt ON t.TagID = rt.TagID
               GROUP BY t.TagID, t.TagName
               ORDER BY RecipeCount DESC""",
            fetch="one"
        )
        
        if most_popular_tag:
            stats['most_popular_tag'] = {
                'tag_name': most_popular_tag[0]['TagName'],
                'recipe_count': most_popular_tag[0]['RecipeCount']
            }
        
        return stats
        
    except Exception as e:
        print(f"❌ Error getting database statistics: {e}")
        return {}