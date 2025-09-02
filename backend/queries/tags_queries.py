"""
Tag Queries - CQRS Read Operations

This module handles all READ operations for tags.
Following the same pattern as your recipes_queries.py and users_queries.py
"""

from typing import List, Dict, Any, Optional
from database import execute_query, execute_scalar

class BaseQuery:
    """
    Base class for all tag queries with common functionality
    """
    
    def __init__(self):
        self.cache_enabled = True
        self.cache_ttl = 300  # 5 minutes default cache
    
    def _log_query(self, query_name: str, params: Any = None):
        """Log query execution for monitoring"""
        print(f"🔍 Executing tag query: {query_name} with params: {params}")

class GetAllTagsQuery(BaseQuery):
    """
    Get all available tags with usage statistics
    """
    
    def execute(self, limit: Optional[int] = None, order_by: str = "usage") -> List[Dict[str, Any]]:
        """
        Get all tags with their usage counts
        
        Args:
            limit (int): Maximum number of tags to return
            order_by (str): Order by 'usage', 'name', or 'recent'
            
        Returns:
            List[Dict]: Tag data with usage statistics
        """
        self._log_query("GetAllTags", {"limit": limit, "order_by": order_by})
        
        try:
            # Build base query
            query = """
                SELECT 
                    t.TagID,
                    t.TagName,
                    COUNT(rt.RecipeID) as UsageCount,
                    MAX(r.CreatedAt) as LastUsed
                FROM Tags t
                LEFT JOIN RecipeTags rt ON t.TagID = rt.TagID
                LEFT JOIN Recipes r ON rt.RecipeID = r.RecipeID
                GROUP BY t.TagID, t.TagName
            """
            
            # Add ordering
            if order_by == "usage":
                query += " ORDER BY UsageCount DESC, t.TagName ASC"
            elif order_by == "name":
                query += " ORDER BY t.TagName ASC"
            elif order_by == "recent":
                query += " ORDER BY LastUsed DESC, UsageCount DESC"
            else:
                query += " ORDER BY UsageCount DESC, t.TagName ASC"
            
            # Add limit if specified
            if limit:
                query += f" LIMIT {limit}"
            
            return execute_query(query)
            
        except Exception as e:
            print(f"❌ Error in GetAllTagsQuery: {e}")
            return []

