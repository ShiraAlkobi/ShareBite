"""
Recipe Commands - CQRS Write Operations

This module handles all WRITE operations for recipes.
Commands contain business logic, validation, and side effects.

Key Principles:
- Handle business logic and validation
- Manage transactions and rollbacks
- Trigger events and notifications
- Ensure data consistency
- Can have side effects (unlike queries)

Commands vs Queries:
- Commands: Change data (INSERT/UPDATE/DELETE)
- Queries: Read data (SELECT)
"""

from typing import List, Dict, Any, Optional
from database import get_database_cursor, execute_non_query, execute_scalar, insert_and_get_id, execute_query
from datetime import datetime

class BaseCommand:
    """
    Base class for all commands with common functionality
    """
    
    def __init__(self):
        self.transaction_active = False
    
    def _log_command(self, command_name: str, params: Any = None):
        """Log command execution for audit trail"""
        print(f"⚡ Executing command: {command_name} with params: {params}")
    
    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]):
        """Validate that required fields are present and not empty"""
        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"Required field '{field}' is missing")
            
            if isinstance(data[field], str) and not data[field].strip():
                raise ValueError(f"Required field '{field}' cannot be empty")

class CreateRecipeCommand(BaseCommand):
    """
    Command to create a new recipe
    """
    
    def execute(self, 
                author_id: int,
                title: str,
                description: Optional[str] = None,
                ingredients: Optional[str] = None,
                raw_ingredients: Optional[str] = None,
                instructions: Optional[str] = None,
                servings: Optional[int] = None,
                image_url: Optional[str] = None,
                tags: Optional[List[str]] = None) -> int:
        """
        Create a new recipe with validation and business logic
        
        Args:
            author_id (int): ID of the user creating the recipe
            title (str): Recipe title (required)
            description (str): Recipe description
            ingredients (str): Formatted ingredients with quantities
            raw_ingredients (str): Raw ingredients list
            instructions (str): Cooking instructions
            servings (int): Number of servings
            image_url (str): Recipe image URL
            tags (List[str]): List of tag names
            
        Returns:
            int: ID of the created recipe
            
        Raises:
            ValueError: If validation fails
            Exception: If creation fails
        """
        self._log_command("CreateRecipe", {
            "author_id": author_id,
            "title": title,
            "tags_count": len(tags) if tags else 0
        })
        
        try:
            # Validate required fields
            if not title or not title.strip():
                raise ValueError("Recipe title is required")
            
            if not author_id or author_id <= 0:
                raise ValueError("Valid author ID is required")
            
            # Validate business rules
            self._validate_recipe_business_rules(title, servings, tags)
            
            # Check if author exists
            author_exists = execute_scalar(
                "SELECT COUNT(*) FROM Users WHERE UserID = ?", 
                (author_id,)
            )
            
            if not author_exists:
                raise ValueError(f"Author with ID {author_id} does not exist")
            
            with get_database_cursor() as cursor:
                # Create the recipe
                recipe_id = insert_and_get_id(
                    "Recipes",
                    ["AuthorID", "Title", "Description", "Ingredients", 
                     "Instructions", "ImageURL", "RawIngredients", "Servings"],
                    (author_id, title.strip(), description, ingredients, 
                     instructions, image_url, raw_ingredients, servings)
                )
                
                print(f"✅ Recipe created with ID: {recipe_id}")
                
                # Add tags if provided
                if tags:
                    self._add_tags_to_recipe(recipe_id, tags)
                
                # Log the creation event
                self._log_recipe_creation_event(recipe_id, author_id, title)
                
                return recipe_id
                
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            print(f"❌ Error creating recipe: {e}")
            raise Exception(f"Failed to create recipe: {str(e)}")
    
    def _validate_recipe_business_rules(self, title: str, servings: Optional[int], tags: Optional[List[str]]):
        """Validate business rules for recipe creation"""
        
        # Title validation
        if len(title.strip()) > 100:
            raise ValueError("Recipe title cannot exceed 100 characters")
        
        # Check for spam/inappropriate content (basic example)
        spam_keywords = ["CLICK HERE", "FREE MONEY", "URGENT"]
        if any(keyword in title.upper() for keyword in spam_keywords):
            raise ValueError("Recipe title contains inappropriate content")
        
        # Servings validation
        if servings is not None:
            if servings < 1 or servings > 50:
                raise ValueError("Servings must be between 1 and 50")
        
        # Tags validation
        if tags:
            if len(tags) > 10:
                raise ValueError("Recipe cannot have more than 10 tags")
            
            for tag in tags:
                if len(tag.strip()) > 50:
                    raise ValueError(f"Tag '{tag}' cannot exceed 50 characters")
    
    def _add_tags_to_recipe(self, recipe_id: int, tags: List[str]):
        """Add tags to recipe, creating tags if they don't exist"""
        try:
            for tag_name in tags:
                cleaned_tag = tag_name.strip().lower()
                if not cleaned_tag:
                    continue
                
                # Get or create tag
                tag_id = execute_scalar(
                    "SELECT TagID FROM Tags WHERE TagName = ?", 
                    (cleaned_tag,)
                )
                
                if not tag_id:
                    # Create new tag
                    tag_id = insert_and_get_id(
                        "Tags", 
                        ["TagName"], 
                        (cleaned_tag,)
                    )
                    print(f"📝 Created new tag: {cleaned_tag}")
                
                # Link tag to recipe (avoid duplicates)
                existing_link = execute_scalar(
                    "SELECT COUNT(*) FROM RecipeTags WHERE RecipeID = ? AND TagID = ?",
                    (recipe_id, tag_id)
                )
                
                if not existing_link:
                    execute_non_query(
                        "INSERT INTO RecipeTags (RecipeID, TagID) VALUES (?, ?)",
                        (recipe_id, tag_id)
                    )
                    print(f"🏷️ Added tag '{cleaned_tag}' to recipe {recipe_id}")
                
        except Exception as e:
            print(f"⚠️ Error adding tags: {e}")
            # Don't fail recipe creation if tags fail
    
    def _log_recipe_creation_event(self, recipe_id: int, author_id: int, title: str):
        """Log recipe creation for event sourcing/audit trail"""
        try:
            # This would typically go to an events table
            # For now, we'll just log it
            print(f"📊 EVENT: Recipe {recipe_id} '{title}' created by user {author_id} at {datetime.now()}")
            
            # In a full implementation, you might do:
            # event_data = {
            #     "event_type": "recipe_created",
            #     "recipe_id": recipe_id,
            #     "author_id": author_id,
            #     "title": title,
            #     "timestamp": datetime.now()
            # }
            # Save to RecipeEvents table
            
        except Exception as e:
            print(f"⚠️ Error logging creation event: {e}")

