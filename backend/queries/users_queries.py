"""
User Queries - CQRS Read Operations

This module handles all READ operations for users.
Focuses on fast data retrieval without side effects.

Key Operations:
- Get user profiles
- Search users
- Get user statistics
- Get user activity feeds
- Get user relationships (followers/following)
"""

from typing import List, Dict, Any, Optional
from database import execute_query, execute_scalar
from datetime import datetime

class BaseQuery:
    """
    Base class for all user queries
    """
    
    def __init__(self):
        self.cache_enabled = True
        self.cache_ttl = 300  # 5 minutes default cache
    
    def _log_query(self, query_name: str, params: Any = None):
        """Log query execution for monitoring"""
        print(f"🔍 Executing user query: {query_name} with params: {params}")

class GetUserByIdQuery(BaseQuery):
    """
    Get user profile by ID
    """
    
    def execute(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get complete user profile with statistics
        
        Args:
            user_id (int): User ID to retrieve
            
        Returns:
            Optional[Dict]: User profile data or None if not found
        """
        self._log_query("GetUserById", user_id)
        
        try:
            # Main user query
            user_query = """
                SELECT 
                    UserID,
                    Username,
                    Email,
                    ProfilePicURL,
                    Bio,
                    CreatedAt
                FROM Users
                WHERE UserID = ?
            """
            
            result = execute_query(user_query, (user_id,), fetch="one")
            
            if not result:
                return None
            
            user_data = result[0]
            
            # Get user statistics
            stats = self._get_user_stats(user_id)
            user_data.update(stats)
            
            return user_data
            
        except Exception as e:
            print(f"❌ Error in GetUserByIdQuery: {e}")
            return None
    
    def _get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            stats = {}
            
            # Recipe count
            stats['recipes_count'] = execute_scalar(
                "SELECT COUNT(*) FROM Recipes WHERE AuthorID = ?", 
                (user_id,)
            ) or 0
            
            # Total likes received on user's recipes
            stats['total_likes_received'] = execute_scalar(
                """SELECT COUNT(*) FROM Likes l
                   JOIN Recipes r ON l.RecipeID = r.RecipeID
                   WHERE r.AuthorID = ?""",
                (user_id,)
            ) or 0
            
            # Total favorites received on user's recipes
            stats['total_favorites_received'] = execute_scalar(
                """SELECT COUNT(*) FROM Favorites f
                   JOIN Recipes r ON f.RecipeID = r.RecipeID
                   WHERE r.AuthorID = ?""",
                (user_id,)
            ) or 0
            
            # Most popular recipe
            popular_recipe = execute_query(
                """SELECT TOP 1 r.Title,
                          (SELECT COUNT(*) FROM Likes l WHERE l.RecipeID = r.RecipeID) +
                          (SELECT COUNT(*) FROM Favorites f WHERE f.RecipeID = r.RecipeID) as Popularity
                   FROM Recipes r
                   WHERE r.AuthorID = ?
                   ORDER BY Popularity DESC""",
                (user_id,),
                fetch="one"
            )
            
            stats['most_popular_recipe'] = popular_recipe[0]['Title'] if popular_recipe else None
            stats['most_popular_recipe_score'] = popular_recipe[0]['Popularity'] if popular_recipe else 0
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting user stats: {e}")
            return {}

class GetUserByUsernameQuery(BaseQuery):
    """
    Get user by username
    """
    
    def execute(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username
        
        Args:
            username (str): Username to search for
            
        Returns:
            Optional[Dict]: User data or None if not found
        """
        self._log_query("GetUserByUsername", username)
        
        try:
            query = """
                SELECT 
                    UserID,
                    Username,
                    Email,
                    ProfilePicURL,
                    Bio,
                    CreatedAt
                FROM Users
                WHERE Username = ?
            """
            
            result = execute_query(query, (username,), fetch="one")
            return result[0] if result else None
            
        except Exception as e:
            print(f"❌ Error in GetUserByUsernameQuery: {e}")
            return None

class GetUserByEmailQuery(BaseQuery):
    """
    Get user by email (typically for login)
    """
    
    def execute(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email including password hash for authentication
        
        Args:
            email (str): Email to search for
            
        Returns:
            Optional[Dict]: User data including password hash
        """
        self._log_query("GetUserByEmail", email)
        
        try:
            query = """
                SELECT 
                    UserID,
                    Username,
                    Email,
                    PasswordHash,
                    ProfilePicURL,
                    Bio,
                    CreatedAt
                FROM Users
                WHERE Email = ?
            """
            
            result = execute_query(query, (email,), fetch="one")
            return result[0] if result else None
            
        except Exception as e:
            print(f"❌ Error in GetUserByEmailQuery: {e}")
            return None

class SearchUsersQuery(BaseQuery):
    """
    Search users by username or bio
    """
    
    def execute(self, search_text: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search users by username or bio content
        
        Args:
            search_text (str): Text to search for
            limit (int): Maximum results
            offset (int): Results offset for pagination
            
        Returns:
            List[Dict]: Matching users
        """
        self._log_query("SearchUsers", {"search_text": search_text, "limit": limit})
        
        try:
            query = """
                SELECT 
                    u.UserID,
                    u.Username,
                    u.ProfilePicURL,
                    u.Bio,
                    u.CreatedAt,
                    (SELECT COUNT(*) FROM Recipes r WHERE r.AuthorID = u.UserID) as RecipesCount,
                    (SELECT COUNT(*) FROM Likes l 
                     JOIN Recipes r ON l.RecipeID = r.RecipeID 
                     WHERE r.AuthorID = u.UserID) as TotalLikes
                FROM Users u
                WHERE u.Username LIKE ? OR u.Bio LIKE ?
                ORDER BY 
                    CASE WHEN u.Username LIKE ? THEN 1 ELSE 2 END,
                    TotalLikes DESC,
                    u.Username ASC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            
            search_param = f"%{search_text}%"
            exact_username = f"{search_text}%"
            
            return execute_query(query, (search_param, search_param, exact_username, offset, limit))
            
        except Exception as e:
            print(f"❌ Error in SearchUsersQuery: {e}")
            return []

class GetUserActivityFeedQuery(BaseQuery):
    """
    Get user's activity feed (their actions)
    """
    
    def execute(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get chronological feed of user activities
        
        Args:
            user_id (int): User ID
            limit (int): Number of activities to return
            
        Returns:
            List[Dict]: Activity items with type and timestamp
        """
        self._log_query("GetUserActivityFeed", {"user_id": user_id, "limit": limit})
        
        try:
            activities = []
            
            # Get recipe creations
            recipe_activities = execute_query(
                """SELECT 
                       'recipe_created' as ActivityType,
                       r.RecipeID as TargetID,
                       r.Title as TargetTitle,
                       r.CreatedAt as ActivityTimestamp
                   FROM Recipes r
                   WHERE r.AuthorID = ?
                   ORDER BY r.CreatedAt DESC""",
                (user_id,)
            )
            
            activities.extend(recipe_activities)
            
            # Get likes
            like_activities = execute_query(
                """SELECT 
                       'recipe_liked' as ActivityType,
                       l.RecipeID as TargetID,
                       r.Title as TargetTitle,
                       l.CreatedAt as ActivityTimestamp,
                       u.Username as TargetAuthor
                   FROM Likes l
                   JOIN Recipes r ON l.RecipeID = r.RecipeID
                   JOIN Users u ON r.AuthorID = u.UserID
                   WHERE l.UserID = ?
                   ORDER BY l.CreatedAt DESC""",
                (user_id,)
            )
            
            activities.extend(like_activities)
            
            # Get favorites
            favorite_activities = execute_query(
                """SELECT 
                       'recipe_favorited' as ActivityType,
                       f.RecipeID as TargetID,
                       r.Title as TargetTitle,
                       f.CreatedAt as ActivityTimestamp,
                       u.Username as TargetAuthor
                   FROM Favorites f
                   JOIN Recipes r ON f.RecipeID = r.RecipeID
                   JOIN Users u ON r.AuthorID = u.UserID
                   WHERE f.UserID = ?
                   ORDER BY f.CreatedAt DESC""",
                (user_id,)
            )
            
            activities.extend(favorite_activities)
            
            # Sort all activities by timestamp and limit
            activities.sort(key=lambda x: x['ActivityTimestamp'], reverse=True)
            return activities[:limit]
            
        except Exception as e:
            print(f"❌ Error in GetUserActivityFeedQuery: {e}")
            return []

class GetUserRecipesQuery(BaseQuery):
    """
    Get all recipes created by a user
    """
    
    def execute(self, user_id: int, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get user's recipes with engagement metrics
        
        Args:
            user_id (int): User ID
            limit (int): Maximum recipes to return
            offset (int): Number of recipes to skip
            
        Returns:
            List[Dict]: User's recipes
        """
        self._log_query("GetUserRecipes", {"user_id": user_id, "limit": limit})
        
        try:
            query = """
                SELECT 
                    r.RecipeID,
                    r.Title,
                    r.Description,
                    r.ImageURL,
                    r.Servings,
                    r.CreatedAt,
                    (SELECT COUNT(*) FROM Likes l WHERE l.RecipeID = r.RecipeID) as LikesCount,
                    (SELECT COUNT(*) FROM Favorites f WHERE f.RecipeID = r.RecipeID) as FavoritesCount,
                    (SELECT COUNT(*) FROM RecipeTags rt WHERE rt.RecipeID = r.RecipeID) as TagsCount
                FROM Recipes r
                WHERE r.AuthorID = ?
                ORDER BY r.CreatedAt DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            
            return execute_query(query, (user_id, offset, limit))
            
        except Exception as e:
            print(f"❌ Error in GetUserRecipesQuery: {e}")
            return []

class GetUserFavoritesQuery(BaseQuery):
    """
    Get recipes favorited by a user
    """
    
    def execute(self, user_id: int, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get user's favorite recipes
        
        Args:
            user_id (int): User ID
            limit (int): Maximum recipes to return
            offset (int): Number of recipes to skip
            
        Returns:
            List[Dict]: Favorited recipes
        """
        self._log_query("GetUserFavorites", {"user_id": user_id, "limit": limit})
        
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
            
            return execute_query(query, (user_id, offset, limit))
            
        except Exception as e:
            print(f"❌ Error in GetUserFavoritesQuery: {e}")
            return []

class GetUserLikedRecipesQuery(BaseQuery):
    """
    Get recipes liked by a user
    """
    
    def execute(self, user_id: int, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get user's liked recipes
        
        Args:
            user_id (int): User ID
            limit (int): Maximum recipes to return
            offset (int): Number of recipes to skip
            
        Returns:
            List[Dict]: Liked recipes
        """
        self._log_query("GetUserLikedRecipes", {"user_id": user_id, "limit": limit})
        
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
                    l.CreatedAt as LikedAt,
                    (SELECT COUNT(*) FROM Likes ll WHERE ll.RecipeID = r.RecipeID) as LikesCount,
                    (SELECT COUNT(*) FROM Favorites f WHERE f.RecipeID = r.RecipeID) as FavoritesCount
                FROM Likes l
                JOIN Recipes r ON l.RecipeID = r.RecipeID
                JOIN Users u ON r.AuthorID = u.UserID
                WHERE l.UserID = ?
                ORDER BY l.CreatedAt DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            
            return execute_query(query, (user_id, offset, limit))
            
        except Exception as e:
            print(f"❌ Error in GetUserLikedRecipesQuery: {e}")
            return []

class GetUserStatsQuery(BaseQuery):
    """
    Get comprehensive user statistics
    """
    
    def execute(self, user_id: int) -> Dict[str, Any]:
        """
        Get detailed statistics for a user
        
        Args:
            user_id (int): User ID
            
        Returns:
            Dict: Comprehensive user statistics
        """
        self._log_query("GetUserStats", user_id)
        
        try:
            stats = {}
            
            # Basic counts
            stats['total_recipes'] = execute_scalar(
                "SELECT COUNT(*) FROM Recipes WHERE AuthorID = ?", 
                (user_id,)
            ) or 0
            
            stats['total_likes_given'] = execute_scalar(
                "SELECT COUNT(*) FROM Likes WHERE UserID = ?", 
                (user_id,)
            ) or 0
            
            stats['total_favorites_given'] = execute_scalar(
                "SELECT COUNT(*) FROM Favorites WHERE UserID = ?", 
                (user_id,)
            ) or 0
            
            stats['total_likes_received'] = execute_scalar(
                """SELECT COUNT(*) FROM Likes l
                   JOIN Recipes r ON l.RecipeID = r.RecipeID
                   WHERE r.AuthorID = ?""",
                (user_id,)
            ) or 0
            
            stats['total_favorites_received'] = execute_scalar(
                """SELECT COUNT(*) FROM Favorites f
                   JOIN Recipes r ON f.RecipeID = r.RecipeID
                   WHERE r.AuthorID = ?""",
                (user_id,)
            ) or 0
            
            # Recent activity (last 30 days)
            stats['recent_recipes'] = execute_scalar(
                """SELECT COUNT(*) FROM Recipes 
                   WHERE AuthorID = ? AND CreatedAt >= DATEADD(day, -30, GETDATE())""",
                (user_id,)
            ) or 0
            
            stats['recent_likes_given'] = execute_scalar(
                """SELECT COUNT(*) FROM Likes 
                   WHERE UserID = ? AND CreatedAt >= DATEADD(day, -30, GETDATE())""",
                (user_id,)
            ) or 0
            
            # Most used tags
            most_used_tags = execute_query(
                """SELECT TOP 5 t.TagName, COUNT(*) as UsageCount
                   FROM Tags t
                   JOIN RecipeTags rt ON t.TagID = rt.TagID
                   JOIN Recipes r ON rt.RecipeID = r.RecipeID
                   WHERE r.AuthorID = ?
                   GROUP BY t.TagID, t.TagName
                   ORDER BY UsageCount DESC""",
                (user_id,)
            )
            
            stats['most_used_tags'] = [
                {"tag": tag['TagName'], "count": tag['UsageCount']} 
                for tag in most_used_tags
            ]
            
            # Average engagement per recipe
            if stats['total_recipes'] > 0:
                stats['avg_likes_per_recipe'] = round(
                    stats['total_likes_received'] / stats['total_recipes'], 2
                )
                stats['avg_favorites_per_recipe'] = round(
                    stats['total_favorites_received'] / stats['total_recipes'], 2
                )
            else:
                stats['avg_likes_per_recipe'] = 0
                stats['avg_favorites_per_recipe'] = 0
            
            # Engagement rate (total engagement / total recipes)
            total_engagement = stats['total_likes_received'] + stats['total_favorites_received']
            stats['engagement_rate'] = round(
                total_engagement / max(stats['total_recipes'], 1), 2
            )
            
            # Most popular recipe
            popular_recipe = execute_query(
                """SELECT TOP 1 
                       r.RecipeID,
                       r.Title,
                       (SELECT COUNT(*) FROM Likes l WHERE l.RecipeID = r.RecipeID) +
                       (SELECT COUNT(*) FROM Favorites f WHERE f.RecipeID = r.RecipeID) as TotalEngagement
                   FROM Recipes r
                   WHERE r.AuthorID = ?
                   ORDER BY TotalEngagement DESC, r.CreatedAt DESC""",
                (user_id,),
                fetch="one"
            )
            
            if popular_recipe:
                stats['most_popular_recipe'] = {
                    "recipe_id": popular_recipe[0]['RecipeID'],
                    "title": popular_recipe[0]['Title'],
                    "engagement": popular_recipe[0]['TotalEngagement']
                }
            else:
                stats['most_popular_recipe'] = None
            
            return stats
            
        except Exception as e:
            print(f"❌ Error in GetUserStatsQuery: {e}")
            return {}

class GetActiveUsersQuery(BaseQuery):
    """
    Get most active users in the platform
    """
    
    def execute(self, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get users with most activity in the last N days
        
        Args:
            days (int): Number of days to look back
            limit (int): Number of users to return
            
        Returns:
            List[Dict]: Most active users
        """
        self._log_query("GetActiveUsers", {"days": days, "limit": limit})
        
        try:
            query = """
                SELECT 
                    u.UserID,
                    u.Username,
                    u.ProfilePicURL,
                    u.Bio,
                    COUNT(DISTINCT r.RecipeID) as RecentRecipes,
                    COUNT(DISTINCT l.RecipeID) as RecentLikes,
                    COUNT(DISTINCT f.RecipeID) as RecentFavorites,
                    (COUNT(DISTINCT r.RecipeID) + COUNT(DISTINCT l.RecipeID) + COUNT(DISTINCT f.RecipeID)) as ActivityScore
                FROM Users u
                LEFT JOIN Recipes r ON u.UserID = r.AuthorID 
                    AND r.CreatedAt >= DATEADD(day, -?, GETDATE())
                LEFT JOIN Likes l ON u.UserID = l.UserID 
                    AND l.CreatedAt >= DATEADD(day, -?, GETDATE())
                LEFT JOIN Favorites f ON u.UserID = f.UserID 
                    AND f.CreatedAt >= DATEADD(day, -?, GETDATE())
                GROUP BY u.UserID, u.Username, u.ProfilePicURL, u.Bio
                HAVING ActivityScore > 0
                ORDER BY ActivityScore DESC, u.Username ASC
                OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
            """
            
            return execute_query(query, (days, days, days, limit))
            
        except Exception as e:
            print(f"❌ Error in GetActiveUsersQuery: {e}")
            return []

class GetNewUsersQuery(BaseQuery):
    """
    Get recently joined users
    """
    
    def execute(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get users who joined in the last N days
        
        Args:
            days (int): Number of days to look back
            limit (int): Number of users to return
            
        Returns:
            List[Dict]: New users
        """
        self._log_query("GetNewUsers", {"days": days, "limit": limit})
        
        try:
            query = """
                SELECT 
                    u.UserID,
                    u.Username,
                    u.ProfilePicURL,
                    u.Bio,
                    u.CreatedAt,
                    (SELECT COUNT(*) FROM Recipes r WHERE r.AuthorID = u.UserID) as RecipesCount
                FROM Users u
                WHERE u.CreatedAt >= DATEADD(day, -?, GETDATE())
                ORDER BY u.CreatedAt DESC
                OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
            """
            
            return execute_query(query, (days, limit))
            
        except Exception as e:
            print(f"❌ Error in GetNewUsersQuery: {e}")
            return []

# class CheckUsernameAvailabilityQuery(BaseQuery):
#     """
#     Check if username is available
#     """
    
#     def execute(self, username: str, exclude_user_id: Optional[int] = None) -> bool:
#         """
#         Check if username is available for use
        
#         Args:
#             username (str): Username to check
#             exclude_user_id (int): User ID to exclude (for updates)
            
#         Returns:
#             bool: True if available, False if taken
#         """
#         self._log_query("CheckUsernameAvailability", {"username": username, "exclude": exclude_user_id})
        
#         try:
#             if exclude_user_id:
#                 # Check availability excluding specific user (for profile updates)
#                 count = execute_scalar(
#                     "SELECT COUNT(*) FROM Users WHERE Username = ? AND UserID != ?",
#                     (username, exclude_user_id)
#                 ) or 0
#             else:
#                 # Check availability for new registration
#                 count = execute_scalar(
#                     "SELECT COUNT(*) FROM Users WHERE Username = ?",
#                     (username,)
#                 ) or 0
            
#             return count == 0  # Available if count is 0
            
#         except Exception as e:
#             print(f"❌ Error in CheckUsernameAvailabilityQuery: {e}")
#             return False

# class CheckEmailAvailabilityQuery(BaseQuery):
#     """
#     Check if email is available
#     """
    
#     def execute(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
#         """
#         Check if email is available for use
        
#         Args:
#             email (str): Email to check
#             exclude_user_id (int): User ID to exclude (for updates)
            
#         Returns:
#             bool: True if available, False if taken
#         """
#         self._log_query("CheckEmailAvailability", {"email": email, "exclude": exclude_user_id})
        
#         try:
#             if exclude_user_id:
#                 # Check availability excluding specific user (for profile updates)
#                 count = execute_scalar(
#                     "SELECT COUNT(*) FROM Users WHERE Email = ? AND UserID != ?",
#                     (email, exclude_user_id)
#                 ) or 0
#             else:
#                 # Check availability for new registration
#                 count = execute_scalar(
#                     "SELECT COUNT(*) FROM Users WHERE Email = ?",
#                     (email,)
#                 ) or 0
            
#             return count == 0  # Available if count is 0
            
#         except Exception as e:
#             print(f"❌ Error in CheckEmailAvailabilityQuery: {e}")
#             return False

class GetUserDashboardDataQuery(BaseQuery):
    """
    Get all data needed for user dashboard in one query
    """
    
    def execute(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for user
        
        Args:
            user_id (int): User ID
            
        Returns:
            Dict: Dashboard data including stats, recent activity, etc.
        """
        self._log_query("GetUserDashboardData", user_id)
        
        try:
            dashboard_data = {}
            
            # Get user profile
            user_query = GetUserByIdQuery()
            dashboard_data['profile'] = user_query.execute(user_id)
            
            # Get user stats
            stats_query = GetUserStatsQuery()
            dashboard_data['stats'] = stats_query.execute(user_id)
            
            # Get recent recipes (last 5)
            recipes_query = GetUserRecipesQuery()
            dashboard_data['recent_recipes'] = recipes_query.execute(user_id, limit=5)
            
            # Get recent activity (last 10)
            activity_query = GetUserActivityFeedQuery()
            dashboard_data['recent_activity'] = activity_query.execute(user_id, limit=10)
            
            # Get recent favorites (last 5)
            favorites_query = GetUserFavoritesQuery()
            dashboard_data['recent_favorites'] = favorites_query.execute(user_id, limit=5)
            
            return dashboard_data
            
        except Exception as e:
            print(f"❌ Error in GetUserDashboardDataQuery: {e}")
            return {}