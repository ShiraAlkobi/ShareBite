"""
User Commands - CQRS Write Operations

This module handles all WRITE operations for users.
Commands contain business logic, validation, and side effects.

Key Operations:
- User registration and profile management
- Authentication and password changes
- User relationship management
- Account deactivation/deletion
"""

from typing import Dict, Any, Optional
from database import get_database_cursor, execute_non_query, execute_scalar, insert_and_get_id, execute_query
from datetime import datetime
import hashlib
import re

class BaseCommand:
    """
    Base class for all user commands
    """
    
    def __init__(self):
        self.transaction_active = False
    
    def _log_command(self, command_name: str, params: Any = None):
        """Log command execution for audit trail"""
        print(f"⚡ Executing user command: {command_name} with params: {params}")
    
    def _create_password_hash(self, password: str) -> str:
        """Create secure password hash"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_username(self, username: str) -> bool:
        """Validate username format"""
        # Username must be 3-50 chars, alphanumeric and underscores only
        pattern = r'^[a-zA-Z0-9_]{3,50}$'
        return re.match(pattern, username) is not None

class CreateUserCommand(BaseCommand):
    """
    Command to create a new user account
    """
    
    def execute(self,
                username: str,
                email: str,
                password: str,
                bio: Optional[str] = None,
                profile_pic_url: Optional[str] = None) -> int:
        """
        Create a new user account with validation
        
        Args:
            username (str): Unique username
            email (str): Unique email address
            password (str): Plain text password (will be hashed)
            bio (str): User biography
            profile_pic_url (str): Profile picture URL
            
        Returns:
            int: ID of created user
            
        Raises:
            ValueError: If validation fails
            Exception: If creation fails
        """
        self._log_command("CreateUser", {
            "username": username,
            "email": email
        })
        
        try:
            # Validate input
            self._validate_user_input(username, email, password, bio)
            
            # Check for existing username/email
            self._check_user_uniqueness(username, email)
            
            # Hash password
            password_hash = self._create_password_hash(password)
            
            with get_database_cursor() as cursor:
                # Create user
                user_id = insert_and_get_id(
                    "Users",
                    ["Username", "Email", "PasswordHash", "Bio", "ProfilePicURL"],
                    (username.lower().strip(), email.lower().strip(), password_hash, 
                     bio, profile_pic_url)
                )
                
                # Log creation event
                self._log_user_creation_event(user_id, username, email)
                
                print(f"✅ User created successfully with ID: {user_id}")
                return user_id
                
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            raise Exception(f"Failed to create user: {str(e)}")
    
    def _validate_user_input(self, username: str, email: str, password: str, bio: Optional[str]):
        """Validate user input data"""
        
        # Username validation
        if not username or not username.strip():
            raise ValueError("Username is required")
        
        if not self._validate_username(username.strip()):
            raise ValueError("Username must be 3-50 characters and contain only letters, numbers, and underscores")
        
        # Email validation
        if not email or not email.strip():
            raise ValueError("Email is required")
        
        if not self._validate_email(email.strip()):
            raise ValueError("Invalid email format")
        
        # Password validation
        if not password:
            raise ValueError("Password is required")
        
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        
        if len(password) > 128:
            raise ValueError("Password cannot exceed 128 characters")
        
        # Bio validation
        if bio and len(bio) > 500:
            raise ValueError("Bio cannot exceed 500 characters")
        
        # Check for inappropriate content
        forbidden_words = ["admin", "root", "system", "test"]
        if username.lower() in forbidden_words:
            raise ValueError("Username not allowed")
    
    def _check_user_uniqueness(self, username: str, email: str):
        """Check if username and email are unique"""
        
        # Check username
        existing_username = execute_scalar(
            "SELECT COUNT(*) FROM Users WHERE Username = ?",
            (username.lower().strip(),)
        )
        
        if existing_username and existing_username > 0:
            raise ValueError(f"Username '{username}' is already taken")
        
        # Check email
        existing_email = execute_scalar(
            "SELECT COUNT(*) FROM Users WHERE Email = ?",
            (email.lower().strip(),)
        )
        
        if existing_email and existing_email > 0:
            raise ValueError(f"Email '{email}' is already registered")
    
    def _log_user_creation_event(self, user_id: int, username: str, email: str):
        """Log user creation for audit trail"""
        try:
            print(f"📊 EVENT: User {user_id} '{username}' created with email '{email}' at {datetime.now()}")
        except Exception as e:
            print(f"⚠️ Error logging user creation event: {e}")

class UpdateUserCommand(BaseCommand):
    """
    Command to update user profile
    """
    
    def execute(self,
                user_id: int,
                username: Optional[str] = None,
                email: Optional[str] = None,
                bio: Optional[str] = None,
                profile_pic_url: Optional[str] = None) -> bool:
        """
        Update user profile information
        
        Args:
            user_id (int): User ID to update
            username (str): New username
            email (str): New email
            bio (str): New bio
            profile_pic_url (str): New profile picture URL
            
        Returns:
            bool: True if update successful
            
        Raises:
            ValueError: If validation fails
            Exception: If update fails
        """
        self._log_command("UpdateUser", {
            "user_id": user_id,
            "updating_username": username is not None,
            "updating_email": email is not None
        })
        
        try:
            # Check if user exists
            existing_user = execute_query(
                "SELECT Username, Email FROM Users WHERE UserID = ?",
                (user_id,),
                fetch="one"
            )
            
            if not existing_user:
                raise ValueError(f"User with ID {user_id} does not exist")
            
            # Validate updates
            if username is not None:
                if not self._validate_username(username.strip()):
                    raise ValueError("Invalid username format")
                
                # Check uniqueness (excluding current user)
                existing_username = execute_scalar(
                    "SELECT COUNT(*) FROM Users WHERE Username = ? AND UserID != ?",
                    (username.lower().strip(), user_id)
                )
                
                if existing_username and existing_username > 0:
                    raise ValueError(f"Username '{username}' is already taken")
            
            if email is not None:
                if not self._validate_email(email.strip()):
                    raise ValueError("Invalid email format")
                
                # Check uniqueness (excluding current user)
                existing_email = execute_scalar(
                    "SELECT COUNT(*) FROM Users WHERE Email = ? AND UserID != ?",
                    (email.lower().strip(), user_id)
                )
                
                if existing_email and existing_email > 0:
                    raise ValueError(f"Email '{email}' is already registered")
            
            if bio is not None and len(bio) > 500:
                raise ValueError("Bio cannot exceed 500 characters")
            
            with get_database_cursor() as cursor:
                # Build dynamic update query
                update_fields = []
                params = []
                
                if username is not None:
                    update_fields.append("Username = ?")
                    params.append(username.lower().strip())
                
                if email is not None:
                    update_fields.append("Email = ?")
                    params.append(email.lower().strip())
                
                if bio is not None:
                    update_fields.append("Bio = ?")
                    params.append(bio)
                
                if profile_pic_url is not None:
                    update_fields.append("ProfilePicURL = ?")
                    params.append(profile_pic_url)
                
                if update_fields:
                    query = f"UPDATE Users SET {', '.join(update_fields)} WHERE UserID = ?"
                    params.append(user_id)
                    
                    rows_affected = execute_non_query(query, tuple(params))
                    
                    if rows_affected == 0:
                        raise Exception("User update failed - no rows affected")
                
                # Log update event
                self._log_user_update_event(user_id, update_fields)
                
                print(f"✅ User {user_id} updated successfully")
                return True
                
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            print(f"❌ Error updating user: {e}")
            raise Exception(f"Failed to update user: {str(e)}")
    
    def _log_user_update_event(self, user_id: int, updated_fields: List[str]):
        """Log user update event"""
        try:
            print(f"📊 EVENT: User {user_id} updated fields: {updated_fields} at {datetime.now()}")
        except Exception as e:
            print(f"⚠️ Error logging user update event: {e}")

class ChangePasswordCommand(BaseCommand):
    """
    Command to change user password
    """
    
    def execute(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Change user password with verification
        
        Args:
            user_id (int): User ID
            old_password (str): Current password for verification
            new_password (str): New password
            
        Returns:
            bool: True if password changed successfully
            
        Raises:
            ValueError: If validation fails
            PermissionError: If old password is incorrect
            Exception: If change fails
        """
        self._log_command("ChangePassword", {"user_id": user_id})
        
        try:
            # Validate new password
            if len(new_password) < 6:
                raise ValueError("New password must be at least 6 characters long")
            
            if len(new_password) > 128:
                raise ValueError("New password cannot exceed 128 characters")
            
            # Get current password hash
            current_hash = execute_scalar(
                "SELECT PasswordHash FROM Users WHERE UserID = ?",
                (user_id,)
            )
            
            if not current_hash:
                raise ValueError(f"User with ID {user_id} does not exist")
            
            # Verify old password
            old_password_hash = self._create_password_hash(old_password)
            if old_password_hash != current_hash:
                raise PermissionError("Current password is incorrect")
            
            # Check if new password is different
            new_password_hash = self._create_password_hash(new_password)
            if new_password_hash == current_hash:
                raise ValueError("New password must be different from current password")
            
            # Update password
            rows_affected = execute_non_query(
                "UPDATE Users SET PasswordHash = ? WHERE UserID = ?",
                (new_password_hash, user_id)
            )
            
            if rows_affected == 0:
                raise Exception("Password change failed - no rows affected")
            
            # Log password change event
            self._log_password_change_event(user_id)
            
            print(f"✅ Password changed successfully for user {user_id}")
            return True
            
        except (ValueError, PermissionError):
            raise  # Re-raise validation and permission errors
        except Exception as e:
            print(f"❌ Error changing password: {e}")
            raise Exception(f"Failed to change password: {str(e)}")
    
    def _log_password_change_event(self, user_id: int):
        """Log password change event"""
        try:
            print(f"📊 EVENT: User {user_id} changed password at {datetime.now()}")
        except Exception as e:
            print(f"⚠️ Error logging password change event: {e}")

