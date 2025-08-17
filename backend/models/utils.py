"""
Utility functions for Recipe Sharing Platform models

This module contains helper functions that work across multiple models
or perform complex database operations that don't belong to a single model.

Functions include:
- Trending and recommendation algorithms
- Search functionality
- Activity feeds
- Database statistics
- Complex aggregations
"""

from typing import Dict, Any, List
from database import execute_query, execute_scalar

def get_trending_recipes(days: int = 7, limit: int = 10):
    """
    Get trending recipes based on recent likes and favorites
    
    Algorithm: Calculates a trending score based on unique users who 
    liked or favorited recipes within the specified time period.
    
    Args:
        days (int): Number of days to look back for trending calculation
        limit (int): Maximum number of recipes to return
        
    Returns:
        List[dict]: List of recipe dictionaries with trending scores
        
    Example:
        # Get top 10 trending recipes from last 7 days
        trending = get_trending_recipes(days=7, limit=10)
        
        # Get top 5 trending recipes from last 30 days  
        monthly_trending = get_trending_recipes(days=30, limit=5)
    """
    try:
        result = execute_query(
            """SELECT r.RecipeID, r.AuthorID, r.Title, r.Description, 
                      r.Ingredients, r.Instructions, r.ImageURL, 
                      r.RawIngredients, r.Servings, r.CreatedAt,
                      u.Username as AuthorUsername,
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
               HAVING (COUNT(DISTINCT l.UserID) + COUNT(DISTINCT f.UserID)) > 0
               ORDER BY TrendingScore DESC, r.CreatedAt DESC""",
            (days, days)
        )
        
        recipes = result[:limit] if result else []
        print(f"✅ Found {len(recipes)} trending recipes from last {days} days")
        return recipes
        
    except Exception as e:
        print(f"❌ Error getting trending recipes: {e}")
        return []

def get_recipe_recommendations(user_id: int, limit: int = 10):
    """
    Get personalized recipe recommendations for a user
    
    Algorithm: Finds recipes with tags similar to those the user has 
    liked or favorited, excluding recipes they already know about.
    
    Args:
        user_id (int): User ID to generate recommendations for
        limit (int): Maximum number of recommendations to return
        
    Returns:
        List[dict]: List of recommended recipe dictionaries
        
    Example:
        # Get 10 recommendations for user
        recommendations = get_recipe_recommendations(user_id=5, limit=10)
        
        # Get 5 recommendations for user
        few_recommendations = get_recipe_recommendations(user_id=5, limit=5)
    """
    try:
        # Get recipes with similar tags to user's liked/favorited recipes
        result = execute_query(
            """SELECT DISTINCT r.RecipeID, r.AuthorID, r.Title, r.Description,
                      r.Ingredients, r.Instructions, r.ImageURL, r.RawIngredients,
                      r.Servings, r.CreatedAt, u.Username as AuthorUsername,
                      COUNT(DISTINCT rt.TagID) as CommonTags
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
                   -- Exclude recipes user already liked
                   SELECT RecipeID FROM Likes WHERE UserID = ?
                   UNION
                   -- Exclude recipes user already favorited
                   SELECT RecipeID FROM Favorites WHERE UserID = ?
               )
               AND r.AuthorID != ?  -- Exclude user's own recipes
               GROUP BY r.RecipeID, r.AuthorID, r.Title, r.Description,
                        r.Ingredients, r.Instructions, r.ImageURL, r.RawIngredients,
                        r.Servings, r.CreatedAt, u.Username
               ORDER BY CommonTags DESC, r.CreatedAt DESC""",
            (user_id, user_id, user_id, user_id, user_id)
        )
        
        recommendations = result[:limit] if result else []
        print(f"✅ Generated {len(recommendations)} recommendations for user {user_id}")
        return recommendations
        
    except Exception as e:
        print(f"❌ Error getting recipe recommendations: {e}")
        return []

def get_recent_recipes(limit: int = 20):
    """
    Get most recently created recipes
    
    Args:
        limit (int): Maximum number of recipes to return
        
    Returns:
        List[dict]: List of recent recipe dictionaries
        
    Example:
        # Get 20 most recent recipes
        recent = get_recent_recipes(limit=20)
        
        # Get 5 most recent recipes
        latest = get_recent_recipes(limit=5)
    """
    try:
        result = execute_query(
            """SELECT r.RecipeID, r.AuthorID, r.Title, r.Description,
                      r.Ingredients, r.Instructions, r.ImageURL, r.RawIngredients,
                      r.Servings, r.CreatedAt, u.Username as AuthorUsername
               FROM Recipes r
               JOIN Users u ON r.AuthorID = u.UserID
               ORDER BY r.CreatedAt DESC"""
        )
        
        recipes = result[:limit] if result else []
        print(f"✅ Retrieved {len(recipes)} recent recipes")
        return recipes
        
    except Exception as e:
        print(f"❌ Error getting recent recipes: {e}")
        return []

