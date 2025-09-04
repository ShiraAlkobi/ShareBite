from .base_model import BaseModel
from database import execute_query, execute_non_query, execute_scalar, insert_and_get_id
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

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
        if not isinstance(password, str):
            print(f"Warning: Password is not a string, type: {type(password)}")
            password = str(password)
        
        hash_result = hashlib.sha256(password.encode()).hexdigest()
        print(f"Hash function: input='{password}' -> output='{hash_result[:20]}...'")
        return hash_result
    
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
            print(f"Error getting user by ID: {e}")
            return None
    
    @classmethod
    def get_by_username(cls, username: str) -> Optional[dict]:
        """Get user by username from database - returns dict for auth compatibility"""
        try:
            print(f"Searching for user: '{username}'")
            result = execute_query(
                "SELECT UserID, Username, Email, PasswordHash, ProfilePicURL, Bio, CreatedAt FROM Users WHERE Username = ?", 
                (username,), 
                fetch="one"
            )
            
            print(f"Raw database result: {result}")
            print(f"Result type: {type(result)}")
            
            if result and len(result) > 0:
                # Your execute_query returns a list of dictionaries
                if isinstance(result, list) and len(result) > 0:
                    row = result[0]  # Get first result
                    
                    # Check if it's a dictionary (your format) or tuple
                    if isinstance(row, dict):
                        print(f"Processing dictionary row: {dict(row, PasswordHash='***HIDDEN***')}")
                        
                        user_dict = {
                            'userid': int(row['UserID']),
                            'username': str(row['Username']) if row['Username'] else None,
                            'email': str(row['Email']) if row['Email'] else None,
                            'passwordhash': str(row['PasswordHash']) if row['PasswordHash'] else None,
                            'profilepicurl': str(row['ProfilePicURL']) if row['ProfilePicURL'] else None,
                            'bio': str(row['Bio']) if row['Bio'] else None,
                            'createdat': row['CreatedAt']
                        }
                    else:
                        # Handle tuple format (if your DB returns tuples)
                        print(f"Processing tuple row: {row}")
                        user_dict = {
                            'userid': int(row[0]),
                            'username': str(row[1]) if row[1] else None,
                            'email': str(row[2]) if row[2] else None,
                            'passwordhash': str(row[3]) if row[3] else None,
                            'profilepicurl': str(row[4]) if row[4] else None,
                            'bio': str(row[5]) if row[5] else None,
                            'createdat': row[6]
                        }
                    
                    print(f"Created user dict: {dict(user_dict, passwordhash='***HIDDEN***')}")
                    return user_dict
                
            print(f"No user found with username: '{username}'")
            return None
            
        except Exception as e:
            print(f"Error getting user by username: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @classmethod
    def get_by_email(cls, email: str) -> Optional[dict]:
        """Get user by email from database - returns dict for auth compatibility"""
        try:
            result = execute_query(
                "SELECT UserID, Username, Email, PasswordHash, ProfilePicURL, Bio, CreatedAt FROM Users WHERE Email = ?", 
                (email,), 
                fetch="one"
            )
            
            if result and len(result) > 0:
                row = result[0]  # Get first result
                
                if isinstance(row, dict):
                    return {
                        'userid': int(row['UserID']),
                        'username': str(row['Username']) if row['Username'] else None,
                        'email': str(row['Email']) if row['Email'] else None,
                        'passwordhash': str(row['PasswordHash']) if row['PasswordHash'] else None,
                        'profilepicurl': str(row['ProfilePicURL']) if row['ProfilePicURL'] else None,
                        'bio': str(row['Bio']) if row['Bio'] else None,
                        'createdat': row['CreatedAt']
                    }
                else:
                    # Handle tuple format
                    return {
                        'userid': int(row[0]),
                        'username': str(row[1]) if row[1] else None,
                        'email': str(row[2]) if row[2] else None,
                        'passwordhash': str(row[3]) if row[3] else None,
                        'profilepicurl': str(row[4]) if row[4] else None,
                        'bio': str(row[5]) if row[5] else None,
                        'createdat': row[6]
                    }
            return None
            
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    @classmethod
    def get_user_by_id_dict(cls, user_id: int) -> Optional[dict]:
        """Get user by ID from database - returns dict for auth compatibility"""
        try:
            result = execute_query(
                "SELECT UserID, Username, Email, PasswordHash, ProfilePicURL, Bio, CreatedAt FROM Users WHERE UserID = ?", 
                (user_id,), 
                fetch="one"
            )
            
            if result and len(result) > 0:
                row = result[0]  # Get first result
                
                if isinstance(row, dict):
                    return {
                        'userid': int(row['UserID']),
                        'username': str(row['Username']) if row['Username'] else None,
                        'email': str(row['Email']) if row['Email'] else None,
                        'passwordhash': str(row['PasswordHash']) if row['PasswordHash'] else None,
                        'profilepicurl': str(row['ProfilePicURL']) if row['ProfilePicURL'] else None,
                        'bio': str(row['Bio']) if row['Bio'] else None,
                        'createdat': row['CreatedAt']
                    }
                else:
                    # Handle tuple format
                    return {
                        'userid': int(row[0]),
                        'username': str(row[1]) if row[1] else None,
                        'email': str(row[2]) if row[2] else None,
                        'passwordhash': str(row[3]) if row[3] else None,
                        'profilepicurl': str(row[4]) if row[4] else None,
                        'bio': str(row[5]) if row[5] else None,
                        'createdat': row[6]
                    }
            return None
            
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    @classmethod
    def create_user(cls, username: str, email: str, password: str, bio: str = None) -> Optional[int]:
        """
        Create a new user in the database
        
        Args:
            username (str): Username
            email (str): Email address
            password (str): Plain text password (will be hashed)
            bio (str): User bio (optional)
            
        Returns:
            Optional[int]: User ID if successful, None otherwise
        """
        try:
            print(f"Creating user in database...")
            print(f"Username: {username}, Email: {email}")
            
            # Create password hash
            password_hash = cls.create_password_hash(password)
            print(f"Generated password hash: {password_hash}")
            print(f"Password hash length: {len(password_hash)}")
            
            # Clean bio field - handle None and empty strings
            bio_value = None
            if bio and bio.strip():
                bio_value = bio.strip()
            
            print(f"Bio value: {bio_value}")
            print(f"About to insert - Username: {username}, Email: {email}")
            
            # Log the exact values being inserted
            insert_values = (username, email, password_hash, None, bio_value)
            print(f"Insert values: {[str(v) if v is not None else None for v in insert_values]}")
            print(f"Insert value types: {[type(v) for v in insert_values]}")
            
            user_id = insert_and_get_id(
                "Users",
                ["Username", "Email", "PasswordHash", "ProfilePicURL", "Bio"],
                insert_values
            )
            print(f"Raw user_id from database: {user_id} (type: {type(user_id)})")
            
            if not user_id:
                print(f"Failed to create user in database")
                return None
            
            # Convert user_id to int if it's a Decimal
            if hasattr(user_id, '__int__'):
                user_id = int(user_id)
            print(f"User created with ID: {user_id} (type: {type(user_id)})")
            
            # VERIFICATION: Immediately test if we can retrieve the user and verify password
            print(f"VERIFICATION: Testing immediate password verification...")
            test_user = cls.get_by_username(username)
            if test_user:
                test_hash = cls.create_password_hash(password)
                verification_result = test_user['passwordhash'] == test_hash
                print(f"VERIFICATION: User retrieved: ✅")
                print(f"VERIFICATION: Stored hash: {test_user['passwordhash']}")
                print(f"VERIFICATION: Test hash: {test_hash}")
                print(f"VERIFICATION: Hashes match: {verification_result}")
                if not verification_result:
                    print(f"WARNING: Password verification failed immediately after registration!")
            else:
                print(f"VERIFICATION: Could not retrieve user immediately after creation!")
            
            return user_id
            
        except Exception as e:
            print(f"Database insertion error: {e}")
            import traceback
            traceback.print_exc()
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
            print(f"Error getting all users: {e}")
            return []
    
    # ============= NEW METHODS FROM USER_ROUTES =============
    
    @classmethod
    def get_profile_data(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user profile information by ID
        
        Args:
            user_id (int): User ID
            
        Returns:
            Optional[Dict]: User profile data or None if not found
        """
        try:
            user_data = execute_query(
                """SELECT UserID, Username, Email, ProfilePicURL, Bio, CreatedAt
                   FROM Users WHERE UserID = ?""",
                (user_id,),
                fetch="one"
            )
            
            if not user_data or len(user_data) == 0:
                return None
            
            return user_data[0]
            
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    @classmethod
    def get_user_stats(cls, user_id: int) -> Dict[str, int]:
        """Get user statistics"""
        try:
            recipes_count = execute_scalar(
                "SELECT COUNT(*) FROM Recipes WHERE AuthorID = ?", 
                (user_id,)
            ) or 0
            
            total_likes = execute_scalar(
                """SELECT COUNT(*) FROM Likes l
                   JOIN Recipes r ON l.RecipeID = r.RecipeID
                   WHERE r.AuthorID = ?""",
                (user_id,)
            ) or 0
            
            total_favorites = execute_scalar(
                """SELECT COUNT(*) FROM Favorites f
                   JOIN Recipes r ON f.RecipeID = r.RecipeID
                   WHERE r.AuthorID = ?""",
                (user_id,)
            ) or 0
            
            return {
                "recipes_count": recipes_count,
                "total_likes_received": total_likes,
                "total_favorites_received": total_favorites
            }
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {
                "recipes_count": 0,
                "total_likes_received": 0,
                "total_favorites_received": 0
            }
    
    @classmethod
    def update_profile(cls, user_id: int, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user profile information
        
        Args:
            user_id (int): User ID
            profile_data (Dict): Profile data to update
            
        Returns:
            Dict: Result with updated user data or error info
        """
        try:
            # Build dynamic update query
            update_fields = []
            params = []
            updated_field_names = []
            
            if profile_data.get('username') is not None:
                # Check username uniqueness
                existing = execute_scalar(
                    "SELECT COUNT(*) FROM Users WHERE Username = ? AND UserID != ?",
                    (profile_data['username'], user_id)
                )
                if existing and existing > 0:
                    return {"error": "Username already taken"}
                
                update_fields.append("Username = ?")
                params.append(profile_data['username'])
                updated_field_names.append("username")
            
            if profile_data.get('email') is not None:
                # Check email uniqueness
                existing = execute_scalar(
                    "SELECT COUNT(*) FROM Users WHERE Email = ? AND UserID != ?",
                    (str(profile_data['email']), user_id)
                )
                if existing and existing > 0:
                    return {"error": "Email already taken"}
                
                update_fields.append("Email = ?")
                params.append(str(profile_data['email']))
                updated_field_names.append("email")
            
            if profile_data.get('bio') is not None:
                update_fields.append("Bio = ?")
                params.append(profile_data['bio'])
                updated_field_names.append("bio")
            
            if profile_data.get('profile_pic_url') is not None:
                update_fields.append("ProfilePicURL = ?")
                params.append(profile_data['profile_pic_url'])
                updated_field_names.append("profile_pic_url")
            
            if not update_fields:
                return {"error": "No fields to update"}
            
            # Execute update
            query = f"UPDATE Users SET {', '.join(update_fields)} WHERE UserID = ?"
            params.append(user_id)
            
            rows_affected = execute_non_query(query, tuple(params))
            
            if rows_affected == 0:
                return {"error": "User not found"}
            
            # Get updated user data
            updated_user = execute_query(
                """SELECT UserID, Username, Email, ProfilePicURL, Bio, CreatedAt
                   FROM Users WHERE UserID = ?""",
                (user_id,),
                fetch="one"
            )[0]
            
            return {
                "success": True,
                "updated_fields": updated_field_names,
                "user": updated_user
            }
            
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return {"error": "Failed to update profile"}
    
    @classmethod
    def log_user_event(cls, user_id: int, action_type: str, event_data: Dict = None):
        """
        Log a user event to the RecipeEvents table for event sourcing
        Note: We use recipe_id = 0 for user-related events since it's not recipe-specific
        
        Args:
            user_id (int): ID of the user performing the action
            action_type (str): Type of action (UserRegistered, UserUpdated, UserLoggedIn, etc.)
            event_data (Dict): Additional data to store as JSON
        """
        try:
            # Convert event_data to JSON string if provided
            event_data_json = json.dumps(event_data) if event_data else None
            
            # Insert event into RecipeEvents table (using RecipeID = 0 for user events)
            execute_non_query(
                """INSERT INTO RecipeEvents (RecipeID, UserID, ActionType, EventData) 
                   VALUES (?, ?, ?, ?)""",
                (0, user_id, action_type, event_data_json)
            )
            
            print(f"User event logged: {action_type} - User {user_id}")
            
        except Exception as e:
            print(f"Failed to log user event: {e}")
            # Don't raise exception - event logging failure shouldn't break the main operation
    
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
                print(f"User created with ID: {user_id}")
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
                print(f"User updated, {rows_affected} rows affected")
                return rows_affected > 0
                
        except Exception as e:
            print(f"Error saving user: {e}")
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
            
            print(f"User deleted, {rows_affected} rows affected")
            return rows_affected > 0
            
        except Exception as e:
            print(f"Error deleting user: {e}")
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
            print(f"Error getting user stats: {e}")
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