class DeleteUserCommand(BaseCommand):
    """
    Command to delete user account
    """
    
    def execute(self, user_id: int, password: str) -> bool:
        """
        Delete user account with password verification
        
        Args:
            user_id (int): User ID to delete
            password (str): Password for verification
            
        Returns:
            bool: True if deletion successful
            
        Raises:
            ValueError: If user doesn't exist
            PermissionError: If password is incorrect
            Exception: If deletion fails
        """
        self._log_command("DeleteUser", {"user_id": user_id})
        
        try:
            # Get user data
            user_data = execute_query(
                "SELECT Username, PasswordHash FROM Users WHERE UserID = ?",
                (user_id,),
                fetch="one"
            )
            
            if not user_data:
                raise ValueError(f"User with ID {user_id} does not exist")
            
            username = user_data[0]['Username']
            stored_hash = user_data[0]['PasswordHash']
            
            # Verify password
            password_hash = self._create_password_hash(password)
            if password_hash != stored_hash:
                raise PermissionError("Incorrect password")
            
            with get_database_cursor() as cursor:
                # Delete in correct order due to foreign key constraints
                
                # Note: Based on your schema, User deletion will CASCADE
                # to delete related recipes, and recipes will CASCADE to 
                # delete likes, favorites, and recipe tags
                
                # However, we'll be explicit about it
                
                # 1. Get recipes by this user for logging
                user_recipes = execute_query(
                    "SELECT RecipeID, Title FROM Recipes WHERE AuthorID = ?",
                    (user_id,)
                )
                
                # 2. Delete user (CASCADE will handle related data)
                rows_affected = execute_non_query(
                    "DELETE FROM Users WHERE UserID = ?",
                    (user_id,)
                )
                
                if rows_affected == 0:
                    raise Exception("User deletion failed - no rows affected")
                
                # Log deletion event
                self._log_user_deletion_event(user_id, username, len(user_recipes))
                
                print(f"✅ User {user_id} '{username}' deleted successfully")
                print(f"📊 Also deleted {len(user_recipes)} recipes and related data")
                return True
                
        except (ValueError, PermissionError):
            raise  # Re-raise validation and permission errors
        except Exception as e:
            print(f"❌ Error deleting user: {e}")
            raise Exception(f"Failed to delete user: {str(e)}")
    
    def _log_user_deletion_event(self, user_id: int, username: str, recipes_count: int):
        """Log user deletion event"""
        try:
            print(f"📊 EVENT: User {user_id} '{username}' deleted with {recipes_count} recipes at {datetime.now()}")
        except Exception as e:
            print(f"⚠️ Error logging user deletion event: {e}")