def get_user_activity_feed(user_id: int, limit: int = 20):
    """
    Get activity feed for a user (their likes, favorites, and recipe creations)
    
    Combines different types of user activities into a chronological feed.
    
    Args:
        user_id (int): User ID to get activity feed for
        limit (int): Maximum number of activities to return
        
    Returns:
        List[dict]: List of activity items with type, timestamp, and data
        
    Example:
        # Get user's activity feed
        activities = get_user_activity_feed(user_id=5, limit=20)
        
        for activity in activities:
            print(f"{activity['type']}: {activity['timestamp']}")
    """
    try:
        activities = []
        
        # Get user's recipe creations
        recipes = execute_query(
            """SELECT r.RecipeID, r.Title, r.CreatedAt, 'recipe_created' as ActivityType
               FROM Recipes r
               WHERE r.AuthorID = ?
               ORDER BY r.CreatedAt DESC""",
            (user_id,)
        )
        
        for recipe in recipes:
            activities.append({
                "type": "recipe_created",
                "timestamp": recipe['CreatedAt'],
                "recipe_id": recipe['RecipeID'],
                "recipe_title": recipe['Title'],
                "data": recipe
            })
        
        # Get user's likes
        likes = execute_query(
            """SELECT r.RecipeID, r.Title, l.CreatedAt as LikedAt, 
                      'recipe_liked' as ActivityType, u.Username as RecipeAuthor
               FROM Likes l
               JOIN Recipes r ON l.RecipeID = r.RecipeID
               JOIN Users u ON r.AuthorID = u.UserID
               WHERE l.UserID = ?
               ORDER BY l.CreatedAt DESC""",
            (user_id,)
        )
        
        for like in likes:
            activities.append({
                "type": "recipe_liked",
                "timestamp": like['LikedAt'],
                "recipe_id": like['RecipeID'],
                "recipe_title": like['Title'],
                "recipe_author": like['RecipeAuthor'],
                "data": like
            })
        
        # Get user's favorites
        favorites = execute_query(
            """SELECT r.RecipeID, r.Title, f.CreatedAt as FavoritedAt,
                      'recipe_favorited' as ActivityType, u.Username as RecipeAuthor
               FROM Favorites f
               JOIN Recipes r ON f.RecipeID = r.RecipeID  
               JOIN Users u ON r.AuthorID = u.UserID
               WHERE f.UserID = ?
               ORDER BY f.CreatedAt DESC""",
            (user_id,)
        )
        
        for favorite in favorites:
            activities.append({
                "type": "recipe_favorited", 
                "timestamp": favorite['FavoritedAt'],
                "recipe_id": favorite['RecipeID'],
                "recipe_title": favorite['Title'],
                "recipe_author": favorite['RecipeAuthor'],
                "data": favorite
            })
        
        # Sort all activities by timestamp and limit
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        result = activities[:limit]
        
        print(f"✅ Generated activity feed with {len(result)} items for user {user_id}")
        return result
        
    except Exception as e:
        print(f"❌ Error getting user activity feed: {e}")
        return []

def search_users(query: str, limit: int = 10):
    """
    Search users by username or bio
    
    Args:
        query (str): Search query string
        limit (int): Maximum number of users to return
        
    Returns:
        List[dict]: List of user dictionaries matching the search
        
    Example:
        # Search for users
        users = search_users("chef", limit=5)
        
        # Search for users with specific bio content
        food_lovers = search_users("food lover", limit=10)
    """
    try:
        result = execute_query(
            """SELECT UserID, Username, Email, ProfilePicURL, Bio, CreatedAt
               FROM Users 
               WHERE Username LIKE ? OR Bio LIKE ?
               ORDER BY 
                   CASE WHEN Username LIKE ? THEN 1 ELSE 2 END,
                   Username ASC""",
            (f"%{query}%", f"%{query}%", f"{query}%")
        )
        
        users = result[:limit] if result else []
        print(f"✅ Found {len(users)} users matching '{query}'")
        return users
        
    except Exception as e:
        print(f"❌ Error searching users: {e}")
        return []