class UpdateRecipeCommand(BaseCommand):
    """
    Command to update an existing recipe
    """
    
    def execute(self, 
                recipe_id: int,
                author_id: int,  # For authorization
                title: Optional[str] = None,
                description: Optional[str] = None,
                ingredients: Optional[str] = None,
                raw_ingredients: Optional[str] = None,
                instructions: Optional[str] = None,
                servings: Optional[int] = None,
                image_url: Optional[str] = None,
                tags: Optional[List[str]] = None) -> bool:
        """
        Update an existing recipe
        
        Args:
            recipe_id (int): ID of recipe to update
            author_id (int): ID of user making the update (for authorization)
            title (str): New title
            description (str): New description
            ingredients (str): New ingredients
            raw_ingredients (str): New raw ingredients
            instructions (str): New instructions
            servings (int): New servings count
            image_url (str): New image URL
            tags (List[str]): New tags list
            
        Returns:
            bool: True if update successful
            
        Raises:
            ValueError: If validation fails
            PermissionError: If user not authorized
            Exception: If update fails
        """
        self._log_command("UpdateRecipe", {
            "recipe_id": recipe_id,
            "author_id": author_id
        })
        
        try:
            # Check if recipe exists and user is authorized
            recipe_data = execute_query(
                "SELECT AuthorID FROM Recipes WHERE RecipeID = ?",
                (recipe_id,),
                fetch="one"
            )
            
            if not recipe_data:
                raise ValueError(f"Recipe with ID {recipe_id} does not exist")
            
            recipe_author_id = recipe_data[0]['AuthorID']
            
            if recipe_author_id != author_id:
                raise PermissionError("You can only update your own recipes")
            
            # Validate updates
            if title is not None:
                if not title.strip():
                    raise ValueError("Recipe title cannot be empty")
                if len(title.strip()) > 100:
                    raise ValueError("Recipe title cannot exceed 100 characters")
            
            if servings is not None:
                if servings < 1 or servings > 50:
                    raise ValueError("Servings must be between 1 and 50")
            
            with get_database_cursor() as cursor:
                # Build dynamic update query
                update_fields = []
                params = []
                
                if title is not None:
                    update_fields.append("Title = ?")
                    params.append(title.strip())
                
                if description is not None:
                    update_fields.append("Description = ?")
                    params.append(description)
                
                if ingredients is not None:
                    update_fields.append("Ingredients = ?")
                    params.append(ingredients)
                
                if raw_ingredients is not None:
                    update_fields.append("RawIngredients = ?")
                    params.append(raw_ingredients)
                
                if instructions is not None:
                    update_fields.append("Instructions = ?")
                    params.append(instructions)
                
                if servings is not None:
                    update_fields.append("Servings = ?")
                    params.append(servings)
                
                if image_url is not None:
                    update_fields.append("ImageURL = ?")
                    params.append(image_url)
                
                if update_fields:
                    query = f"UPDATE Recipes SET {', '.join(update_fields)} WHERE RecipeID = ?"
                    params.append(recipe_id)
                    
                    rows_affected = execute_non_query(query, tuple(params))
                    
                    if rows_affected == 0:
                        raise Exception("Recipe update failed - no rows affected")
                
                # Update tags if provided
                if tags is not None:
                    self._update_recipe_tags(recipe_id, tags)
                
                # Log the update event
                self._log_recipe_update_event(recipe_id, author_id, update_fields)
                
                print(f"✅ Recipe {recipe_id} updated successfully")
                return True
                
        except (ValueError, PermissionError):
            raise  # Re-raise validation and permission errors
        except Exception as e:
            print(f"❌ Error updating recipe: {e}")
            raise Exception(f"Failed to update recipe: {str(e)}")
    
    def _update_recipe_tags(self, recipe_id: int, new_tags: List[str]):
        """Replace all tags for a recipe with new tags"""
        try:
            # Remove existing tags
            execute_non_query(
                "DELETE FROM RecipeTags WHERE RecipeID = ?",
                (recipe_id,)
            )
            
            # Add new tags
            if new_tags:
                create_command = CreateRecipeCommand()
                create_command._add_tags_to_recipe(recipe_id, new_tags)
            
            print(f"🏷️ Updated tags for recipe {recipe_id}")
            
        except Exception as e:
            print(f"⚠️ Error updating tags: {e}")
            raise
    
    def _log_recipe_update_event(self, recipe_id: int, author_id: int, updated_fields: List[str]):
        """Log recipe update event"""
        try:
            print(f"📊 EVENT: Recipe {recipe_id} updated by user {author_id}. Fields: {updated_fields} at {datetime.now()}")
        except Exception as e:
            print(f"⚠️ Error logging update event: {e}")