class UpdateUserProfilePictureCommand(BaseCommand):
    """
    Command to update user profile picture
    """
    
    def execute(self, user_id: int, new_profile_pic_url: str) -> bool:
        """
        Update user profile picture URL
        
        Args:
            user_id (int): User ID
            new_profile_pic_url (str): New profile picture URL
            
        Returns:
            bool: True if update successful
        """
        self._log_command("UpdateUserProfilePicture", {"user_id": user_id})
        
        try:
            # Check if user exists
            user_exists = execute_scalar(
                "SELECT COUNT(*) FROM Users WHERE UserID = ?",
                (user_id,)
            )
            
            if not user_exists:
                raise ValueError(f"User with ID {user_id} does not exist")
            
            # Update profile picture
            rows_affected = execute_non_query(
                "UPDATE Users SET ProfilePicURL = ? WHERE UserID = ?",
                (new_profile_pic_url, user_id)
            )
            
            if rows_affected == 0:
                raise Exception("Profile picture update failed - no rows affected")
            
            print(f"✅ Profile picture updated for user {user_id}")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            print(f"❌ Error updating profile picture: {e}")
            raise Exception(f"Failed to update profile picture: {str(e)}")

class DeactivateUserCommand(BaseCommand):
    """
    Command to deactivate user account (soft delete alternative)
    """
    
    def execute(self, user_id: int, password: str) -> bool:
        """
        Deactivate user account (alternative to hard delete)
        
        Note: This would require adding an 'IsActive' column to Users table
        For now, we'll simulate with a bio update
        
        Args:
            user_id (int): User ID
            password (str): Password for verification
            
        Returns:
            bool: True if deactivation successful
        """
        self._log_command("DeactivateUser", {"user_id": user_id})
        
        try:
            # Get user data
            user_data = execute_query(
                "SELECT Username, PasswordHash FROM Users WHERE UserID = ?",
                (user_id,),
                fetch="one"
            )
            
            if not user_data:
                raise ValueError(f"User with ID {user_id} does not exist")
            
            stored_hash = user_data[0]['PasswordHash']
            username = user_data[0]['Username']
            
            # Verify password
            password_hash = self._create_password_hash(password)
            if password_hash != stored_hash:
                raise PermissionError("Incorrect password")
            
            # Deactivate by updating bio (in real implementation, use IsActive column)
            deactivation_marker = f"[DEACTIVATED-{datetime.now().strftime('%Y%m%d')}]"
            
            rows_affected = execute_non_query(
                "UPDATE Users SET Bio = ? WHERE UserID = ?",
                (deactivation_marker, user_id)
            )
            
            if rows_affected == 0:
                raise Exception("User deactivation failed - no rows affected")
            
            print(f"✅ User {user_id} '{username}' deactivated successfully")
            return True
            
        except (ValueError, PermissionError):
            raise
        except Exception as e:
            print(f"❌ Error deactivating user: {e}")
            raise Exception(f"Failed to deactivate user: {str(e)}")

