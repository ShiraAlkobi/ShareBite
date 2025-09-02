from typing import Dict, Any, Optional, List
from datetime import datetime
from services.recipe_search_service import RecipeSearchService
from services.ollama_client import OllamaClient

class RAGChatService:
    """
    Main RAG service - handles conversation flow, context, and AI coordination
    """
    
    def __init__(self):
        self.recipe_search = RecipeSearchService()
        self.ollama_client = OllamaClient()
        self.conversation_history = {}  # user_id -> conversation list
    
    def process_chat_message(self, user_id: int, user_message: str) -> Dict[str, Any]:
        """
        Main processing pipeline with context awareness
        """
        try:
            print(f"Processing chat from user {user_id}: {user_message}")
            
            # Step 1: Enhance query with conversation context
            enhanced_query = self._enhance_query_with_context(user_id, user_message)
            print(f"Enhanced query: {enhanced_query}")
            
            # Step 2: Analyze intent
            intent = self.recipe_search.analyze_query_intent(enhanced_query)
            
            # Step 3: Smart recipe search
            relevant_recipes = self._smart_recipe_search(intent, enhanced_query)
            print(f"Found {len(relevant_recipes)} relevant recipes")
            
            # Step 4: Generate contextual AI response
            ai_response = self._generate_contextual_response(
                user_id, user_message, relevant_recipes
            )
            
            # Step 5: Store conversation
            self._update_conversation_history(user_id, user_message, ai_response)
            
            return {
                "success": True,
                "response": ai_response,
                "relevant_recipes_count": len(relevant_recipes),
                "recipe_ids": [r.get('RecipeID') for r in relevant_recipes],
                "search_intent": intent['type']
            }
            
        except Exception as e:
            print(f"Error processing chat: {e}")
            return {
                "success": False,
                "response": "I'm having trouble right now. Please try rephrasing your question.",
                "error": str(e)
            }
    
    def _enhance_query_with_context(self, user_id: int, current_message: str) -> str:
        """
        Add conversation context to improve search
        """
        history = self.get_conversation_history(user_id, limit=2)
        if not history:
            return current_message
        
        current_lower = current_message.lower()
        
        # If asking for "new/another recipe", extract context from previous messages
        if any(word in current_lower for word in ['new', 'another', 'different', 'other']):
            # Look for food-related context in recent conversation
            for exchange in reversed(history):  # Most recent first
                prev_message = exchange.get('user_message', '').lower()
                prev_response = exchange.get('ai_response', '').lower()
                
                # Extract food context from previous messages
                food_terms = self._extract_food_context(prev_message + ' ' + prev_response)
                if food_terms:
                    enhanced = f"{current_message} {food_terms[0]}"  # Use most relevant term
                    print(f"Context enhancement: '{current_message}' -> '{enhanced}'")
                    return enhanced
        
        return current_message
    
    def _extract_food_context(self, text: str) -> List[str]:
        """Extract food-related terms from text"""
        food_keywords = [
            'mashed potatoes', 'chicken', 'pasta', 'beef', 'fish', 'rice', 
            'eggs', 'bread', 'soup', 'salad', 'cake', 'cookies', 'pizza',
            'breakfast', 'lunch', 'dinner', 'dessert', 'potatoes', 'vegetables'
        ]
        
        found_terms = []
        text_lower = text.lower()
        
        for keyword in food_keywords:
            if keyword in text_lower:
                found_terms.append(keyword)
        
        return found_terms[:2]  # Return max 2 most relevant
    
    def _smart_recipe_search(self, intent: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """
        Intelligent recipe search with cascading fallbacks
        """
        # Strategy 1: Exact match search (highest priority)
        if intent['type'] == 'general':
            recipes = self.recipe_search.search_recipes_by_exact_match(query, limit=2)
            if recipes:
                return recipes
        
        # Strategy 2: Category search
        if intent['type'] == 'category' and intent['category']:
            recipes = self.recipe_search.search_recipes_by_category(intent['category'], limit=2)
            if recipes:
                return recipes
        
        # Strategy 3: Popular recipes for vague queries
        if intent['specific_request'] == 'popular':
            return self.recipe_search.get_popular_recipes(limit=2)
        
        # Strategy 4: Fallback keyword search
        recipes = self.recipe_search.search_recipes_by_keywords(query, limit=2)
        if recipes:
            return recipes
        
        # Strategy 5: Last resort - popular recipes
        return self.recipe_search.get_popular_recipes(limit=2)
    
    def _generate_contextual_response(self, user_id: int, user_message: str, recipes: List[Dict]) -> str:
        """
        Generate AI response with conversation context
        """
        if not self.ollama_client.test_connection():
            return "AI service is temporarily unavailable. Please try again later."
        
        # Get conversation history for context
        history = self.get_conversation_history(user_id, limit=2)
        
        # Format recipes concisely
        recipe_context = self.recipe_search.format_recipes_for_prompt(recipes)
        
        # Create context-aware prompt
        system_prompt, user_prompt = self._create_contextual_prompt(
            user_message, recipe_context, history
        )
        
        response = self.ollama_client.generate_response(user_prompt, system_prompt)
        
        return response if response else "I'm having trouble generating a response. Please try again."
    
    def _create_contextual_prompt(self, user_message: str, recipes: str, history: List[Dict]) -> tuple:
        """
        Create optimized prompt with context
        """
        system_prompt = """You are a helpful cooking assistant with access to a recipe database.

Rules:
- ALWAYS reference recipes from the database when they match the user's request
- If user asks for "new recipe" or "another recipe", give them something related to previous discussion
- Keep responses concise and practical
- Focus on the recipes provided in the database"""
        
        # Build minimal context
        context = ""
        if history:
            last_exchange = history[-1]
            last_user_msg = last_exchange.get('user_message', '')
            if any(word in last_user_msg.lower() for word in ['mashed potato', 'chicken', 'pasta', 'cake']):
                context = f"Previous request: {last_user_msg}\n\n"
        
        user_prompt = f"""{context}Current request: {user_message}

Available recipes:
{recipes}

Provide a helpful response using the recipes above. If they match what the user wants, recommend them specifically."""
        
        return system_prompt, user_prompt
    
    def _update_conversation_history(self, user_id: int, user_message: str, ai_response: str):
        """Store conversation with size limit"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        # Keep only last 5 exchanges (10 messages total)
        if len(self.conversation_history[user_id]) >= 5:
            self.conversation_history[user_id].pop(0)
        
        self.conversation_history[user_id].append({
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "ai_response": ai_response
        })
    
    def get_conversation_history(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get conversation history"""
        history = self.conversation_history.get(user_id, [])
        return history[-limit:] if history else []
    
    def clear_conversation_history(self, user_id: int):
        """Clear conversation history"""
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]