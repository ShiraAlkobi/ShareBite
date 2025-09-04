from PySide6.QtCore import QObject, Signal
from models.add_recipe_model import AddRecipeModel
from models.login_model import UserData
from views.add_recipe_view import AddRecipeView
from typing import Optional, List, Dict, Any

class AddRecipePresenter(QObject):
    """
    Presenter for add recipe functionality following MVP pattern
    Mediates between Model and View, contains business logic
    """
    
    # Signals for parent application
    home_requested = Signal()
    logout_requested = Signal()
    recipe_created = Signal(int)  # recipe_id
    
    def __init__(self, user_data: UserData, access_token: str, 
                 base_url: str = "http://127.0.0.1:8000", parent=None):
        super().__init__(parent)
        
        # Store user data and token
        self.user_data = user_data
        self.access_token = access_token
        
        # Initialize Model and View
        self.model = AddRecipeModel(base_url, access_token)
        self.view = AddRecipeView(user_data)
        
        # Setup connections
        self.setup_model_connections()
        self.setup_view_connections()
        
        # State management
        self.is_creating = False

        
        # Load available tags on initialization
        self.load_available_tags()
    
    def setup_model_connections(self):
        """Connect model signals to presenter methods"""
        self.model.tags_loaded.connect(self.on_tags_loaded)
        self.model.recipe_created.connect(self.on_recipe_created)
        self.model.creation_error.connect(self.on_creation_error)
        self.model.network_error.connect(self.on_network_error)
    
    def setup_view_connections(self):
        """Connect view signals to presenter methods"""
        self.view.home_requested.connect(self.home_requested.emit)
        self.view.logout_requested.connect(self.logout_requested.emit)
        self.view.recipe_creation_requested.connect(self.handle_recipe_creation)
        self.view.tags_load_requested.connect(self.load_available_tags)
    
    def load_available_tags(self):
        """Load available tags from the server"""
        print("Loading available tags...")
        self.model.load_available_tags()
    
    def handle_recipe_creation(self, recipe_data: Dict[str, Any]):
        """
        Handle recipe creation request from view
        
        Args:
            recipe_data (Dict): Recipe data from the form
        """
        if self.is_creating:
            return
        
        print(f"Handling recipe creation: {recipe_data['title']}")
        
        self.is_creating = True
        
        # Show loading state
        self.view.show_message("Creating recipe...", is_error=False)
        
        # Create recipe directly with URL (no separate upload needed)
        self.create_recipe_with_data(recipe_data)
    

    
    def create_recipe_with_data(self, recipe_data: Dict[str, Any]):
        """
        Create recipe with the provided data
        
        Args:
            recipe_data (Dict): Recipe data
        """
        # Prepare recipe creation data
        creation_data = {
            'author_id': self.user_data.userid,
            'title': recipe_data['title'],
            'description': recipe_data.get('description'),
            'ingredients': recipe_data['ingredients'],
            'instructions': recipe_data['instructions'],
            'servings': recipe_data.get('servings'),
            'image_url': recipe_data.get('image_url'),  # Use URL directly
            'tags': recipe_data.get('tags', [])
        }
        
        print(f"Creating recipe with data: {creation_data['title']}")
        if creation_data['image_url']:
            print(f"Image URL: {creation_data['image_url']}")
        
        self.model.create_recipe(creation_data)
    
    def on_tags_loaded(self, tags: List[str]):
        """
        Handle successful tags loading
        
        Args:
            tags (List[str]): Available tags
        """
        print(f"Tags loaded: {len(tags)} tags")
        self.view.set_available_tags(tags)
    
    def on_recipe_created(self, recipe_id: int, message: str):
        """
        Handle successful recipe creation
        
        Args:
            recipe_id (int): Created recipe ID
            message (str): Success message
        """
        print(f"Recipe created successfully: ID {recipe_id}")
        
        self.is_creating = False
         
        # Show success message
        self.view.show_message(f"Recipe created successfully! {message}", is_error=False)
        
        # Clear form
        self.view.clear_form()
        
        # Emit signal to parent
        self.recipe_created.emit(recipe_id)
        
        # Navigate back to home after a short delay
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, self.home_requested.emit)
    

    
    def on_creation_error(self, error_message: str):
        """
        Handle recipe creation error
        
        Args:
            error_message (str): Error message
        """
        self.is_creating = False

        
        print(f"Recipe creation error: {error_message}")
        self.view.show_message(f"Error creating recipe: {error_message}", is_error=True)
    
    def on_network_error(self, error_message: str):
        """
        Handle network error
        
        Args:
            error_message (str): Network error message
        """
        self.is_creating = False
        
        print(f"Network error: {error_message}")
        self.view.show_message(f"Network Error: {error_message}", is_error=True)
    
    def get_view(self):
        """Return the QWidget of the add recipe view"""
        return self.view
    
    def get_model(self):
        """Return the add recipe model"""
        return self.model
    
    def show_view(self):
        """Show the add recipe view"""
        self.view.show()
        self.view.raise_()
        self.view.activateWindow()
    
    def hide_view(self):
        """Hide the add recipe view"""
        self.view.hide()
    
    def close_view(self):
        """Close the add recipe view"""
        self.view.close()
    
    def cleanup(self):
        """Clean up resources"""
        self.view.cleanup()
        print("Add recipe presenter cleaned up")
    
    def get_current_user(self) -> UserData:
        """Get current user data"""
        return self.user_data
    