class ResetPasswordCommand(BaseCommand):
    """
    Command to reset user password (admin function or forgot password)
    """
    
    def execute(self, email: str, new_password: str) -> bool:
        """
        Reset password for user by email
        
        Args:
            email (str): User email
            new_password (str): New password
            
        Returns:
            bool: True if reset successful
            
        Note: In production, this should require email verification
        """
        self._log_command("ResetPassword", {"email": email})
        
        try:
            # Validate new password
            if len(new_password) < 6:
                raise ValueError("New password must be at least 6 characters long")
            
            # Find user by email
            user_data = execute_query(
                "SELECT UserID, Username FROM Users WHERE Email = ?",
                (email.lower().strip(),),
                fetch="one"
            )
            
            if not user_data:
                raise ValueError(f"No user found with email '{email}'")
            
            user_id = user_data[0]['UserID']
            username = user_data[0]['Username']
            
            # Hash new password
            new_password_hash = self._create_password_hash(new_password)
            
            # Update password
            rows_affected = execute_non_query(
                "UPDATE Users SET PasswordHash = ? WHERE UserID = ?",
                (new_password_hash, user_id)
            )
            
            if rows_affected == 0:
                raise Exception("Password reset failed - no rows affected")
            
            # Log password reset event
            print(f"📊 EVENT: Password reset for user {user_id} '{username}' at {datetime.now()}")
            print(f"✅ Password reset successfully for user {username}")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            print(f"❌ Error resetting password: {e}")
            raise Exception(f"Failed to reset password: {str(e)}")