class DeleteRecipeCommand(BaseCommand):
    """
    Command to delete a recipe
    """
    
    def execute(self, recipe_id: int, author_id: int) -> bool:
        """
        Delete a recipe and all related data
        
        Args:
            recipe_id (int): ID of recipe to delete
            author_id (int): ID of user requesting deletion (for authorization)
            
        Returns:
            bool: True if deletion successful
            
        Raises:
            ValueError: If recipe doesn't exist
            PermissionError: If user not authorized
            Exception: If deletion fails
        """
        self._log_command("DeleteRecipe", {
            "recipe_id": recipe_id,
            "author_id": author_id
        })
        
        try:
            # Check if recipe exists and user is authorized
            recipe_data = execute_query(
                "SELECT AuthorID, Title FROM Recipes WHERE RecipeID = ?",
                (recipe_id,),
                fetch="one"
            )
            
            if not recipe_data:
                raise ValueError(f"Recipe with ID {recipe_id} does not exist")
            
            recipe_author_id = recipe_data[0]['AuthorID']
            recipe_title = recipe_data[0]['Title']
            
            if recipe_author_id != author_id:
                raise PermissionError("You can only delete your own recipes")
            
            with get_database_cursor() as cursor:
                # Delete in correct order due to foreign key constraints
                
                # 1. Delete recipe tags
                execute_non_query(
                    "DELETE FROM RecipeTags WHERE RecipeID = ?",
                    (recipe_id,)
                )
                
                # 2. Delete likes
                execute_non_query(
                    "DELETE FROM Likes WHERE RecipeID = ?",
                    (recipe_id,)
                )
                
                # 3. Delete favorites
                execute_non_query(
                    "DELETE FROM Favorites WHERE RecipeID = ?",
                    (recipe_id,)
                )
                
                # 4. Delete the recipe itself
                rows_affected = execute_non_query(
                    "DELETE FROM Recipes WHERE RecipeID = ?",
                    (recipe_id,)
                )
                
                if rows_affected == 0:
                    raise Exception("Recipe deletion failed - no rows affected")
                
                # Log the deletion event
                self._log_recipe_deletion_event(recipe_id, author_id, recipe_title)
                
                print(f"✅ Recipe {recipe_id} '{recipe_title}' deleted successfully")
                return True
                
        except (ValueError, PermissionError):
            raise  # Re-raise validation and permission errors
        except Exception as e:
            print(f"❌ Error deleting recipe: {e}")
            raise Exception(f"Failed to delete recipe: {str(e)}")
    
    def _log_recipe_deletion_event(self, recipe_id: int, author_id: int, title: str):
        """Log recipe deletion event"""
        try:
            print(f"📊 EVENT: Recipe {recipe_id} '{title}' deleted by user {author_id} at {datetime.now()}")
        except Exception as e:
            print(f"⚠️ Error logging deletion event: {e}")