def get_database_statistics():
    """
    Get comprehensive database statistics for monitoring and analytics
    
    Returns:
        Dict[str, Any]: Dictionary containing various database statistics
        
    Example:
        stats = get_database_statistics()
        print(f"Total users: {stats['total_users']}")
        print(f"Total recipes: {stats['total_recipes']}")
        print(f"Most active user: {stats['most_active_user']['username']}")
    """
    try:
        stats = {}
        
        # Basic counts
        stats['total_users'] = execute_scalar("SELECT COUNT(*) FROM Users") or 0
        stats['total_recipes'] = execute_scalar("SELECT COUNT(*) FROM Recipes") or 0
        stats['total_tags'] = execute_scalar("SELECT COUNT(*) FROM Tags") or 0
        stats['total_likes'] = execute_scalar("SELECT COUNT(*) FROM Likes") or 0
        stats['total_favorites'] = execute_scalar("SELECT COUNT(*) FROM Favorites") or 0
        stats['total_recipe_tags'] = execute_scalar("SELECT COUNT(*) FROM RecipeTags") or 0
        
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
        
        stats['recent_favorites'] = execute_scalar(
            "SELECT COUNT(*) FROM Favorites WHERE CreatedAt >= DATEADD(day, -7, GETDATE())"
        ) or 0
        
        # Average statistics
        stats['avg_recipes_per_user'] = round(
            (stats['total_recipes'] / stats['total_users']) if stats['total_users'] > 0 else 0, 2
        )
        
        stats['avg_likes_per_recipe'] = round(
            (stats['total_likes'] / stats['total_recipes']) if stats['total_recipes'] > 0 else 0, 2
        )
        
        stats['avg_tags_per_recipe'] = round(
            (stats['total_recipe_tags'] / stats['total_recipes']) if stats['total_recipes'] > 0 else 0, 2
        )
        
        # Top statistics
        most_active_user = execute_query(
            """SELECT TOP 1 u.UserID, u.Username, COUNT(r.RecipeID) as RecipeCount
               FROM Users u
               LEFT JOIN Recipes r ON u.UserID = r.AuthorID
               GROUP BY u.UserID, u.Username
               ORDER BY RecipeCount DESC""",
            fetch="one"
        )
        
        if most_active_user:
            stats['most_active_user'] = {
                'user_id': most_active_user[0]['UserID'],
                'username': most_active_user[0]['Username'],
                'recipe_count': most_active_user[0]['RecipeCount']
            }
        else:
            stats['most_active_user'] = None
        
        most_popular_tag = execute_query(
            """SELECT TOP 1 t.TagID, t.TagName, COUNT(rt.RecipeID) as RecipeCount
               FROM Tags t
               LEFT JOIN RecipeTags rt ON t.TagID = rt.TagID
               GROUP BY t.TagID, t.TagName
               ORDER BY RecipeCount DESC""",
            fetch="one"
        )
        
        if most_popular_tag:
            stats['most_popular_tag'] = {
                'tag_id': most_popular_tag[0]['TagID'],
                'tag_name': most_popular_tag[0]['TagName'],
                'recipe_count': most_popular_tag[0]['RecipeCount']
            }
        else:
            stats['most_popular_tag'] = None
        
        most_liked_recipe = execute_query(
            """SELECT TOP 1 r.RecipeID, r.Title, COUNT(l.UserID) as LikeCount
               FROM Recipes r
               LEFT JOIN Likes l ON r.RecipeID = l.RecipeID
               GROUP BY r.RecipeID, r.Title
               ORDER BY LikeCount DESC""",
            fetch="one"
        )
        
        if most_liked_recipe:
            stats['most_liked_recipe'] = {
                'recipe_id': most_liked_recipe[0]['RecipeID'],
                'title': most_liked_recipe[0]['Title'],
                'like_count': most_liked_recipe[0]['LikeCount']
            }
        else:
            stats['most_liked_recipe'] = None
        
        # Engagement rates
        if stats['total_users'] > 0:
            stats['user_engagement_rate'] = round(
                (stats['recent_users'] / stats['total_users']) * 100, 2
            )
        else:
            stats['user_engagement_rate'] = 0
        
        print("✅ Database statistics compiled successfully")
        return stats
        
    except Exception as e:
        print(f"❌ Error getting database statistics: {e}")
        return {}