class BulkUpdateUsersCommand(BaseCommand):
    """
    Command for bulk user operations (admin function)
    """
    
    def execute(self, user_updates: Dict[int, Dict[str, Any]]) -> Dict[int, bool]:
        """
        Update multiple users at once
        
        Args:
            user_updates (Dict): {user_id: {field: new_value}}
            
        Returns:
            Dict: {user_id: success_status}
        """
        self._log_command("BulkUpdateUsers", {
            "user_count": len(user_updates)
        })
        
        results = {}
        
        try:
            with get_database_cursor() as cursor:
                for user_id, updates in user_updates.items():
                    try:
                        # Use individual update command for each user
                        update_command = UpdateUserCommand()
                        success = update_command.execute(
                            user_id=user_id,
                            username=updates.get('username'),
                            email=updates.get('email'),
                            bio=updates.get('bio'),
                            profile_pic_url=updates.get('profile_pic_url')
                        )
                        results[user_id] = success
                        
                    except Exception as e:
                        print(f"❌ Error updating user {user_id}: {e}")
                        results[user_id] = False
                
                successful_updates = sum(1 for success in results.values() if success)
                print(f"✅ Bulk user update: {successful_updates}/{len(user_updates)} users updated")
                
                return results
                
        except Exception as e:
            print(f"❌ Error in bulk user update: {e}")
            raise Exception(f"Bulk user update failed: {str(e)}")

