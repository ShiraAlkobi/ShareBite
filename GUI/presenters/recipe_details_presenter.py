from PySide6.QtCore import QObject, Signal
from models.recipe_details_model import RecipeDetailsModel
from views.recipe_details_view import RecipeDetailsView
from typing import Optional, Dict, Any

class RecipeDetailsPresenter(QObject):
    """
    Presenter for recipe details functionality following MVP pattern
    Mediates between RecipeDetailsModel and RecipeDetailsView
    """
    
    # Signals for parent application
    back_to_home_requested = Signal()
    recipe_updated = Signal(int)  # recipe_id - when like/favorite status changes
    
    def __init__(self, access_token: str, base_url: str = "http://127.0.0.1:8000", parent=None):
        super().__init__(parent)
        
        self.access_token = access_token
        self.current_recipe_id = None
        
        # Initialize Model and View
        self.model = RecipeDetailsModel(access_token, base_url)
        self.view = RecipeDetailsView()
        
        # Setup connections
        self.setup_model_connections()
        self.setup_view_connections()
        
        # State management
        self.is_loading = False
        
        print("Recipe Details Presenter initialized")
    
    def setup_model_connections(self):
        """Connect model signals to presenter methods"""
        self.model.recipe_loaded.connect(self.on_recipe_loaded)
        self.model.recipe_load_failed.connect(self.on_recipe_load_failed)
        self.model.ai_response_received.connect(self.on_ai_response_received)
        self.model.ai_response_failed.connect(self.on_ai_response_failed)
        self.model.network_error.connect(self.on_network_error)
    
    def setup_view_connections(self):
        """Connect view signals to presenter methods"""
        self.view.back_to_home_requested.connect(self.back_to_home_requested.emit)
        self.view.like_recipe_requested.connect(self.handle_like_recipe)
        self.view.favorite_recipe_requested.connect(self.handle_favorite_recipe)
        self.view.chat_message_sent.connect(self.handle_chat_message)
    
    def load_recipe_details(self, recipe_id: int):
        """Load recipe details for display"""
        if self.is_loading:
            return
        
        self.current_recipe_id = recipe_id
        self.is_loading = True
        
        print(f"Loading recipe details for ID: {recipe_id}")
        
        # Load recipe data from model
        self.model.load_recipe_details(recipe_id)
    
    def handle_like_recipe(self, recipe_id: int):
        """Handle recipe like action"""
        print(f"Handling like for recipe: {recipe_id}")
        
        if not self.model.current_recipe:
            print("No current recipe loaded")
            return
        
        # Get current state for optimistic update
        current_recipe = self.model.current_recipe
        original_like_status = current_recipe.get('is_liked', False)
        original_likes_count = current_recipe.get('likes_count', 0)
        
        # Calculate optimistic new state
        new_like_status = not original_like_status
        optimistic_likes_count = original_likes_count + (1 if new_like_status else -1)
        optimistic_likes_count = max(0, optimistic_likes_count)
        
        # Update view immediately (optimistic update)
        self.view.update_like_status(new_like_status, optimistic_likes_count)
        
        # Update model cache immediately
        current_recipe['is_liked'] = new_like_status
        current_recipe['likes_count'] = optimistic_likes_count
        
        # Send request to server
        try:
            actual_like_status, actual_likes_count = self.model.toggle_like_recipe(recipe_id)
            
            if actual_like_status is not None and actual_likes_count is not None:
                # Server response successful, update with actual values
                if actual_like_status != new_like_status or actual_likes_count != optimistic_likes_count:
                    print("Server state differs from optimistic update, correcting...")
                    self.view.update_like_status(actual_like_status, actual_likes_count)
                    current_recipe['is_liked'] = actual_like_status
                    current_recipe['likes_count'] = actual_likes_count
                
                # Notify parent that recipe was updated
                self.recipe_updated.emit(recipe_id)
                
            else:
                # Server request failed, rollback optimistic changes
                print("Like request failed, rolling back")
                self.view.update_like_status(original_like_status, original_likes_count)
                current_recipe['is_liked'] = original_like_status
                current_recipe['likes_count'] = original_likes_count
                
        except Exception as e:
            print(f"Error toggling like: {e}")
            # Rollback on error
            self.view.update_like_status(original_like_status, original_likes_count)
            current_recipe['is_liked'] = original_like_status
            current_recipe['likes_count'] = original_likes_count
    
    def handle_favorite_recipe(self, recipe_id: int):
        """Handle recipe favorite action"""
        print(f"Handling favorite for recipe: {recipe_id}")
        
        if not self.model.current_recipe:
            print("No current recipe loaded")
            return
        
        # Get current state for optimistic update
        current_recipe = self.model.current_recipe
        original_favorite_status = current_recipe.get('is_favorited', False)
        
        # Calculate optimistic new state
        new_favorite_status = not original_favorite_status
        
        # Update view immediately
        self.view.update_favorite_status(new_favorite_status)
        
        # Update model cache immediately
        current_recipe['is_favorited'] = new_favorite_status
        
        # Send request to server
        try:
            actual_favorite_status = self.model.toggle_favorite_recipe(recipe_id)
            
            if actual_favorite_status is not None:
                # Server response successful
                if actual_favorite_status != new_favorite_status:
                    print("Server state differs from optimistic update, correcting...")
                    self.view.update_favorite_status(actual_favorite_status)
                    current_recipe['is_favorited'] = actual_favorite_status
                
                # Notify parent that recipe was updated
                self.recipe_updated.emit(recipe_id)
                
            else:
                # Server request failed, rollback optimistic changes
                print("Favorite request failed, rolling back")
                self.view.update_favorite_status(original_favorite_status)
                current_recipe['is_favorited'] = original_favorite_status
                
        except Exception as e:
            print(f"Error toggling favorite: {e}")
            # Rollback on error
            self.view.update_favorite_status(original_favorite_status)
            current_recipe['is_favorited'] = original_favorite_status
    
    def handle_chat_message(self, message: str, recipe_context: Dict[str, Any]):
        """Handle AI chat message with recipe context"""
        if not recipe_context or not message.strip():
            return
        
        print(f"Sending chat message with recipe context: {message[:50]}...")
        
        # Send to model for AI processing
        self.model.send_chat_message(message, recipe_context)
    
    def on_recipe_loaded(self, recipe_data: dict):
        """Handle successful recipe loading"""
        self.is_loading = False
        
        print(f"Recipe loaded successfully: {recipe_data.get('title', 'Unknown')}")
        
        # Update view with recipe data
        self.view.set_recipe_data(recipe_data)
    
    def on_recipe_load_failed(self, error_message: str):
        """Handle failed recipe loading"""
        self.is_loading = False
        
        print(f"Recipe loading failed: {error_message}")
        
        # Could show error in view or emit signal to parent
        # For now, we'll emit back to home signal
        self.back_to_home_requested.emit()
    
    def on_ai_response_received(self, response: str):
        """Handle AI response from model"""
        print("AI response received, updating view")
        self.view.add_ai_response(response)
    
    def on_ai_response_failed(self, error_message: str):
        """Handle AI response failure"""
        print(f"AI response failed: {error_message}")
        
        # Add error message to chat
        error_response = f"Sorry, I couldn't generate a response right now. Error: {error_message}"
        self.view.add_ai_response(error_response)
    
    def on_network_error(self, error_message: str):
        """Handle network errors"""
        print(f"Network error in recipe details: {error_message}")
        
        # Could show network error in view
        # For now, just log it
    
    def get_view(self):
        """Return the QWidget of the recipe details view"""
        return self.view
    
    def get_model(self):
        """Get the model instance"""
        return self.model
    
    def get_current_recipe_id(self) -> Optional[int]:
        """Get current recipe ID"""
        return self.current_recipe_id
    
    def cleanup(self):
        """Cleanup resources"""
        print("Cleaning up recipe details presenter resources")
        
        # Cleanup model resources (if the model has cleanup)
        if hasattr(self.model, 'cleanup'):
            self.model.cleanup()
        
        # Cleanup view resources (including image loading)
        if hasattr(self.view, 'cleanup'):
            self.view.cleanup()
        
        # Reset loading states
        self.is_loading = False