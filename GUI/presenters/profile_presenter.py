from PySide6.QtCore import QObject, Signal
from models.profile_model import ProfileModel, Recipe
from models.login_model import UserData
from views.profile_view import ProfileView
from typing import Optional, List

class ProfilePresenter(QObject):
    """
    Presenter for profile functionality following MVP pattern
    Mediates between Model and View, contains business logic
    """
    
    # Signals for parent application
    home_requested = Signal()
    logout_requested = Signal()
    recipe_details_requested = Signal(int)  # recipe_id
    profile_data_loaded = Signal()
    
    def __init__(self, user_data: UserData, access_token: str, 
                 base_url: str = "http://127.0.0.1:8000", parent=None):
        super().__init__(parent)
        
        # Store user data and token
        self.user_data = user_data
        self.access_token = access_token
        
        # Initialize Model and View
        self.model = ProfileModel(base_url, access_token)
        self.view = ProfileView(user_data)
        
        # Setup connections
        self.setup_model_connections()
        self.setup_view_connections()
        
        # State management
        self.is_loading = False
        
        # Load initial data
        self.load_profile_data()
    
    def setup_model_connections(self):
        """Connect model signals to presenter methods"""
        self.model.user_recipes_loaded.connect(self.on_user_recipes_loaded)
        self.model.favorite_recipes_loaded.connect(self.on_favorite_recipes_loaded)
        self.model.user_data_updated.connect(self.on_user_data_updated)
        self.model.recipe_like_toggled.connect(self.on_recipe_like_toggled)
        self.model.profile_updated.connect(self.on_profile_updated)
        self.model.data_loading_error.connect(self.on_data_error)
        self.model.network_error.connect(self.on_network_error)
    
    def setup_view_connections(self):
        """Connect view signals to presenter methods"""
        self.view.home_requested.connect(self.home_requested.emit)
        self.view.logout_requested.connect(self.logout_requested.emit)
        self.view.recipe_selected.connect(self.handle_recipe_selection)
        self.view.recipe_like_toggled.connect(self.handle_recipe_like_toggle)
        self.view.profile_edit_requested.connect(self.handle_profile_edit_request)
        self.view.profile_update_submitted.connect(self.handle_profile_update)
        self.view.refresh_requested.connect(self.handle_refresh_request)
    
    def load_profile_data(self):
        """Load all profile data from the server"""
        if self.is_loading:
            return
        
        self.is_loading = True
        self.view.set_loading(True)
        
        print(f"Loading profile data for user: {self.user_data.username}")
        
        # Load user's recipes and favorites
        self.model.load_user_recipes(self.user_data.userid)
        self.model.load_favorite_recipes(self.user_data.userid)
    
    def handle_recipe_selection(self, recipe_id: int):
        """
        Handle recipe selection from view
        
        Args:
            recipe_id (int): Selected recipe ID
        """
        print(f"Recipe selected: {recipe_id}")
        self.recipe_details_requested.emit(recipe_id)
    
    def handle_recipe_like_toggle(self, recipe_id: int):
        """
        Handle recipe like toggle from view
        
        Args:
            recipe_id (int): Recipe ID to toggle like
        """
        if self.is_loading:
            return
        
        print(f"Toggling like for recipe: {recipe_id}")
        self.model.toggle_recipe_like(recipe_id)
    
    def handle_profile_edit_request(self):
        """Handle request to edit profile"""
        print("Profile edit requested")
        self.view.show_edit_dialog()
    
    def handle_profile_update(self, username: str, email: str, bio: str):
        """
        Handle profile update submission
        
        Args:
            username (str): New username
            email (str): New email
            bio (str): New bio
        """
        if self.is_loading:
            return
        
        print(f"Updating profile: {username}, {email}")
        
        self.is_loading = True
        self.view.set_loading(True)
        
        # Only send changed values
        new_username = username if username != self.user_data.username else None
        new_email = email if email != self.user_data.email else None
        new_bio = bio if bio != (self.user_data.bio or "") else None
        
        self.model.update_user_profile(
            self.user_data.userid,
            username=new_username,
            email=new_email,
            bio=new_bio
        )
    
    def handle_refresh_request(self):
        """Handle request to refresh profile data"""
        print("Refresh requested")
        self.load_profile_data()
    
    def on_user_recipes_loaded(self, recipes: List[Recipe]):
        """
        Handle successful user recipes loading
        
        Args:
            recipes (List[Recipe]): Loaded recipes
        """
        print(f"User recipes loaded: {len(recipes)} recipes")
        self.view.update_user_recipes(recipes)
        self.check_loading_complete()
    
    def on_favorite_recipes_loaded(self, recipes: List[Recipe]):
        """
        Handle successful favorite recipes loading
        
        Args:
            recipes (List[Recipe]): Loaded favorite recipes
        """
        print(f"Favorite recipes loaded: {len(recipes)} recipes")
        self.view.update_favorite_recipes(recipes)
        self.check_loading_complete()
    
    def on_user_data_updated(self, user_data: UserData):
        """
        Handle successful user data update
        
        Args:
            user_data (UserData): Updated user data
        """
        print(f"User data updated: {user_data.username}")
        self.user_data = user_data
        self.view.update_user_info(user_data)
        self.is_loading = False
        self.view.set_loading(False)
        self.view.hide_edit_dialog()
    
    def on_recipe_like_toggled(self, recipe_id: int, is_liked: bool):
        """
        Handle successful recipe like toggle
        
        Args:
            recipe_id (int): Recipe ID
            is_liked (bool): New like status
        """
        print(f"Recipe {recipe_id} like status: {is_liked}")
        self.view.update_recipe_like_status(recipe_id, is_liked)
        
        # If recipe was unliked from favorites, reload favorites
        if not is_liked:
            # Small delay to allow server to update, then reload
            from PySide6.QtCore import QTimer
            QTimer.singleShot(500, lambda: self.model.load_favorite_recipes(self.user_data.userid))
    
    def on_profile_updated(self, message: str):
        """
        Handle successful profile update
        
        Args:
            message (str): Success message
        """
        print(f"Profile updated: {message}")
        self.view.show_message(message, is_error=False)
    
    def on_data_error(self, error_message: str):
        """
        Handle data loading error
        
        Args:
            error_message (str): Error message
        """
        self.is_loading = False
        self.view.set_loading(False)
        self.view.show_message(error_message, is_error=True)
        print(f"Data error: {error_message}")
    
    def on_network_error(self, error_message: str):
        """
        Handle network error
        
        Args:
            error_message (str): Network error message
        """
        self.is_loading = False
        self.view.set_loading(False)
        self.view.show_message(f"Network Error: {error_message}", is_error=True)
        print(f"Network error: {error_message}")
    
    def check_loading_complete(self):
        """Check if all initial data has been loaded"""
        # Simple check - if we have both user and favorite recipes loaded
        if (hasattr(self.view, '_user_recipes_loaded') and 
            hasattr(self.view, '_favorite_recipes_loaded')):
            self.is_loading = False
            self.view.set_loading(False)
            self.profile_data_loaded.emit()
            print("Profile data loading complete")
    
    def get_view(self):
        """Return the QWidget of the profile view"""
        return self.view
    
    def get_model(self):
        """Return the profile model"""
        return self.model
    
    def show_view(self):
        """Show the profile view"""
        self.view.show()
        self.view.raise_()
        self.view.activateWindow()
    
    def hide_view(self):
        """Hide the profile view"""
        self.view.hide()
    
    def close_view(self):
        """Close the profile view"""
        self.view.close()
    
    def cleanup(self):
        """Clean up resources"""
        self.view.cleanup()
        print("Profile presenter cleaned up")
    
    def get_current_user(self) -> UserData:
        """Get current user data"""
        return self.user_data