class AddTagToRecipeCommand(BaseCommand):
    """
    Command to add a tag to a recipe
    """
    
    def execute(self, recipe_id: int, tag_name: str, author_id: int) -> bool:
        """
        Add a tag to a recipe
        
        Args:
            recipe_id (int): Recipe ID
            tag_name (str): Tag name to add
            author_id (int): User ID for authorization
            
        Returns:
            bool: True if successful
        """
        self._log_command("AddTagToRecipe", {
            "recipe_id": recipe_id,
            "tag_name": tag_name
        })
        
        try:
            # Verify recipe exists and user owns it
            recipe_author = execute_scalar(
                "SELECT AuthorID FROM Recipes WHERE RecipeID = ?",
                (recipe_id,)
            )
            
            if not recipe_author:
                raise ValueError(f"Recipe with ID {recipe_id} does not exist")
            
            if recipe_author != author_id:
                raise PermissionError("You can only modify your own recipes")
            
            # Clean and validate tag name
            cleaned_tag = tag_name.strip().lower()
            if not cleaned_tag:
                raise ValueError("Tag name cannot be empty")
            
            if len(cleaned_tag) > 50:
                raise ValueError("Tag name cannot exceed 50 characters")
            
            # Get or create tag
            tag_id = execute_scalar(
                "SELECT TagID FROM Tags WHERE TagName = ?",
                (cleaned_tag,)
            )
            
            if not tag_id:
                tag_id = insert_and_get_id(
                    "Tags",
                    ["TagName"],
                    (cleaned_tag,)
                )
                print(f"📝 Created new tag: {cleaned_tag}")
            
            # Check if already associated
            existing = execute_scalar(
                "SELECT COUNT(*) FROM RecipeTags WHERE RecipeID = ? AND TagID = ?",
                (recipe_id, tag_id)
            )
            
            if existing:
                print(f"🏷️ Tag '{cleaned_tag}' already associated with recipe {recipe_id}")
                return True
            
            # Create association
            execute_non_query(
                "INSERT INTO RecipeTags (RecipeID, TagID) VALUES (?, ?)",
                (recipe_id, tag_id)
            )
            
            print(f"✅ Added tag '{cleaned_tag}' to recipe {recipe_id}")
            return True
            
        except (ValueError, PermissionError):
            raise
        except Exception as e:
            print(f"❌ Error adding tag to recipe: {e}")
            raise Exception(f"Failed to add tag: {str(e)}")

