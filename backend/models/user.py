from .base_model import BaseModel
from database import execute_query, execute_non_query, execute_scalar, insert_and_get_id
import hashlib
from typing import Optional, List, Dict, Any

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
    
    def get_recipes(self, limit: int = 10) -> List:
        """
        Get all recipes created by this user
        
        Args:
            limit (int): Maximum number of recipes to return
            
        Returns:
            List: List of recipe instances (will be Recipe objects when Recipe model is created)
        """
        if self.userid is None:
            return []
        
        # For now, return empty list until Recipe model is implemented
        # return Recipe.get_by_author(self.userid, limit)
        return []
    
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
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """
        Create User instance from dictionary
        
        Args:
            data (dict): User data dictionary
            
        Returns:
            User: User instance
        """
        user = cls()
        
        # Handle different key formats (case-insensitive)
        for key, value in data.items():
            key_lower = key.lower()
            if key_lower == 'userid':
                user.userid = value
            elif key_lower == 'username':
                user.username = value
            elif key_lower == 'email':
                user.email = value
            elif key_lower == 'passwordhash':
                user.passwordhash = value
            elif key_lower == 'profilepicurl':
                user.profilepicurl = value
            elif key_lower == 'bio':
                user.bio = value
            elif key_lower == 'createdat':
                user.createdat = value
        
        return user
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert User instance to dictionary
        
        Returns:
            Dict[str, Any]: User data dictionary
        """
        return {
            'userid': self.userid,
            'username': self.username,
            'email': self.email,
            'passwordhash': self.passwordhash,
            'profilepicurl': self.profilepicurl,
            'bio': self.bio,
            'createdat': self.createdat
        }
    
    def __str__(self) -> str:
        """String representation of User"""
        return f"User(id={self.userid}, username='{self.username}', email='{self.email}')"
    
    def __repr__(self) -> str:
        """Detailed string representation of User"""
        return self.__str__()