def get_popular_recipes_by_tag(tag_name: str, limit: int = 10):
    """
    Get most popular recipes for a specific tag based on likes and favorites
    
    Args:
        tag_name (str): Name of the tag to filter by
        limit (int): Maximum number of recipes to return
        
    Returns:
        List[dict]: List of popular recipe dictionaries for the tag
        
    Example:
        # Get popular Italian recipes
        popular_italian = get_popular_recipes_by_tag("italian", limit=5)
        
        # Get popular vegetarian recipes  
        popular_veggie = get_popular_recipes_by_tag("vegetarian", limit=10)
    """
    try:
        result = execute_query(
            """SELECT r.RecipeID, r.AuthorID, r.Title, r.Description,
                      r.Ingredients, r.Instructions, r.ImageURL, r.RawIngredients,
                      r.Servings, r.CreatedAt, u.Username as AuthorUsername,
                      COUNT(DISTINCT l.UserID) as LikeCount,
                      COUNT(DISTINCT f.UserID) as FavoriteCount,
                      (COUNT(DISTINCT l.UserID) + COUNT(DISTINCT f.UserID)) as PopularityScore
               FROM Recipes r
               JOIN Users u ON r.AuthorID = u.UserID
               JOIN RecipeTags rt ON r.RecipeID = rt.RecipeID
               JOIN Tags t ON rt.TagID = t.TagID
               LEFT JOIN Likes l ON r.RecipeID = l.RecipeID
               LEFT JOIN Favorites f ON r.RecipeID = f.RecipeID
               WHERE t.TagName = ?
               GROUP BY r.RecipeID, r.AuthorID, r.Title, r.Description,
                        r.Ingredients, r.Instructions, r.ImageURL, r.RawIngredients,
                        r.Servings, r.CreatedAt, u.Username
               ORDER BY PopularityScore DESC, r.CreatedAt DESC""",
            (tag_name,)
        )
        
        recipes = result[:limit] if result else []
        print(f"✅ Found {len(recipes)} popular recipes for tag '{tag_name}'")
        return recipes
        
    except Exception as e:
        print(f"❌ Error getting popular recipes by tag: {e}")
        return []

def get_recipe_analytics(recipe_id: int):
    """
    Get detailed analytics for a specific recipe
    
    Args:
        recipe_id (int): Recipe ID to analyze
        
    Returns:
        Dict[str, Any]: Analytics data for the recipe
        
    Example:
        analytics = get_recipe_analytics(recipe_id=5)
        print(f"Total likes: {analytics['total_likes']}")
        print(f"Like rate: {analytics['engagement_rate']}%")
    """
    try:
        # Get basic recipe info
        recipe_info = execute_query(
            """SELECT r.*, u.Username as AuthorUsername
               FROM Recipes r
               JOIN Users u ON r.AuthorID = u.UserID
               WHERE r.RecipeID = ?""",
            (recipe_id,),
            fetch="one"
        )
        
        if not recipe_info:
            return {}
        
        recipe = recipe_info[0]
        analytics = {
            'recipe_id': recipe_id,
            'title': recipe['Title'],
            'author': recipe['AuthorUsername'],
            'created_at': recipe['CreatedAt']
        }
        
        # Get engagement metrics
        analytics['total_likes'] = execute_scalar(
            "SELECT COUNT(*) FROM Likes WHERE RecipeID = ?", (recipe_id,)
        ) or 0
        
        analytics['total_favorites'] = execute_scalar(
            "SELECT COUNT(*) FROM Favorites WHERE RecipeID = ?", (recipe_id,)
        ) or 0
        
        analytics['total_engagement'] = analytics['total_likes'] + analytics['total_favorites']
        
        # Get tag information
        tags = execute_query(
            """SELECT t.TagName FROM Tags t
               JOIN RecipeTags rt ON t.TagID = rt.TagID
               WHERE rt.RecipeID = ?""",
            (recipe_id,)
        )
        analytics['tags'] = [tag['TagName'] for tag in tags] if tags else []
        analytics['tag_count'] = len(analytics['tags'])
        
        # Calculate engagement rate (likes + favorites per day since creation)
        from datetime import datetime
        if recipe['CreatedAt']:
            days_since_creation = max(1, (datetime.now() - recipe['CreatedAt']).days)
            analytics['daily_engagement_rate'] = round(
                analytics['total_engagement'] / days_since_creation, 2
            )
        else:
            analytics['daily_engagement_rate'] = 0
        
        print(f"✅ Analytics compiled for recipe {recipe_id}")
        return analytics
        
    except Exception as e:
        print(f"❌ Error getting recipe analytics: {e}")
        return {}