class RemoveTagFromRecipeCommand(BaseCommand):
    """
    Command to remove a tag from a recipe
    """
    
    def execute(self, recipe_id: int, tag_name: str, author_id: int) -> bool:
        """
        Remove a tag from a recipe
        
        Args:
            recipe_id (int): Recipe ID
            tag_name (str): Tag name to remove
            author_id (int): User ID for authorization
            
        Returns:
            bool: True if successful
        """
        self._log_command("RemoveTagFromRecipe", {
            "recipe_id": recipe_id,
            "tag_name": tag_name
        })
        
        try:
            # Verify recipe exists and user owns it
            recipe_author = execute_scalar(
                "SELECT AuthorID FROM Recipes WHERE RecipeID = ?",
                (recipe_id,)
            )
            
            if not recipe_author:
                raise ValueError(f"Recipe with ID {recipe_id} does not exist")
            
            if recipe_author != author_id:
                raise PermissionError("You can only modify your own recipes")
            
            # Remove tag association
            rows_affected = execute_non_query(
                """DELETE FROM RecipeTags 
                   WHERE RecipeID = ? AND TagID = (
                       SELECT TagID FROM Tags WHERE TagName = ?
                   )""",
                (recipe_id, tag_name.strip().lower())
            )
            
            if rows_affected == 0:
                raise ValueError(f"Tag '{tag_name}' not found on recipe")
            
            print(f"✅ Removed tag '{tag_name}' from recipe {recipe_id}")
            return True
            
        except (ValueError, PermissionError):
            raise
        except Exception as e:
            print(f"❌ Error removing tag from recipe: {e}")
            raise Exception(f"Failed to remove tag: {str(e)}")

class ToggleLikeCommand(BaseCommand):
    """
    Command to toggle like on a recipe
    """
    
    def execute(self, user_id: int, recipe_id: int) -> Dict[str, Any]:
        """
        Toggle like status on a recipe
        
        Args:
            user_id (int): User ID
            recipe_id (int): Recipe ID
            
        Returns:
            Dict: {"is_liked": bool, "total_likes": int}
        """
        self._log_command("ToggleLike", {
            "user_id": user_id,
            "recipe_id": recipe_id
        })
        
        try:
            # Verify recipe exists
            recipe_exists = execute_scalar(
                "SELECT COUNT(*) FROM Recipes WHERE RecipeID = ?",
                (recipe_id,)
            )
            
            if not recipe_exists:
                raise ValueError(f"Recipe with ID {recipe_id} does not exist")
            
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
                action = "removed"
            else:
                # Add like
                execute_non_query(
                    "INSERT INTO Likes (UserID, RecipeID) VALUES (?, ?)",
                    (user_id, recipe_id)
                )
                new_status = True
                action = "added"
            
            # Get updated total likes
            total_likes = execute_scalar(
                "SELECT COUNT(*) FROM Likes WHERE RecipeID = ?",
                (recipe_id,)
            ) or 0
            
            print(f"✅ Like {action} for recipe {recipe_id} by user {user_id}")
            
            return {
                "is_liked": new_status,
                "total_likes": total_likes
            }
            
        except ValueError:
            raise
        except Exception as e:
            print(f"❌ Error toggling like: {e}")
            raise Exception(f"Failed to toggle like: {str(e)}")

class ToggleFavoriteCommand(BaseCommand):
    """
    Command to toggle favorite on a recipe
    """
    
    def execute(self, user_id: int, recipe_id: int) -> Dict[str, Any]:
        """
        Toggle favorite status on a recipe
        
        Args:
            user_id (int): User ID
            recipe_id (int): Recipe ID
            
        Returns:
            Dict: {"is_favorited": bool, "total_favorites": int}
        """
        self._log_command("ToggleFavorite", {
            "user_id": user_id,
            "recipe_id": recipe_id
        })
        
        try:
            # Verify recipe exists
            recipe_exists = execute_scalar(
                "SELECT COUNT(*) FROM Recipes WHERE RecipeID = ?",
                (recipe_id,)
            )
            
            if not recipe_exists:
                raise ValueError(f"Recipe with ID {recipe_id} does not exist")
            
            # Check current favorite status
            is_favorited = execute_scalar(
                "SELECT COUNT(*) FROM Favorites WHERE UserID = ? AND RecipeID = ?",
                (user_id, recipe_id)
            ) > 0
            
            if is_favorited:
                # Remove favorite
                execute_non_query(
                    "DELETE FROM Favorites WHERE UserID = ? AND RecipeID = ?",
                    (user_id, recipe_id)
                )
                new_status = False
                action = "removed"
            else:
                # Add favorite
                execute_non_query(
                    "INSERT INTO Favorites (UserID, RecipeID) VALUES (?, ?)",
                    (user_id, recipe_id)
                )
                new_status = True
                action = "added"
            
            # Get updated total favorites
            total_favorites = execute_scalar(
                "SELECT COUNT(*) FROM Favorites WHERE RecipeID = ?",
                (recipe_id,)
            ) or 0
            
            print(f"✅ Favorite {action} for recipe {recipe_id} by user {user_id}")
            
            return {
                "is_favorited": new_status,
                "total_favorites": total_favorites
            }
            
        except ValueError:
            raise
        except Exception as e:
            print(f"❌ Error toggling favorite: {e}")
            raise Exception(f"Failed to toggle favorite: {str(e)}")