class ValidateUserCredentialsCommand(BaseCommand):
    """
    Command to validate user login credentials
    """
    
    def execute(self, username_or_email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Validate user credentials for login
        
        Args:
            username_or_email (str): Username or email
            password (str): Password
            
        Returns:
            Optional[Dict]: User data if valid, None if invalid
        """
        self._log_command("ValidateUserCredentials", {"identifier": username_or_email})
        
        try:
            # Try to find user by username or email
            user_data = execute_query(
                """SELECT UserID, Username, Email, PasswordHash, ProfilePicURL, Bio, CreatedAt
                   FROM Users 
                   WHERE Username = ? OR Email = ?""",
                (username_or_email.lower().strip(), username_or_email.lower().strip()),
                fetch="one"
            )
            
            if not user_data:
                print(f"❌ No user found with identifier: {username_or_email}")
                return None
            
            user = user_data[0]
            stored_hash = user['PasswordHash']
            
            # Verify password
            password_hash = self._create_password_hash(password)
            if password_hash != stored_hash:
                print(f"❌ Invalid password for user: {user['Username']}")
                return None
            
            # Remove password hash from returned data
            user_info = {
                'UserID': user['UserID'],
                'Username': user['Username'],
                'Email': user['Email'],
                'ProfilePicURL': user['ProfilePicURL'],
                'Bio': user['Bio'],
                'CreatedAt': user['CreatedAt']
            }
            
            # Log successful login
            print(f"📊 EVENT: User {user['UserID']} '{user['Username']}' logged in at {datetime.now()}")
            print(f"✅ Login successful for user: {user['Username']}")
            
            return user_info
            
        except Exception as e:
            print(f"❌ Error validating credentials: {e}")
            return None

class UpdateUserLastLoginCommand(BaseCommand):
    """
    Command to update user's last login timestamp
    """
    
    def execute(self, user_id: int) -> bool:
        """
        Update user's last login time
        
        Note: This would require adding a 'LastLoginAt' column to Users table
        For now, we'll just log it
        
        Args:
            user_id (int): User ID
            
        Returns:
            bool: True if successful
        """
        self._log_command("UpdateUserLastLogin", {"user_id": user_id})
        
        try:
            # In a real implementation, you'd do:
            # execute_non_query(
            #     "UPDATE Users SET LastLoginAt = GETDATE() WHERE UserID = ?",
            #     (user_id,)
            # )
            
            # For now, just log it
            print(f"📊 EVENT: User {user_id} last login updated to {datetime.now()}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating last login: {e}")
            return False

class CleanupInactiveUsersCommand(BaseCommand):
    """
    Command to clean up inactive user accounts (admin function)
    """
    
    def execute(self, days_inactive: int = 365) -> Dict[str, int]:
        """
        Clean up users who haven't been active for specified days
        
        Args:
            days_inactive (int): Days of inactivity threshold
            
        Returns:
            Dict: Statistics about cleanup
        """
        self._log_command("CleanupInactiveUsers", {"days_inactive": days_inactive})
        
        try:
            # Find inactive users (no recipes, likes, or favorites in X days)
            inactive_users = execute_query(
                """SELECT u.UserID, u.Username, u.CreatedAt
                   FROM Users u
                   WHERE u.UserID NOT IN (
                       SELECT DISTINCT AuthorID FROM Recipes 
                       WHERE CreatedAt >= DATEADD(day, -?, GETDATE())
                       UNION
                       SELECT DISTINCT UserID FROM Likes 
                       WHERE CreatedAt >= DATEADD(day, -?, GETDATE())
                       UNION
                       SELECT DISTINCT UserID FROM Favorites 
                       WHERE CreatedAt >= DATEADD(day, -?, GETDATE())
                   )
                   AND u.CreatedAt < DATEADD(day, -?, GETDATE())""",
                (days_inactive, days_inactive, days_inactive, days_inactive)
            )
            
            cleanup_stats = {
                "users_found": len(inactive_users),
                "users_deactivated": 0,
                "users_deleted": 0
            }
            
            for user in inactive_users:
                try:
                    # For safety, we'll deactivate rather than delete
                    # In production, you might want admin approval
                    deactivate_command = DeactivateUserCommand()
                    # Note: This requires password, so in practice you'd need a different approach
                    # For now, just mark them in bio
                    
                    execute_non_query(
                        "UPDATE Users SET Bio = ? WHERE UserID = ?",
                        (f"[INACTIVE-CLEANUP-{datetime.now().strftime('%Y%m%d')}]", user['UserID'])
                    )
                    
                    cleanup_stats["users_deactivated"] += 1
                    print(f"📊 Deactivated inactive user: {user['Username']}")
                    
                except Exception as e:
                    print(f"❌ Error deactivating user {user['Username']}: {e}")
            
            print(f"✅ Cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            print(f"❌ Error in cleanup: {e}")
            raise Exception(f"Cleanup failed: {str(e)}")