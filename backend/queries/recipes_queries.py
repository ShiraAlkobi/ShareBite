"""
Recipe Queries - CQRS Read Operations

This module handles all READ operations for recipes.
Queries are optimized for fast data retrieval and can use:
- Simple database queries
- Complex joins
- Cached results
- Read-only database replicas (in production)

Key Principles:
- No business logic (just data retrieval)
- No side effects (don't change data)
- Optimized for performance
- Can return raw data or formatted results
"""

from typing import List, Dict, Any, Optional
from database import execute_query, execute_scalar
from datetime import datetime

class BaseQuery:
    """
    Base class for all queries with common functionality
    """
    
    def __init__(self):
        self.cache_enabled = True
        self.cache_ttl = 300  # 5 minutes default cache
    
    def _log_query(self, query_name: str, params: Any = None):
        """Log query execution for monitoring"""
        print(f"🔍 Executing query: {query_name} with params: {params}")

class GetRecipeByIdQuery(BaseQuery):
    """
    Get a single recipe by ID with all related data
    """
    
    def execute(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """
        Get recipe with author info, tags, and engagement metrics
        
        Args:
            recipe_id (int): Recipe ID to retrieve
            
        Returns:
            Optional[Dict]: Recipe data or None if not found
        """
        self._log_query("GetRecipeById", recipe_id)
        
        try:
            # Main recipe query with author join
            recipe_query = """
                SELECT 
                    r.RecipeID,
                    r.AuthorID,
                    r.Title,
                    r.Description,
                    r.Ingredients,
                    r.Instructions,
                    r.ImageURL,
                    r.RawIngredients,
                    r.Servings,
                    r.CreatedAt,
                    u.Username as AuthorUsername,
                    u.ProfilePicURL as AuthorProfilePic
                FROM Recipes r
                JOIN Users u ON r.AuthorID = u.UserID
                WHERE r.RecipeID = ?
            """
            
            result = execute_query(recipe_query, (recipe_id,), fetch="one")
            
            if not result:
                return None
            
            recipe_data = result[0]
            
            # Get tags for this recipe
            tags_query = """
                SELECT t.TagName
                FROM Tags t
                JOIN RecipeTags rt ON t.TagID = rt.TagID
                WHERE rt.RecipeID = ?
                ORDER BY t.TagName
            """
            
            tags_result = execute_query(tags_query, (recipe_id,))
            recipe_data['tags'] = [tag['TagName'] for tag in tags_result]
            
            # Get engagement metrics
            likes_count = execute_scalar(
                "SELECT COUNT(*) FROM Likes WHERE RecipeID = ?", 
                (recipe_id,)
            ) or 0
            
            favorites_count = execute_scalar(
                "SELECT COUNT(*) FROM Favorites WHERE RecipeID = ?", 
                (recipe_id,)
            ) or 0
            
            recipe_data['likes_count'] = likes_count
            recipe_data['favorites_count'] = favorites_count
            recipe_data['total_engagement'] = likes_count + favorites_count
            
            return recipe_data
            
        except Exception as e:
            print(f"❌ Error in GetRecipeByIdQuery: {e}")
            return None

class GetRecipesByAuthorQuery(BaseQuery):
    """
    Get all recipes by a specific author
    """
    
    def execute(self, author_id: int, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get recipes by author with pagination
        
        Args:
            author_id (int): Author's user ID
            limit (int): Maximum number of recipes
            offset (int): Number of recipes to skip
            
        Returns:
            List[Dict]: List of recipe data
        """
        self._log_query("GetRecipesByAuthor", {"author_id": author_id, "limit": limit})
        
        try:
            query = """
                SELECT 
                    r.RecipeID,
                    r.Title,
                    r.Description,
                    r.ImageURL,
                    r.Servings,
                    r.CreatedAt,
                    u.Username as AuthorUsername,
                    (SELECT COUNT(*) FROM Likes l WHERE l.RecipeID = r.RecipeID) as LikesCount,
                    (SELECT COUNT(*) FROM Favorites f WHERE f.RecipeID = r.RecipeID) as FavoritesCount
                FROM Recipes r
                JOIN Users u ON r.AuthorID = u.UserID
                WHERE r.AuthorID = ?
                ORDER BY r.CreatedAt DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            
            return execute_query(query, (author_id, offset, limit))
            
        except Exception as e:
            print(f"❌ Error in GetRecipesByAuthorQuery: {e}")
            return []

class SearchRecipesQuery(BaseQuery):
    """
    Search recipes by various criteria
    """
    
    def execute(self, 
                search_text: Optional[str] = None,
                tags: Optional[List[str]] = None,
                author_id: Optional[int] = None,
                min_servings: Optional[int] = None,
                max_servings: Optional[int] = None,
                limit: int = 20,
                offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search recipes with multiple filters
        
        Args:
            search_text (str): Search in title and description
            tags (List[str]): Filter by tags
            author_id (int): Filter by author
            min_servings (int): Minimum servings
            max_servings (int): Maximum servings
            limit (int): Results limit
            offset (int): Results offset
            
        Returns:
            List[Dict]: Matching recipes
        """
        self._log_query("SearchRecipes", {
            "search_text": search_text,
            "tags": tags,
            "author_id": author_id
        })
        
        try:
            # Build dynamic query
            base_query = """
                SELECT DISTINCT
                    r.RecipeID,
                    r.Title,
                    r.Description,
                    r.ImageURL,
                    r.Servings,
                    r.CreatedAt,
                    u.Username as AuthorUsername,
                    (SELECT COUNT(*) FROM Likes l WHERE l.RecipeID = r.RecipeID) as LikesCount,
                    (SELECT COUNT(*) FROM Favorites f WHERE f.RecipeID = r.RecipeID) as FavoritesCount
                FROM Recipes r
                JOIN Users u ON r.AuthorID = u.UserID
            """
            
            conditions = []
            params = []
            
            # Add tag joins if needed
            if tags:
                base_query += """
                    JOIN RecipeTags rt ON r.RecipeID = rt.RecipeID
                    JOIN Tags t ON rt.TagID = t.TagID
                """
                placeholders = ",".join(["?" for _ in tags])
                conditions.append(f"t.TagName IN ({placeholders})")
                params.extend(tags)
            
            # Add text search
            if search_text:
                conditions.append("(r.Title LIKE ? OR r.Description LIKE ?)")
                search_param = f"%{search_text}%"
                params.extend([search_param, search_param])
            
            # Add author filter
            if author_id:
                conditions.append("r.AuthorID = ?")
                params.append(author_id)
            
            # Add servings filters
            if min_servings:
                conditions.append("r.Servings >= ?")
                params.append(min_servings)
                
            if max_servings:
                conditions.append("r.Servings <= ?")
                params.append(max_servings)
            
            # Build WHERE clause
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            
            # Add ordering and pagination
            base_query += """
                ORDER BY r.CreatedAt DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            params.extend([offset, limit])
            
            return execute_query(base_query, tuple(params))
            
        except Exception as e:
            print(f"❌ Error in SearchRecipesQuery: {e}")
            return []

class GetTrendingRecipesQuery(BaseQuery):
    """
    Get trending recipes based on recent engagement
    """
    
    def execute(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recipes trending in the last N days
        
        Args:
            days (int): Number of days to look back
            limit (int): Number of recipes to return
            
        Returns:
            List[Dict]: Trending recipes with scores
        """
        self._log_query("GetTrendingRecipes", {"days": days, "limit": limit})
        
        try:
            query = """
                SELECT 
                    r.RecipeID,
                    r.Title,
                    r.Description,
                    r.ImageURL,
                    r.Servings,
                    r.CreatedAt,
                    u.Username as AuthorUsername,
                    COUNT(DISTINCT l.UserID) as RecentLikes,
                    COUNT(DISTINCT f.UserID) as RecentFavorites,
                    (COUNT(DISTINCT l.UserID) + COUNT(DISTINCT f.UserID)) as TrendingScore
                FROM Recipes r
                JOIN Users u ON r.AuthorID = u.UserID
                LEFT JOIN Likes l ON r.RecipeID = l.RecipeID 
                    AND l.CreatedAt >= DATEADD(day, -?, GETDATE())
                LEFT JOIN Favorites f ON r.RecipeID = f.RecipeID 
                    AND f.CreatedAt >= DATEADD(day, -?, GETDATE())
                GROUP BY r.RecipeID, r.Title, r.Description, r.ImageURL, 
                         r.Servings, r.CreatedAt, u.Username
                HAVING (COUNT(DISTINCT l.UserID) + COUNT(DISTINCT f.UserID)) > 0
                ORDER BY TrendingScore DESC, r.CreatedAt DESC
                OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
            """
            
            return execute_query(query, (days, days, limit))
            
        except Exception as e:
            print(f"❌ Error in GetTrendingRecipesQuery: {e}")
            return []

class GetRecentRecipesQuery(BaseQuery):
    """
    Get most recently created recipes
    """
    
    def execute(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get newest recipes
        
        Args:
            limit (int): Number of recipes to return
            
        Returns:
            List[Dict]: Recent recipes
        """
        self._log_query("GetRecentRecipes", {"limit": limit})
        
        try:
            query = """
                SELECT 
                    r.RecipeID,
                    r.Title,
                    r.Description,
                    r.ImageURL,
                    r.Servings,
                    r.CreatedAt,
                    u.Username as AuthorUsername,
                    (SELECT COUNT(*) FROM Likes l WHERE l.RecipeID = r.RecipeID) as LikesCount,
                    (SELECT COUNT(*) FROM Favorites f WHERE f.RecipeID = r.RecipeID) as FavoritesCount
                FROM Recipes r
                JOIN Users u ON r.AuthorID = u.UserID
                ORDER BY r.CreatedAt DESC
                OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
            """
            
            return execute_query(query, (limit,))
            
        except Exception as e:
            print(f"❌ Error in GetRecentRecipesQuery: {e}")
            return []

class GetRecipeStatsQuery(BaseQuery):
    """
    Get detailed statistics for a recipe
    """
    
    def execute(self, recipe_id: int) -> Dict[str, Any]:
        """
        Get comprehensive recipe statistics
        
        Args:
            recipe_id (int): Recipe ID
            
        Returns:
            Dict: Recipe statistics
        """
        self._log_query("GetRecipeStats", recipe_id)
        
        try:
            stats = {}
            
            # Basic counts
            stats['total_likes'] = execute_scalar(
                "SELECT COUNT(*) FROM Likes WHERE RecipeID = ?", (recipe_id,)
            ) or 0
            
            stats['total_favorites'] = execute_scalar(
                "SELECT COUNT(*) FROM Favorites WHERE RecipeID = ?", (recipe_id,)
            ) or 0
            
            # Recent engagement (last 7 days)
            stats['recent_likes'] = execute_scalar(
                """SELECT COUNT(*) FROM Likes 
                   WHERE RecipeID = ? AND CreatedAt >= DATEADD(day, -7, GETDATE())""",
                (recipe_id,)
            ) or 0
            
            stats['recent_favorites'] = execute_scalar(
                """SELECT COUNT(*) FROM Favorites 
                   WHERE RecipeID = ? AND CreatedAt >= DATEADD(day, -7, GETDATE())""",
                (recipe_id,)
            ) or 0
            
            # Engagement by day (last 30 days)
            daily_engagement = execute_query(
                """SELECT 
                       CAST(CreatedAt AS DATE) as EngagementDate,
                       COUNT(*) as DailyCount
                   FROM (
                       SELECT CreatedAt FROM Likes WHERE RecipeID = ?
                       UNION ALL
                       SELECT CreatedAt FROM Favorites WHERE RecipeID = ?
                   ) combined
                   WHERE CreatedAt >= DATEADD(day, -30, GETDATE())
                   GROUP BY CAST(CreatedAt AS DATE)
                   ORDER BY EngagementDate DESC""",
                (recipe_id, recipe_id)
            )
            
            stats['daily_engagement'] = daily_engagement
            stats['peak_engagement_day'] = daily_engagement[0] if daily_engagement else None
            
            return stats
            
        except Exception as e:
            print(f"❌ Error in GetRecipeStatsQuery: {e}")
            return {}

class GetUserInteractionsQuery(BaseQuery):
    """
    Check user's interactions with recipes (likes/favorites)
    """
    
    def execute(self, user_id: int, recipe_ids: List[int]) -> Dict[int, Dict[str, bool]]:
        """
        Check if user has liked/favorited specific recipes
        
        Args:
            user_id (int): User ID
            recipe_ids (List[int]): List of recipe IDs to check
            
        Returns:
            Dict: {recipe_id: {"is_liked": bool, "is_favorited": bool}}
        """
        self._log_query("GetUserInteractions", {"user_id": user_id, "recipe_count": len(recipe_ids)})
        
        try:
            if not recipe_ids:
                return {}
            
            # Check likes
            placeholders = ",".join(["?" for _ in recipe_ids])
            likes_query = f"""
                SELECT RecipeID FROM Likes 
                WHERE UserID = ? AND RecipeID IN ({placeholders})
            """
            
            liked_recipes = execute_query(likes_query, [user_id] + recipe_ids)
            liked_ids = {row['RecipeID'] for row in liked_recipes}
            
            # Check favorites
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
            print(f"❌ Error in GetUserInteractionsQuery: {e}")
            return {}

class GetRecipeRecommendationsQuery(BaseQuery):
    """
    Get personalized recipe recommendations for a user
    """
    
    def execute(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recipes recommended for user based on their activity
        
        Args:
            user_id (int): User ID for recommendations
            limit (int): Number of recommendations
            
        Returns:
            List[Dict]: Recommended recipes
        """
        self._log_query("GetRecipeRecommendations", {"user_id": user_id, "limit": limit})
        
        try:
            # Get recipes with tags similar to user's liked/favorited recipes
            query = """
                SELECT DISTINCT
                    r.RecipeID,
                    r.Title,
                    r.Description,
                    r.ImageURL,
                    r.Servings,
                    r.CreatedAt,
                    u.Username as AuthorUsername,
                    COUNT(DISTINCT rt.TagID) as CommonTags,
                    (SELECT COUNT(*) FROM Likes l WHERE l.RecipeID = r.RecipeID) as LikesCount
                FROM Recipes r
                JOIN Users u ON r.AuthorID = u.UserID
                JOIN RecipeTags rt ON r.RecipeID = rt.RecipeID
                WHERE rt.TagID IN (
                    -- Tags from recipes user has liked
                    SELECT DISTINCT rt2.TagID
                    FROM RecipeTags rt2
                    JOIN Likes l ON rt2.RecipeID = l.RecipeID
                    WHERE l.UserID = ?
                    UNION
                    -- Tags from recipes user has favorited
                    SELECT DISTINCT rt3.TagID
                    FROM RecipeTags rt3
                    JOIN Favorites f ON rt3.RecipeID = f.RecipeID
                    WHERE f.UserID = ?
                )
                AND r.RecipeID NOT IN (
                    -- Exclude recipes user already interacted with
                    SELECT RecipeID FROM Likes WHERE UserID = ?
                    UNION
                    SELECT RecipeID FROM Favorites WHERE UserID = ?
                )
                AND r.AuthorID != ?  -- Exclude user's own recipes
                GROUP BY r.RecipeID, r.Title, r.Description, r.ImageURL, 
                         r.Servings, r.CreatedAt, u.Username
                ORDER BY CommonTags DESC, LikesCount DESC, r.CreatedAt DESC
                OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
            """
            
            return execute_query(query, (user_id, user_id, user_id, user_id, user_id, limit))
            
        except Exception as e:
            print(f"❌ Error in GetRecipeRecommendationsQuery: {e}")
            return []