class BulkUpdateRecipeTagsCommand(BaseCommand):
    """
    Command to update multiple recipes' tags at once
    """
    
    def execute(self, author_id: int, recipe_tags_map: Dict[int, List[str]]) -> Dict[int, bool]:
        """
        Update tags for multiple recipes at once
        
        Args:
            author_id (int): User ID for authorization
            recipe_tags_map (Dict): {recipe_id: [tag_names]}
            
        Returns:
            Dict: {recipe_id: success_status}
        """
        self._log_command("BulkUpdateRecipeTags", {
            "author_id": author_id,
            "recipe_count": len(recipe_tags_map)
        })
        
        results = {}
        
        try:
            with get_database_cursor() as cursor:
                for recipe_id, tags in recipe_tags_map.items():
                    try:
                        # Verify ownership
                        recipe_author = execute_scalar(
                            "SELECT AuthorID FROM Recipes WHERE RecipeID = ?",
                            (recipe_id,)
                        )
                        
                        if recipe_author != author_id:
                            results[recipe_id] = False
                            continue
                        
                        # Update tags
                        update_command = UpdateRecipeCommand()
                        update_command._update_recipe_tags(recipe_id, tags)
                        results[recipe_id] = True
                        
                    except Exception as e:
                        print(f"❌ Error updating tags for recipe {recipe_id}: {e}")
                        results[recipe_id] = False
                
                successful_updates = sum(1 for success in results.values() if success)
                print(f"✅ Bulk tag update: {successful_updates}/{len(recipe_tags_map)} recipes updated")
                
                return results
                
        except Exception as e:
            print(f"❌ Error in bulk tag update: {e}")
            raise Exception(f"Bulk tag update failed: {str(e)}")

class CloneRecipeCommand(BaseCommand):
    """
    Command to clone/duplicate a recipe
    """
    
    def execute(self, original_recipe_id: int, new_author_id: int, new_title: Optional[str] = None) -> int:
        """
        Clone an existing recipe for a new author
        
        Args:
            original_recipe_id (int): ID of recipe to clone
            new_author_id (int): ID of user creating the clone
            new_title (str): Optional new title (default: "Copy of [Original Title]")
            
        Returns:
            int: ID of the cloned recipe
        """
        self._log_command("CloneRecipe", {
            "original_recipe_id": original_recipe_id,
            "new_author_id": new_author_id
        })
        
        try:
            # Get original recipe data
            original_recipe = execute_query(
                """SELECT Title, Description, Ingredients, Instructions, 
                          RawIngredients, Servings FROM Recipes WHERE RecipeID = ?""",
                (original_recipe_id,),
                fetch="one"
            )
            
            if not original_recipe:
                raise ValueError(f"Recipe with ID {original_recipe_id} does not exist")
            
            recipe_data = original_recipe[0]
            
            # Set new title
            if not new_title:
                new_title = f"Copy of {recipe_data['Title']}"
            
            # Get original tags
            original_tags = execute_query(
                """SELECT t.TagName FROM Tags t
                   JOIN RecipeTags rt ON t.TagID = rt.TagID
                   WHERE rt.RecipeID = ?""",
                (original_recipe_id,)
            )
            
            tag_names = [tag['TagName'] for tag in original_tags] if original_tags else []
            
            # Create the cloned recipe
            create_command = CreateRecipeCommand()
            cloned_recipe_id = create_command.execute(
                author_id=new_author_id,
                title=new_title,
                description=recipe_data['Description'],
                ingredients=recipe_data['Ingredients'],
                raw_ingredients=recipe_data['RawIngredients'],
                instructions=recipe_data['Instructions'],
                servings=recipe_data['Servings'],
                tags=tag_names
            )
            
            print(f"✅ Recipe {original_recipe_id} cloned as recipe {cloned_recipe_id}")
            return cloned_recipe_id
            
        except ValueError:
            raise
        except Exception as e:
            print(f"❌ Error cloning recipe: {e}")
            raise Exception(f"Failed to clone recipe: {str(e)}")