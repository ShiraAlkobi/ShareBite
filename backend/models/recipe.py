from .base_model import BaseModel
from database import execute_query, execute_non_query, execute_scalar, insert_and_get_id, get_database_cursor
import hashlib
from typing import List, Optional, TYPE_CHECKING, Dict, Any
from datetime import datetime
import json

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
    
    # ============= NEW METHODS FROM ADD_RECIPE_ROUTES =============
    
    @classmethod
    def create_recipe_with_tags(cls, author_id: int, title: str, description: str = None, 
                               ingredients: str = None, raw_ingredients: str = None,
                               instructions: str = None, servings: int = 4, 
                               image_url: str = None, tags: List[str] = None) -> int:
        """
        Create a new recipe with tags (CQRS-style command execution)
        
        Args:
            author_id (int): Author user ID
            title (str): Recipe title
            description (str): Recipe description
            ingredients (str): Recipe ingredients
            raw_ingredients (str): Raw ingredients
            instructions (str): Recipe instructions
            servings (int): Number of servings
            image_url (str): Image URL
            tags (List[str]): List of tag names
            
        Returns:
            int: New recipe ID
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Validate required fields
            if not title or not title.strip():
                raise ValueError("Recipe title is required")
            
            if not ingredients or not ingredients.strip():
                raise ValueError("Recipe ingredients are required")
            
            if not instructions or not instructions.strip():
                raise ValueError("Recipe instructions are required")
            
            # Create the recipe
            recipe_id = insert_and_get_id(
                "Recipes",
                ["AuthorID", "Title", "Description", "Ingredients", 
                 "Instructions", "ImageURL", "RawIngredients", "Servings"],
                (author_id, title.strip(), description, ingredients, 
                 instructions, image_url, raw_ingredients or ingredients, servings)
            )
            
            # Add tags if provided
            if tags:
                for tag_name in tags:
                    if tag_name and tag_name.strip():
                        cls.add_tag_to_recipe(recipe_id, tag_name.strip(), author_id)
            
            print(f"Recipe created with ID: {recipe_id}")
            return recipe_id
            
        except Exception as e:
            print(f"Error creating recipe: {e}")
            raise
    
    @classmethod
    def add_tag_to_recipe(cls, recipe_id: int, tag_name: str, author_id: int) -> bool:
        """
        Add a tag to a recipe
        
        Args:
            recipe_id (int): Recipe ID
            tag_name (str): Tag name to add
            author_id (int): Author ID (for permission check)
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Validate inputs
            if not tag_name or not tag_name.strip():
                raise ValueError("Tag name cannot be empty")
            
            tag_name = tag_name.strip().lower()
            
            # Check if recipe exists and user owns it
            recipe_author = execute_scalar(
                "SELECT AuthorID FROM Recipes WHERE RecipeID = ?",
                (recipe_id,)
            )
            
            if not recipe_author:
                raise ValueError("Recipe not found")
            
            if recipe_author != author_id:
                raise ValueError("Only the recipe author can add tags")
            
            # Import Tag to avoid circular import
            from .tag import Tag
            
            # Get or create tag
            tag = Tag.get_or_create(tag_name)
            if not tag:
                raise ValueError("Failed to create tag")
            
            # Check if association already exists
            existing = execute_scalar(
                "SELECT COUNT(*) FROM RecipeTags WHERE RecipeID = ? AND TagID = ?",
                (recipe_id, tag.tagid)
            )
            
            if existing > 0:
                print(f"Tag '{tag_name}' already associated with recipe {recipe_id}")
                return True
            
            # Create association
            rows_affected = execute_non_query(
                "INSERT INTO RecipeTags (RecipeID, TagID) VALUES (?, ?)",
                (recipe_id, tag.tagid)
            )
            
            success = rows_affected > 0
            if success:
                print(f"Tag '{tag_name}' added to recipe {recipe_id}")
            
            return success
            
        except Exception as e:
            print(f"Error adding tag to recipe: {e}")
            raise
    
    @classmethod
    def remove_tag_from_recipe(cls, recipe_id: int, tag_name: str, author_id: int) -> bool:
        """
        Remove a tag from a recipe
        
        Args:
            recipe_id (int): Recipe ID
            tag_name (str): Tag name to remove
            author_id (int): Author ID (for permission check)
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Validate inputs
            if not tag_name or not tag_name.strip():
                raise ValueError("Tag name cannot be empty")
            
            tag_name = tag_name.strip().lower()
            
            # Check if recipe exists and user owns it
            recipe_author = execute_scalar(
                "SELECT AuthorID FROM Recipes WHERE RecipeID = ?",
                (recipe_id,)
            )
            
            if not recipe_author:
                raise ValueError("Recipe not found")
            
            if recipe_author != author_id:
                raise ValueError("Only the recipe author can remove tags")
            
            # Remove tag association
            rows_affected = execute_non_query(
                """DELETE FROM RecipeTags 
                   WHERE RecipeID = ? AND TagID = (
                       SELECT TagID FROM Tags WHERE TagName = ?
                   )""",
                (recipe_id, tag_name)
            )
            
            success = rows_affected > 0
            if success:
                print(f"Tag '{tag_name}' removed from recipe {recipe_id}")
            else:
                print(f"Tag '{tag_name}' not found on recipe {recipe_id}")
            
            return success
            
        except Exception as e:
            print(f"Error removing tag from recipe: {e}")
            raise
    
    @classmethod
    def log_recipe_event(cls, recipe_id: int, user_id: int, action_type: str, event_data: Dict = None):
        """
        Log an event to the RecipeEvents table for event sourcing
        
        Args:
            recipe_id (int): ID of the recipe involved
            user_id (int): ID of the user performing the action
            action_type (str): Type of action
            event_data (Dict): Additional data to store as JSON
        """
        try:
            event_data_json = json.dumps(event_data) if event_data else None
            
            execute_non_query(
                """INSERT INTO RecipeEvents (RecipeID, UserID, ActionType, EventData) 
                   VALUES (?, ?, ?, ?)""",
                (recipe_id, user_id, action_type, event_data_json)
            )
            
            print(f"Event logged: {action_type} - Recipe {recipe_id} by User {user_id}")
            
        except Exception as e:
            print(f"Failed to log event: {e}")
    
    # ============= EXISTING METHODS FROM PREVIOUS ROUTES =============
    
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
    
    @classmethod
    def search_recipes_with_filters(cls, user_id: int, query: str = None, category: str = None, 
                                   author: str = None, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        Search recipes with filters and user-specific interaction data
        
        Args:
            user_id (int): Current user ID for interaction data
            query (str): Search query for recipe content
            category (str): Category filter
            author (str): Author filter
            limit (int): Maximum number of results
            offset (int): Number of results to skip
            
        Returns:
            Dict: Search results with metadata
        """
        try:
            # Build search query with user-specific like/favorite status
            base_query = """
            SELECT 
                r.RecipeID,
                r.Title,
                r.Description,
                r.Ingredients,
                r.Instructions,
                r.ImageURL,
                r.RawIngredients,
                r.Servings,
                r.CreatedAt,
                r.AuthorID,
                u.Username as AuthorName,
                (SELECT COUNT(*) FROM Likes WHERE RecipeID = r.RecipeID) as LikesCount,
                CASE WHEN EXISTS(SELECT 1 FROM Likes WHERE RecipeID = r.RecipeID AND UserID = ?) 
                     THEN 1 ELSE 0 END as IsLiked,
                CASE WHEN EXISTS(SELECT 1 FROM Favorites WHERE RecipeID = r.RecipeID AND UserID = ?) 
                     THEN 1 ELSE 0 END as IsFavorited
            FROM Recipes r
            JOIN Users u ON r.AuthorID = u.UserID
            WHERE 1=1
            """
            
            # Build WHERE conditions and parameters
            conditions = []
            params = [user_id, user_id]  # For the IsLiked and IsFavorited subqueries
            
            # Search in multiple fields - Enhanced for multi-word queries
            if query and query.strip():
                search_query = query.strip()
                search_terms = search_query.split()
                
                if len(search_terms) == 1:
                    # Single word search
                    search_condition = """
                    (LOWER(r.Title) LIKE LOWER(?) 
                     OR LOWER(r.Description) LIKE LOWER(?) 
                     OR LOWER(r.Ingredients) LIKE LOWER(?) 
                     OR LOWER(r.RawIngredients) LIKE LOWER(?))
                    """
                    search_term = f"%{search_query}%"
                    conditions.append(search_condition)
                    params.extend([search_term, search_term, search_term, search_term])
                    
                else:
                    # Multi-word search - each word must appear somewhere in the record
                    word_conditions = []
                    for term in search_terms:
                        word_condition = """
                        (LOWER(r.Title) LIKE LOWER(?) 
                         OR LOWER(r.Description) LIKE LOWER(?) 
                         OR LOWER(r.Ingredients) LIKE LOWER(?) 
                         OR LOWER(r.RawIngredients) LIKE LOWER(?))
                        """
                        word_conditions.append(word_condition)
                        word_term = f"%{term}%"
                        params.extend([word_term, word_term, word_term, word_term])
                    
                    # All words must be found (AND logic)
                    multi_word_condition = "(" + " AND ".join(word_conditions) + ")"
                    conditions.append(multi_word_condition)
            
            # Category filter (if provided)
            if category and category.lower() != "all":
                category_condition = """
                (LOWER(r.Title) LIKE LOWER(?) 
                 OR LOWER(r.Description) LIKE LOWER(?))
                """
                conditions.append(category_condition)
                category_term = f"%{category.strip()}%"
                params.extend([category_term, category_term])
            
            # Author filter (if provided)
            if author and author.strip():
                conditions.append("LOWER(u.Username) LIKE LOWER(?)")
                params.append(f"%{author.strip()}%")
            
            # Combine all conditions
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            
            # Add ordering and pagination
            base_query += """
            ORDER BY r.CreatedAt DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            params.extend([offset, limit])
            
            # Execute search query
            search_results = execute_query(base_query, tuple(params))
            
            # Convert results to API format
            recipes = []
            for row in search_results:
                try:
                    created_at_str = cls._format_datetime(row.get('CreatedAt'))
                    
                    recipe_dict = {
                        "recipe_id": row['RecipeID'],
                        "title": row.get('Title') or "Untitled Recipe",
                        "description": row.get('Description') or "",
                        "author_name": row.get('AuthorName') or "Unknown Chef",
                        "author_id": row['AuthorID'],
                        "image_url": row.get('ImageURL'),
                        "ingredients": row.get('Ingredients'),
                        "instructions": row.get('Instructions'),
                        "raw_ingredients": row.get('RawIngredients'),
                        "servings": row.get('Servings'),
                        "created_at": created_at_str,
                        "likes_count": row.get('LikesCount') or 0,
                        "is_liked": bool(row.get('IsLiked')),
                        "is_favorited": bool(row.get('IsFavorited'))
                    }
                    recipes.append(recipe_dict)
                    
                except Exception as e:
                    print(f"Error processing search result row: {e}")
                    continue
            
            # Get total count using separate query
            total_count = cls._get_search_count(query, category, author)
            
            return {
                "recipes": recipes,
                "total_count": total_count
            }
            
        except Exception as e:
            print(f"Error searching recipes: {e}")
            return {
                "recipes": [],
                "total_count": 0
            }
    
    @classmethod
    def _get_search_count(cls, query: str = None, category: str = None, author: str = None) -> int:
        """Get total count for search results"""
        try:
            count_base_query = """
            SELECT COUNT(*)
            FROM Recipes r
            JOIN Users u ON r.AuthorID = u.UserID
            WHERE 1=1
            """
            
            count_conditions = []
            count_params = []
            
            # Search in multiple fields
            if query and query.strip():
                search_terms = query.strip().split()
                
                if len(search_terms) == 1:
                    search_condition = """
                    (LOWER(r.Title) LIKE LOWER(?) 
                     OR LOWER(r.Description) LIKE LOWER(?) 
                     OR LOWER(r.Ingredients) LIKE LOWER(?) 
                     OR LOWER(r.RawIngredients) LIKE LOWER(?))
                    """
                    count_conditions.append(search_condition)
                    search_term = f"%{query.strip()}%"
                    count_params.extend([search_term, search_term, search_term, search_term])
                    
                else:
                    word_conditions = []
                    for term in search_terms:
                        word_condition = """
                        (LOWER(r.Title) LIKE LOWER(?) 
                         OR LOWER(r.Description) LIKE LOWER(?) 
                         OR LOWER(r.Ingredients) LIKE LOWER(?) 
                         OR LOWER(r.RawIngredients) LIKE LOWER(?))
                        """
                        word_conditions.append(word_condition)
                        word_term = f"%{term}%"
                        count_params.extend([word_term, word_term, word_term, word_term])
                    
                    multi_word_condition = "(" + " AND ".join(word_conditions) + ")"
                    count_conditions.append(multi_word_condition)
            
            # Category filter
            if category and category.lower() != "all":
                category_condition = """
                (LOWER(r.Title) LIKE LOWER(?) 
                 OR LOWER(r.Description) LIKE LOWER(?))
                """
                count_conditions.append(category_condition)
                category_term = f"%{category.strip()}%"
                count_params.extend([category_term, category_term])
            
            # Author filter
            if author and author.strip():
                count_conditions.append("LOWER(u.Username) LIKE LOWER(?)")
                count_params.append(f"%{author.strip()}%")
            
            if count_conditions:
                count_base_query += " AND " + " AND ".join(count_conditions)
            
            return execute_scalar(count_base_query, tuple(count_params)) or 0
            
        except Exception as e:
            print(f"Error getting search count: {e}")
            return 0
    
    @classmethod
    def get_all_with_user_interactions(cls, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all recipes with user-specific interaction data
        
        Args:
            user_id (int): Current user ID for interaction data
            
        Returns:
            List[Dict]: List of recipe dictionaries with user interactions
        """
        try:
            query = """
            SELECT 
                r.RecipeID,
                r.Title,
                r.Description,
                r.Ingredients,
                r.Instructions,
                r.ImageURL,
                r.RawIngredients,
                r.Servings,
                r.CreatedAt,
                r.AuthorID,
                u.Username as AuthorName,
                (SELECT COUNT(*) FROM Likes WHERE RecipeID = r.RecipeID) as LikesCount,
                CASE WHEN EXISTS(SELECT 1 FROM Likes WHERE RecipeID = r.RecipeID AND UserID = ?) 
                     THEN 1 ELSE 0 END as IsLiked,
                CASE WHEN EXISTS(SELECT 1 FROM Favorites WHERE RecipeID = r.RecipeID AND UserID = ?) 
                     THEN 1 ELSE 0 END as IsFavorited
            FROM Recipes r
            JOIN Users u ON r.AuthorID = u.UserID
            ORDER BY r.CreatedAt DESC
            """
            
            all_recipes_data = execute_query(query, (user_id, user_id))
            
            # Convert to API format
            all_recipes = []
            for row in all_recipes_data:
                try:
                    created_at_str = cls._format_datetime(row.get('CreatedAt'))
                    
                    recipe_dict = {
                        "recipe_id": row['RecipeID'],
                        "title": row.get('Title') or "Untitled Recipe",
                        "description": row.get('Description') or "",
                        "author_name": row.get('AuthorName') or "Unknown Chef",
                        "author_id": row['AuthorID'],
                        "image_url": row.get('ImageURL'),
                        "ingredients": row.get('Ingredients'),
                        "instructions": row.get('Instructions'),
                        "raw_ingredients": row.get('RawIngredients'),
                        "servings": row.get('Servings'),
                        "created_at": created_at_str,
                        "likes_count": row.get('LikesCount') or 0,
                        "is_liked": bool(row.get('IsLiked')),
                        "is_favorited": bool(row.get('IsFavorited'))
                    }
                    all_recipes.append(recipe_dict)
                    
                except Exception as e:
                    print(f"Error processing recipe row: {e}")
                    continue
            
            return all_recipes
            
        except Exception as e:
            print(f"Error getting all recipes with interactions: {e}")
            return []
    
    @classmethod
    def get_recipe_with_user_interactions(cls, recipe_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific recipe by ID with user-specific like/favorite status
        
        Args:
            recipe_id (int): Recipe ID
            user_id (int): Current user ID for interaction data
            
        Returns:
            Optional[Dict]: Recipe data with user interactions or None if not found
        """
        try:
            query = """
            SELECT 
                r.RecipeID,
                r.Title,
                r.Description,
                r.Ingredients,
                r.Instructions,
                r.ImageURL,
                r.RawIngredients,
                r.Servings,
                r.CreatedAt,
                r.AuthorID,
                u.Username as AuthorName,
                (SELECT COUNT(*) FROM Likes WHERE RecipeID = r.RecipeID) as LikesCount,
                CASE WHEN EXISTS(SELECT 1 FROM Likes WHERE RecipeID = r.RecipeID AND UserID = ?) 
                     THEN 1 ELSE 0 END as IsLiked,
                CASE WHEN EXISTS(SELECT 1 FROM Favorites WHERE RecipeID = r.RecipeID AND UserID = ?) 
                     THEN 1 ELSE 0 END as IsFavorited
            FROM Recipes r
            JOIN Users u ON r.AuthorID = u.UserID
            WHERE r.RecipeID = ?
            """
            
            recipe_data = execute_query(query, (user_id, user_id, recipe_id), fetch="one")
            
            if not recipe_data or len(recipe_data) == 0:
                return None
            
            row = recipe_data[0]
            created_at_str = cls._format_datetime(row.get('CreatedAt'))
            
            return {
                "recipe_id": row['RecipeID'],
                "title": row.get('Title') or "Untitled Recipe",
                "description": row.get('Description') or "",
                "author_name": row.get('AuthorName') or "Unknown Chef",
                "author_id": row['AuthorID'],
                "image_url": row.get('ImageURL'),
                "ingredients": row.get('Ingredients'),
                "instructions": row.get('Instructions'),
                "raw_ingredients": row.get('RawIngredients'),
                "servings": row.get('Servings'),
                "created_at": created_at_str,
                "likes_count": row.get('LikesCount') or 0,
                "is_liked": bool(row.get('IsLiked')),
                "is_favorited": bool(row.get('IsFavorited'))
            }
            
        except Exception as e:
            print(f"Error getting recipe with interactions: {e}")
            return None
    
    @classmethod
    def _format_datetime(cls, dt) -> str:
        """Format datetime for API response"""
        if not dt:
            return datetime.now().isoformat()
        
        if isinstance(dt, str):
            return dt
        
        try:
            return dt.isoformat()
        except:
            return str(dt)
    
    # ============= EXISTING METHODS FROM USER_ROUTES =============
    
    @classmethod
    def get_user_recipes_with_interactions(cls, user_id: int, current_user_id: int, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        Get recipes created by the user with interaction data
        
        Args:
            user_id (int): User ID whose recipes to get
            current_user_id (int): Current user ID for interaction data
            limit (int): Maximum number of recipes to return
            offset (int): Number of recipes to skip
            
        Returns:
            Dict: Dictionary containing recipes and metadata
        """
        try:
            # Get user's recipes with engagement counts
            recipes_query = """
                SELECT 
                    r.RecipeID,
                    r.Title,
                    r.Description,
                    r.ImageURL,
                    r.CreatedAt,
                    (SELECT COUNT(*) FROM Likes l WHERE l.RecipeID = r.RecipeID) as LikesCount,
                    (SELECT COUNT(*) FROM Favorites f WHERE f.RecipeID = r.RecipeID) as FavoritesCount
                FROM Recipes r
                WHERE r.AuthorID = ?
                ORDER BY r.CreatedAt DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            
            recipes_data = execute_query(recipes_query, (user_id, offset, limit))
            
            # Get user interactions for these recipes
            recipe_ids = [recipe["RecipeID"] for recipe in recipes_data]
            interactions = cls.get_user_interactions(current_user_id, recipe_ids)
            
            # Format response
            recipes = []
            for recipe in recipes_data:
                recipe_id = recipe["RecipeID"]
                user_interaction = interactions.get(recipe_id, {"is_liked": False, "is_favorited": False})
                
                recipes.append({
                    "recipe_id": recipe_id,
                    "title": recipe["Title"],
                    "description": recipe.get("Description"),
                    "image_url": recipe.get("ImageURL"),
                    "created_at": str(recipe.get("CreatedAt")) if recipe.get("CreatedAt") else None,
                    "likes_count": recipe.get("LikesCount", 0),
                    "favorites_count": recipe.get("FavoritesCount", 0),
                    "author_username": "",  # Will be filled by controller
                    "is_liked": user_interaction["is_liked"],
                    "is_favorited": user_interaction["is_favorited"]
                })
            
            return {
                "recipes": recipes,
                "total_count": len(recipes),
                "has_more": len(recipes) == limit
            }
            
        except Exception as e:
            print(f"Error getting user recipes: {e}")
            return {
                "recipes": [],
                "total_count": 0,
                "has_more": False
            }
    
    @classmethod
    def get_user_favorites_with_interactions(cls, user_id: int, current_user_id: int, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        Get recipes favorited by the user with interaction data
        
        Args:
            user_id (int): User ID whose favorites to get
            current_user_id (int): Current user ID for interaction data
            limit (int): Maximum number of recipes to return
            offset (int): Number of recipes to skip
            
        Returns:
            Dict: Dictionary containing recipes and metadata
        """
        try:
            favorites_query = """
                SELECT 
                    r.RecipeID,
                    r.Title,
                    r.Description,
                    r.ImageURL,
                    r.CreatedAt,
                    u.Username as AuthorUsername,
                    f.CreatedAt as FavoritedAt,
                    (SELECT COUNT(*) FROM Likes l WHERE l.RecipeID = r.RecipeID) as LikesCount,
                    (SELECT COUNT(*) FROM Favorites ff WHERE ff.RecipeID = r.RecipeID) as FavoritesCount
                FROM Favorites f
                JOIN Recipes r ON f.RecipeID = r.RecipeID
                JOIN Users u ON r.AuthorID = u.UserID
                WHERE f.UserID = ?
                ORDER BY f.CreatedAt DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            
            favorites_data = execute_query(favorites_query, (user_id, offset, limit))
            
            # Get user interactions (likes) for these recipes
            recipe_ids = [recipe["RecipeID"] for recipe in favorites_data]
            interactions = cls.get_user_interactions(current_user_id, recipe_ids)
            
            # Format response
            recipes = []
            for recipe in favorites_data:
                recipe_id = recipe["RecipeID"]
                user_interaction = interactions.get(recipe_id, {"is_liked": False, "is_favorited": True})
                
                recipes.append({
                    "recipe_id": recipe_id,
                    "title": recipe["Title"],
                    "description": recipe.get("Description"),
                    "image_url": recipe.get("ImageURL"),
                    "created_at": str(recipe.get("CreatedAt")) if recipe.get("CreatedAt") else None,
                    "likes_count": recipe.get("LikesCount", 0),
                    "favorites_count": recipe.get("FavoritesCount", 0),
                    "author_username": recipe.get("AuthorUsername", ""),
                    "is_liked": user_interaction["is_liked"],
                    "is_favorited": True  # Always true for favorites
                })
            
            return {
                "recipes": recipes,
                "total_count": len(recipes),
                "has_more": len(recipes) == limit
            }
            
        except Exception as e:
            print(f"Error getting user favorites: {e}")
            return {
                "recipes": [],
                "total_count": 0,
                "has_more": False
            }
    
    @classmethod
    def get_user_interactions(cls, user_id: int, recipe_ids: List[int]) -> Dict[int, Dict[str, bool]]:
        """Check user's likes/favorites for given recipes"""
        if not recipe_ids:
            return {}
        
        try:
            # Get likes
            placeholders = ",".join(["?" for _ in recipe_ids])
            likes_query = f"""
                SELECT RecipeID FROM Likes 
                WHERE UserID = ? AND RecipeID IN ({placeholders})
            """
            
            liked_recipes = execute_query(likes_query, [user_id] + recipe_ids)
            liked_ids = {row['RecipeID'] for row in liked_recipes}
            
            # Get favorites
            favorites_query = f"""
                SELECT RecipeID FROM Favorites 
                WHERE UserID = ? AND RecipeID IN ({placeholders})
            """
            
            favorited_recipes = execute_query(favorites_query, [user_id] + recipe_ids)
            favorited_ids = {row['RecipeID'] for row in favorited_recipes}
            
            # Build result
            result = {}
            for recipe_id in recipe_ids:
                result[recipe_id] = {
                    "is_liked": recipe_id in liked_ids,
                    "is_favorited": recipe_id in favorited_ids
                }
            
            return result
            
        except Exception as e:
            print(f"Error getting user interactions: {e}")
            return {recipe_id: {"is_liked": False, "is_favorited": False} for recipe_id in recipe_ids}
    
    @classmethod
    def recipe_exists(cls, recipe_id: int) -> bool:
        """Check if recipe exists"""
        try:
            count = execute_scalar(
                "SELECT COUNT(*) FROM Recipes WHERE RecipeID = ?",
                (recipe_id,)
            )
            return count > 0
        except Exception as e:
            print(f"Error checking recipe existence: {e}")
            return False
    
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
                    (self.title, self.description, self.ingredients,
                     self.instructions, self.imageurl, self.rawingredients, self.servings, self.recipeid)
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