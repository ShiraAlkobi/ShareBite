from .base_model import BaseModel
from database import execute_query, execute_non_query, execute_scalar, insert_and_get_id
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

class Chat(BaseModel):
    """
    Chat model for managing AI conversation history and chat-related database operations
    
    This model handles conversation history storage and retrieval for the RAG chat service
    """
    
    def __init__(self):
        self.chatid = None
        self.userid = None
        self.message = None
        self.response = None
        self.search_intent = None
        self.relevant_recipes_count = None
        self.recipe_ids = None
        self.createdat = None
    
    @classmethod
    def save_conversation(cls, user_id: int, message: str, response: str, search_intent: str = None, 
                         relevant_recipes_count: int = 0, recipe_ids: List[int] = None) -> Optional[int]:
        """
        Save a conversation exchange to the database
        
        Args:
            user_id (int): User ID
            message (str): User's message
            response (str): AI's response
            search_intent (str): Detected search intent
            relevant_recipes_count (int): Number of relevant recipes found
            recipe_ids (List[int]): List of relevant recipe IDs
            
        Returns:
            Optional[int]: Chat ID if successful, None otherwise
        """
        try:
            # Convert recipe_ids list to JSON string if provided
            recipe_ids_json = json.dumps(recipe_ids) if recipe_ids else None
            
            chat_id = insert_and_get_id(
                "ChatHistory",  # Assuming you have a ChatHistory table
                ["UserID", "Message", "Response", "SearchIntent", "RelevantRecipesCount", "RecipeIDs"],
                (user_id, message, response, search_intent, relevant_recipes_count, recipe_ids_json)
            )
            
            print(f"Chat conversation saved with ID: {chat_id}")
            return chat_id
            
        except Exception as e:
            print(f"Error saving chat conversation: {e}")
            return None
    
    @classmethod
    def get_conversation_history(cls, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get conversation history for a user
        
        Args:
            user_id (int): User ID
            limit (int): Maximum number of conversations to return
            
        Returns:
            List[Dict]: List of conversation history items
        """
        try:
            result = execute_query(
                """SELECT ChatID, Message, Response, SearchIntent, RelevantRecipesCount, 
                          RecipeIDs, CreatedAt
                   FROM ChatHistory 
                   WHERE UserID = ?
                   ORDER BY CreatedAt DESC""",
                (user_id,)
            )
            
            history = []
            for row in result[:limit]:
                # Parse recipe_ids JSON if present
                recipe_ids = []
                if row.get('RecipeIDs'):
                    try:
                        recipe_ids = json.loads(row['RecipeIDs'])
                    except (json.JSONDecodeError, TypeError):
                        recipe_ids = []
                
                history.append({
                    "chat_id": row['ChatID'],
                    "message": row['Message'],
                    "response": row['Response'],
                    "search_intent": row.get('SearchIntent'),
                    "relevant_recipes_count": row.get('RelevantRecipesCount', 0),
                    "recipe_ids": recipe_ids,
                    "timestamp": row['CreatedAt']
                })
            
            return history
            
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []
    
    @classmethod
    def clear_conversation_history(cls, user_id: int) -> bool:
        """
        Clear conversation history for a user
        
        Args:
            user_id (int): User ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            rows_affected = execute_non_query(
                "DELETE FROM ChatHistory WHERE UserID = ?",
                (user_id,)
            )
            
            print(f"Cleared {rows_affected} conversation history items for user {user_id}")
            return True
            
        except Exception as e:
            print(f"Error clearing conversation history: {e}")
            return False
    
    @classmethod
    def get_recent_chat_activity(cls, days: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent chat activity across all users for analytics
        
        Args:
            days (int): Number of days to look back
            limit (int): Maximum number of activities to return
            
        Returns:
            List[Dict]: List of recent chat activities
        """
        try:
            result = execute_query(
                """SELECT c.ChatID, c.UserID, u.Username, c.Message, c.Response,
                          c.SearchIntent, c.RelevantRecipesCount, c.CreatedAt
                   FROM ChatHistory c
                   JOIN Users u ON c.UserID = u.UserID
                   WHERE c.CreatedAt >= DATEADD(day, -?, GETDATE())
                   ORDER BY c.CreatedAt DESC""",
                (days,)
            )
            
            activities = []
            for row in result[:limit]:
                activities.append({
                    "chat_id": row['ChatID'],
                    "user_id": row['UserID'],
                    "username": row['Username'],
                    "message": row['Message'][:100] + "..." if len(row['Message']) > 100 else row['Message'],  # Truncate for privacy
                    "search_intent": row.get('SearchIntent'),
                    "relevant_recipes_count": row.get('RelevantRecipesCount', 0),
                    "timestamp": row['CreatedAt']
                })
            
            return activities
            
        except Exception as e:
            print(f"Error getting recent chat activity: {e}")
            return []
    
    @classmethod
    def get_chat_statistics(cls, user_id: int = None) -> Dict[str, Any]:
        """
        Get chat statistics for a user or globally
        
        Args:
            user_id (int, optional): User ID for user-specific stats, None for global stats
            
        Returns:
            Dict: Chat statistics
        """
        try:
            stats = {}
            
            if user_id:
                # User-specific statistics
                stats['total_conversations'] = execute_scalar(
                    "SELECT COUNT(*) FROM ChatHistory WHERE UserID = ?",
                    (user_id,)
                ) or 0
                
                stats['recent_conversations'] = execute_scalar(
                    """SELECT COUNT(*) FROM ChatHistory 
                       WHERE UserID = ? AND CreatedAt >= DATEADD(day, -7, GETDATE())""",
                    (user_id,)
                ) or 0
                
                stats['avg_recipes_per_query'] = execute_scalar(
                    """SELECT AVG(CAST(RelevantRecipesCount AS FLOAT)) 
                       FROM ChatHistory 
                       WHERE UserID = ? AND RelevantRecipesCount > 0""",
                    (user_id,)
                ) or 0
                
            else:
                # Global statistics
                stats['total_conversations'] = execute_scalar(
                    "SELECT COUNT(*) FROM ChatHistory"
                ) or 0
                
                stats['total_users_with_chats'] = execute_scalar(
                    "SELECT COUNT(DISTINCT UserID) FROM ChatHistory"
                ) or 0
                
                stats['recent_conversations'] = execute_scalar(
                    """SELECT COUNT(*) FROM ChatHistory 
                       WHERE CreatedAt >= DATEADD(day, -7, GETDATE())"""
                ) or 0
                
                stats['avg_conversations_per_user'] = round(
                    (stats['total_conversations'] / stats['total_users_with_chats']) 
                    if stats['total_users_with_chats'] > 0 else 0, 2
                )
            
            return stats
            
        except Exception as e:
            print(f"Error getting chat statistics: {e}")
            return {}
    
    @classmethod
    def get_popular_search_intents(cls, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most popular search intents from chat history
        
        Args:
            limit (int): Maximum number of intents to return
            
        Returns:
            List[Dict]: List of popular search intents with counts
        """
        try:
            result = execute_query(
                """SELECT SearchIntent, COUNT(*) as IntentCount
                   FROM ChatHistory
                   WHERE SearchIntent IS NOT NULL AND SearchIntent != ''
                   GROUP BY SearchIntent
                   ORDER BY IntentCount DESC"""
            )
            
            intents = []
            for row in result[:limit]:
                intents.append({
                    "search_intent": row['SearchIntent'],
                    "count": row['IntentCount']
                })
            
            return intents
            
        except Exception as e:
            print(f"Error getting popular search intents: {e}")
            return []
    
    def save(self) -> bool:
        """
        Save chat instance to database
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.chatid is None:
                # Create new chat record
                recipe_ids_json = json.dumps(self.recipe_ids) if self.recipe_ids else None
                
                chat_id = insert_and_get_id(
                    "ChatHistory",
                    ["UserID", "Message", "Response", "SearchIntent", "RelevantRecipesCount", "RecipeIDs"],
                    (self.userid, self.message, self.response, self.search_intent, 
                     self.relevant_recipes_count, recipe_ids_json)
                )
                self.chatid = chat_id
                print(f"Chat record created with ID: {chat_id}")
                return True
            else:
                # Update existing chat record (if needed)
                recipe_ids_json = json.dumps(self.recipe_ids) if self.recipe_ids else None
                
                rows_affected = execute_non_query(
                    """UPDATE ChatHistory 
                       SET Message = ?, Response = ?, SearchIntent = ?, 
                           RelevantRecipesCount = ?, RecipeIDs = ?
                       WHERE ChatID = ?""",
                    (self.message, self.response, self.search_intent,
                     self.relevant_recipes_count, recipe_ids_json, self.chatid)
                )
                print(f"Chat record updated, {rows_affected} rows affected")
                return rows_affected > 0
                
        except Exception as e:
            print(f"Error saving chat record: {e}")
            return False