class SearchTagsQuery(BaseQuery):
    """
    Search tags by name pattern
    """
    
    def execute(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for tags matching the search term
        
        Args:
            search_term (str): Search pattern
            limit (int): Maximum results to return
            
        Returns:
            List[Dict]: Matching tags with usage statistics
        """
        self._log_query("SearchTags", {"search_term": search_term, "limit": limit})
        
        try:
            query = """
                SELECT 
                    t.TagID,
                    t.TagName,
                    COUNT(rt.RecipeID) as UsageCount,
                    MAX(r.CreatedAt) as LastUsed
                FROM Tags t
                LEFT JOIN RecipeTags rt ON t.TagID = rt.TagID
                LEFT JOIN Recipes r ON rt.RecipeID = r.RecipeID
                WHERE t.TagName LIKE ?
                GROUP BY t.TagID, t.TagName
                ORDER BY 
                    CASE WHEN t.TagName = ? THEN 1 ELSE 2 END,  -- Exact matches first
                    CASE WHEN t.TagName LIKE ? THEN 1 ELSE 2 END,  -- Starts with pattern next
                    UsageCount DESC,
                    t.TagName ASC
                LIMIT ?
            """
            
            search_pattern = f"%{search_term.lower()}%"
            starts_with_pattern = f"{search_term.lower()}%"
            
            return execute_query(query, (search_pattern, search_term.lower(), starts_with_pattern, limit))
            
        except Exception as e:
            print(f"❌ Error in SearchTagsQuery: {e}")
            return []

class GetPopularTagsQuery(BaseQuery):
    """
    Get most popular tags by usage
    """
    
    def execute(self, limit: int = 10, min_usage: int = 1) -> List[Dict[str, Any]]:
        """
        Get most popular tags based on usage count
        
        Args:
            limit (int): Number of tags to return
            min_usage (int): Minimum usage count to include
            
        Returns:
            List[Dict]: Popular tags
        """
        self._log_query("GetPopularTags", {"limit": limit, "min_usage": min_usage})
        
        try:
            query = """
                SELECT 
                    t.TagID,
                    t.TagName,
                    COUNT(rt.RecipeID) as UsageCount,
                    COUNT(DISTINCT r.AuthorID) as UsedByUsers,
                    MAX(r.CreatedAt) as LastUsed
                FROM Tags t
                JOIN RecipeTags rt ON t.TagID = rt.TagID
                JOIN Recipes r ON rt.RecipeID = r.RecipeID
                GROUP BY t.TagID, t.TagName
                HAVING COUNT(rt.RecipeID) >= ?
                ORDER BY UsageCount DESC, UsedByUsers DESC
                LIMIT ?
            """
            
            return execute_query(query, (min_usage, limit))
            
        except Exception as e:
            print(f"❌ Error in GetPopularTagsQuery: {e}")
            return []

class GetRecentTagsQuery(BaseQuery):
    """
    Get recently created or used tags
    """
    
    def execute(self, limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get tags that were recently created or used
        
        Args:
            limit (int): Number of tags to return
            days (int): Number of days to look back
            
        Returns:
            List[Dict]: Recent tags
        """
        self._log_query("GetRecentTags", {"limit": limit, "days": days})
        
        try:
            query = """
                SELECT 
                    t.TagID,
                    t.TagName,
                    COUNT(rt.RecipeID) as UsageCount,
                    MAX(r.CreatedAt) as LastUsed,
                    t.CreatedAt as TagCreated
                FROM Tags t
                LEFT JOIN RecipeTags rt ON t.TagID = rt.TagID
                LEFT JOIN Recipes r ON rt.RecipeID = r.RecipeID 
                    AND r.CreatedAt >= DATEADD(day, -?, GETDATE())
                WHERE t.CreatedAt >= DATEADD(day, -?, GETDATE()) 
                   OR r.CreatedAt >= DATEADD(day, -?, GETDATE())
                GROUP BY t.TagID, t.TagName, t.CreatedAt
                ORDER BY 
                    CASE 
                        WHEN MAX(r.CreatedAt) IS NOT NULL THEN MAX(r.CreatedAt)
                        ELSE t.CreatedAt
                    END DESC
                LIMIT ?
            """
            
            return execute_query(query, (days, days, days, limit))
            
        except Exception as e:
            print(f"❌ Error in GetRecentTagsQuery: {e}")
            return []

class GetTagByIdQuery(BaseQuery):
    """
    Get detailed information about a specific tag
    """
    
    def execute(self, tag_id: int) -> Optional[Dict[str, Any]]:
        """
        Get complete tag information
        
        Args:
            tag_id (int): Tag ID
            
        Returns:
            Optional[Dict]: Tag data or None if not found
        """
        self._log_query("GetTagById", tag_id)
        
        try:
            query = """
                SELECT 
                    t.TagID,
                    t.TagName,
                    t.CreatedAt,
                    COUNT(DISTINCT rt.RecipeID) as UsageCount,
                    COUNT(DISTINCT r.AuthorID) as UsedByUsers,
                    MIN(r.CreatedAt) as FirstUsed,
                    MAX(r.CreatedAt) as LastUsed
                FROM Tags t
                LEFT JOIN RecipeTags rt ON t.TagID = rt.TagID
                LEFT JOIN Recipes r ON rt.RecipeID = r.RecipeID
                WHERE t.TagID = ?
                GROUP BY t.TagID, t.TagName, t.CreatedAt
            """
            
            result = execute_query(query, (tag_id,), fetch="one")
            return result[0] if result else None
            
        except Exception as e:
            print(f"❌ Error in GetTagByIdQuery: {e}")
            return None

class GetTagByNameQuery(BaseQuery):
    """
    Get tag information by name
    """
    
    def execute(self, tag_name: str) -> Optional[Dict[str, Any]]:
        """
        Get tag by exact name match
        
        Args:
            tag_name (str): Tag name to search for
            
        Returns:
            Optional[Dict]: Tag data or None if not found
        """
        self._log_query("GetTagByName", tag_name)
        
        try:
            query = """
                SELECT 
                    t.TagID,
                    t.TagName,
                    t.CreatedAt,
                    COUNT(DISTINCT rt.RecipeID) as UsageCount,
                    COUNT(DISTINCT r.AuthorID) as UsedByUsers,
                    MIN(r.CreatedAt) as FirstUsed,
                    MAX(r.CreatedAt) as LastUsed
                FROM Tags t
                LEFT JOIN RecipeTags rt ON t.TagID = rt.TagID
                LEFT JOIN Recipes r ON rt.RecipeID = r.RecipeID
                WHERE t.TagName = ?
                GROUP BY t.TagID, t.TagName, t.CreatedAt
            """
            
            result = execute_query(query, (tag_name.lower().strip(),), fetch="one")
            return result[0] if result else None
            
        except Exception as e:
            print(f"❌ Error in GetTagByNameQuery: {e}")
            return None

class GetRecipeTagsQuery(BaseQuery):
    """
    Get all tags associated with a specific recipe
    """
    
    def execute(self, recipe_id: int) -> List[Dict[str, Any]]:
        """
        Get tags for a specific recipe
        
        Args:
            recipe_id (int): Recipe ID
            
        Returns:
            List[Dict]: Tags associated with the recipe
        """
        self._log_query("GetRecipeTags", recipe_id)
        
        try:
            query = """
                SELECT 
                    t.TagID,
                    t.TagName,
                    t.CreatedAt,
                    rt.CreatedAt as AssociatedAt
                FROM Tags t
                JOIN RecipeTags rt ON t.TagID = rt.TagID
                WHERE rt.RecipeID = ?
                ORDER BY t.TagName ASC
            """
            
            return execute_query(query, (recipe_id,))
            
        except Exception as e:
            print(f"❌ Error in GetRecipeTagsQuery: {e}")
            return []

class GetTagStatsQuery(BaseQuery):
    """
    Get comprehensive statistics for tags
    """
    
    def execute(self) -> Dict[str, Any]:
        """
        Get overall tag statistics
        
        Returns:
            Dict: Tag statistics
        """
        self._log_query("GetTagStats", None)
        
        try:
            stats = {}
            
            # Total tags count
            stats['total_tags'] = execute_scalar("SELECT COUNT(*) FROM Tags") or 0
            
            # Tags with usage
            stats['used_tags'] = execute_scalar("""
                SELECT COUNT(DISTINCT t.TagID) 
                FROM Tags t 
                JOIN RecipeTags rt ON t.TagID = rt.TagID
            """) or 0
            
            # Unused tags
            stats['unused_tags'] = stats['total_tags'] - stats['used_tags']
            
            # Average usage per tag
            avg_usage = execute_scalar("""
                SELECT AVG(usage_count)
                FROM (
                    SELECT COUNT(rt.RecipeID) as usage_count
                    FROM Tags t
                    LEFT JOIN RecipeTags rt ON t.TagID = rt.TagID
                    GROUP BY t.TagID
                ) usage_data
            """)
            
            stats['average_usage_per_tag'] = round(avg_usage or 0, 2)
            
            # Most used tag
            most_used = execute_query("""
                SELECT t.TagName, COUNT(rt.RecipeID) as usage_count
                FROM Tags t
                JOIN RecipeTags rt ON t.TagID = rt.TagID
                GROUP BY t.TagID, t.TagName
                ORDER BY usage_count DESC
                LIMIT 1
            """, fetch="one")
            
            if most_used:
                stats['most_used_tag'] = {
                    "name": most_used[0]['TagName'],
                    "usage_count": most_used[0]['usage_count']
                }
            else:
                stats['most_used_tag'] = None
            
            return stats
            
        except Exception as e:
            print(f"❌ Error in GetTagStatsQuery: {e}")
            return {}