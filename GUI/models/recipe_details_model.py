from PySide6.QtCore import QObject, Signal
import requests
from typing import Optional, Dict, Any
import json

class RecipeDetailsModel(QObject):
    """
    Model for recipe details functionality
    Handles fetching specific recipe data and direct Ollama chat
    """
    
    # Signals
    recipe_loaded = Signal(dict)  # recipe_data
    recipe_load_failed = Signal(str)  # error_message
    ai_response_received = Signal(str)  # response
    ai_response_failed = Signal(str)  # error_message
    network_error = Signal(str)  # error_message
    
    def __init__(self, access_token: str, base_url: str = "http://127.0.0.1:8000", ollama_url: str = "http://localhost:11434"):
        super().__init__()
        self.base_url = base_url
        self.ollama_url = ollama_url
        self.access_token = access_token
        self.session = requests.Session()
        
        # Set authorization header
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        })
        
        # Current recipe data
        self.current_recipe = None
        self.timeout = 30
        self.ollama_timeout = 120  # Longer timeout for AI responses
    
    def load_recipe_details(self, recipe_id: int):
        """Load detailed recipe information"""
        try:
            print(f"Loading recipe details for ID: {recipe_id}")
            
            response = self.session.get(
                f"{self.base_url}/api/v1/recipes/{recipe_id}",
                timeout=self.timeout
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    recipe_data = response.json()
                    print(f"Raw recipe data: {recipe_data}")
                    
                    # Convert the API response to the format expected by the view
                    formatted_recipe = {
                        'recipe_id': recipe_data.get('recipe_id'),
                        'title': recipe_data.get('title', 'Untitled Recipe'),
                        'description': recipe_data.get('description', ''),
                        'author_name': recipe_data.get('author_name', 'Unknown Chef'),
                        'author_id': recipe_data.get('author_id'),
                        'ingredients': recipe_data.get('ingredients', 'No ingredients listed'),
                        'instructions': recipe_data.get('instructions', 'No instructions provided'),
                        'raw_ingredients': recipe_data.get('raw_ingredients'),
                        'servings': recipe_data.get('servings'),
                        'created_at': recipe_data.get('created_at'),
                        'likes_count': recipe_data.get('likes_count', 0),
                        'is_liked': recipe_data.get('is_liked', False),
                        'is_favorited': recipe_data.get('is_favorited', False),
                        'image_url': recipe_data.get('image_url')
                    }
                    
                    self.current_recipe = formatted_recipe
                    print(f"Recipe loaded: {formatted_recipe.get('title', 'Untitled')}")
                    
                    self.recipe_loaded.emit(formatted_recipe)
                    
                except ValueError as json_error:
                    print(f"JSON decode error: {json_error}")
                    self.recipe_load_failed.emit(f"Invalid response format: {str(json_error)}")
                    
            else:
                print(f"HTTP Error: {response.status_code}")
                try:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                    error_message = error_data.get("detail", f"Failed to load recipe (Status: {response.status_code})")
                except:
                    error_message = f"Failed to load recipe (Status: {response.status_code})"
                
                self.recipe_load_failed.emit(error_message)
                
        except requests.exceptions.Timeout:
            print("Request timeout")
            self.network_error.emit("Request timed out")
        except requests.exceptions.ConnectionError:
            print("Connection error")
            self.network_error.emit("Cannot connect to server")
        except Exception as e:
            print(f"Unexpected error: {e}")
            self.recipe_load_failed.emit(f"Error loading recipe: {str(e)}")
    
    def send_chat_message(self, message: str, recipe_context: Dict[str, Any]):
        """Send chat message with better timeout handling"""
        try:
            chat_payload = {
                "message": message,
                "recipe_context": recipe_context
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/recipe-chat",
                json=chat_payload,
                timeout=45  # REDUCED from 90
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("response", "").strip()
                
                if not ai_response:
                    ai_response = "I couldn't generate a response. Please try a simpler question."
                
                self.ai_response_received.emit(ai_response)
            else:
                # Quick fallback response
                self.ai_response_failed.emit("AI service is busy. Please try again.")
                
        except requests.exceptions.Timeout:
            self.ai_response_failed.emit("Response timed out. Try asking a shorter question.")
        except Exception as e:
            self.ai_response_failed.emit("Chat temporarily unavailable.")
            
    def _create_recipe_focused_prompt(self, user_message: str, recipe_context: Dict[str, Any]) -> str:
        """Create a focused prompt with strict length limits"""
        
        # Aggressive truncation for speed
        title = recipe_context.get('title', 'Recipe')[:40]
        ingredients = recipe_context.get('ingredients', 'No ingredients')[:150]
        instructions = recipe_context.get('instructions', 'No instructions')[:200]
        
        # Ultra-concise prompt
        prompt = f"""Recipe: {title}

    Ingredients: {ingredients}

    Instructions: {instructions}

    Q: {user_message}
    A:"""
        
        # Hard limit: 600 characters max
        if len(prompt) > 600:
            prompt = prompt[:597] + "..."
        
        return prompt
    def toggle_like_recipe(self, recipe_id: int):
        """Toggle like status for current recipe"""
        try:
            print(f"Toggling like for recipe: {recipe_id}")
            
            response = self.session.post(
                f"{self.base_url}/api/v1/recipes/{recipe_id}/like",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                is_liked = data.get("is_liked", False)
                
                # Update current recipe data
                if self.current_recipe and self.current_recipe.get('recipe_id') == recipe_id:
                    self.current_recipe['is_liked'] = is_liked
                    if is_liked:
                        self.current_recipe['likes_count'] = self.current_recipe.get('likes_count', 0) + 1
                    else:
                        self.current_recipe['likes_count'] = max(0, self.current_recipe.get('likes_count', 1) - 1)
                
                return is_liked, self.current_recipe.get('likes_count', 0)
            else:
                try:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                    error_message = error_data.get("detail", "Failed to toggle like")
                except:
                    error_message = f"Failed to toggle like (Status: {response.status_code})"
                raise Exception(error_message)
                
        except Exception as e:
            self.network_error.emit(f"Like error: {str(e)}")
            return None, None
    
    def toggle_favorite_recipe(self, recipe_id: int):
        """Toggle favorite status for current recipe"""
        try:
            print(f"Toggling favorite for recipe: {recipe_id}")
            
            response = self.session.post(
                f"{self.base_url}/api/v1/recipes/{recipe_id}/favorite",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                is_favorited = data.get("is_favorited", False)
                
                # Update current recipe data
                if self.current_recipe and self.current_recipe.get('recipe_id') == recipe_id:
                    self.current_recipe['is_favorited'] = is_favorited
                
                return is_favorited
            else:
                try:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                    error_message = error_data.get("detail", "Failed to toggle favorite")
                except:
                    error_message = f"Failed to toggle favorite (Status: {response.status_code})"
                raise Exception(error_message)
                
        except Exception as e:
            self.network_error.emit(f"Favorite error: {str(e)}")
            return None
    
    def get_current_recipe(self) -> Optional[Dict[str, Any]]:
        """Get current recipe data"""
        return self.current_recipe