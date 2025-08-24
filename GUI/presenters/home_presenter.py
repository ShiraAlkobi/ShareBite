from PySide6.QtCore import QObject, Signal
from models.home_model import HomeModel, RecipeData, UserStatsData
from views.home_view import HomeView
from models.login_model import UserData
from typing import Optional, List, Dict, Any

class HomePresenter(QObject):
    """
    Presenter for home functionality following MVP pattern
    Mediates between HomeModel and HomeView, contains business logic
    """
    
    # Signals for parent application
    recipe_details_requested = Signal(int)  # recipe_id
    add_recipe_requested = Signal()
    user_profile_requested = Signal()
    logout_requested = Signal()
    
    def __init__(self, user_data: UserData, access_token: str, base_url: str = "http://127.0.0.1:8000", parent=None):
        super().__init__(parent)
        
        # Store user information
        self.current_user = user_data
        self.access_token = access_token
        
        # Initialize Model and View
        self.model = HomeModel(access_token, base_url)
        self.view = HomeView(user_data)
        
        # Setup connections
        self.setup_model_connections()
        self.setup_view_connections()
        
        # State management
        self.is_loading = False
        self.current_search_query = ""
        
        # Load initial data
        self.load_initial_data()
    
    def setup_model_connections(self):
        """Connect model signals to presenter methods"""
        self.model.recipes_loaded.connect(self.on_recipes_loaded)
        self.model.recipes_load_failed.connect(self.on_recipes_load_failed)
        self.model.user_stats_loaded.connect(self.on_user_stats_loaded)
        self.model.recipe_liked.connect(self.on_recipe_liked)
        self.model.recipe_favorited.connect(self.on_recipe_favorited)
        self.model.search_results_loaded.connect(self.on_search_results_loaded)
        self.model.network_error.connect(self.on_network_error)
    
    def setup_view_connections(self):
        """Connect view signals to presenter methods"""
        # Navigation signals
        self.view.search_requested.connect(self.handle_search_request)
        self.view.refresh_requested.connect(self.handle_refresh_request)
        self.view.add_recipe_requested.connect(self.add_recipe_requested.emit)
        self.view.user_profile_requested.connect(self.user_profile_requested.emit)
        self.view.logout_requested.connect(self.logout_requested.emit)
        
        # Recipe interaction signals
        self.view.recipe_clicked.connect(self.handle_recipe_clicked)
        self.view.recipe_liked.connect(self.handle_recipe_liked)
        self.view.recipe_favorited.connect(self.handle_recipe_favorited)
        
        # Filter and pagination signals
        self.view.filter_changed.connect(self.handle_filter_changed)
        self.view.load_more_requested.connect(self.handle_load_more_request)
    
    def load_initial_data(self):
        """Load initial data when home screen opens"""
        print("🏠 Loading initial home data...")
        
        # Set loading state
        self.is_loading = True
        self.view.set_loading_state(True)
        
        # Load recipe feed and user stats
        self.model.load_recipe_feed()
        self.model.load_user_stats()
    
    def handle_search_request(self, query: str, filters: Dict[str, Any]):
        """
        Handle search request from view
        
        Args:
            query (str): Search query
            filters (dict): Search filters
        """
        if self.is_loading:
            return
        
        self.current_search_query = query
        self.is_loading = True
        self.view.set_loading_state(True)
        
        print(f"🔍 Handling search request: '{query}' with filters: {filters}")
        
        if query.strip():
            # Perform search
            self.model.search_recipes(query, filters)
        else:
            # Load regular feed if search is empty
            self.model.load_recipe_feed()
    
    def handle_refresh_request(self):
        """Handle refresh request from view"""
        if self.is_loading:
            return
        
        print("🔄 Handling refresh request")
        
        self.is_loading = True
        self.view.set_loading_state(True)
        
        if self.current_search_query:
            # Refresh search results
            self.model.search_recipes(self.current_search_query)
        else:
            # Refresh main feed
            self.model.refresh_feed()
    
    def handle_recipe_clicked(self, recipe_id: int):
        """
        Handle recipe card click
        
        Args:
            recipe_id (int): ID of clicked recipe
        """
        print(f"📖 Recipe clicked: {recipe_id}")
        self.recipe_details_requested.emit(recipe_id)
    
    def handle_recipe_liked(self, recipe_id: int):
        """
        Handle recipe like action
        
        Args:
            recipe_id (int): ID of recipe to like/unlike
        """
        print(f"❤️ Recipe like requested: {recipe_id}")
        self.model.toggle_like_recipe(recipe_id)
    
    def handle_recipe_favorited(self, recipe_id: int):
        """
        Handle recipe favorite action
        
        Args:
            recipe_id (int): ID of recipe to favorite/unfavorite
        """
        print(f"⭐ Recipe favorite requested: {recipe_id}")
        self.model.toggle_favorite_recipe(recipe_id)
    
    def handle_filter_changed(self, filters: Dict[str, Any]):
        """
        Handle filter change from view
        
        Args:
            filters (dict): New filter settings
        """
        print(f"🎛️ Filters changed: {filters}")
        
        if self.is_loading:
            return
        
        self.is_loading = True
        self.view.set_loading_state(True)
        
        if self.current_search_query:
            # Apply filters to current search
            self.model.search_recipes(self.current_search_query, filters)
        else:
            # Apply filters to main feed (could extend API to support this)
            self.model.load_recipe_feed()
    
    def handle_load_more_request(self):
        """Handle load more recipes request (pagination)"""
        if self.is_loading:
            return
        
        print("📄 Load more recipes requested")
        
        current_count = len(self.model.get_cached_recipes())
        self.model.load_recipe_feed(limit=20, offset=current_count)
    
    def on_recipes_loaded(self, recipes: List[RecipeData]):
        """
        Handle successful recipe loading
        
        Args:
            recipes (List[RecipeData]): Loaded recipes
        """
        self.is_loading = False
        self.view.set_loading_state(False)
        self.view.display_recipes(recipes)
        
        print(f"✅ Displayed {len(recipes)} recipes in view")
    
    def on_recipes_load_failed(self, error_message: str):
        """
        Handle failed recipe loading
        
        Args:
            error_message (str): Error message
        """
        self.is_loading = False
        self.view.set_loading_state(False)
        self.view.show_error_message(f"Failed to load recipes: {error_message}")
        
        print(f"❌ Recipe loading failed: {error_message}")
    
    def on_user_stats_loaded(self, stats: UserStatsData):
        """
        Handle successful user stats loading
        
        Args:
            stats (UserStatsData): User statistics
        """
        self.view.display_user_stats(stats)
        print(f"✅ Displayed user stats: {stats}")
    
    def on_recipe_liked(self, recipe_id: int, is_liked: bool):
        """
        Handle successful recipe like/unlike
        
        Args:
            recipe_id (int): Recipe ID
            is_liked (bool): New like status
        """
        self.view.update_recipe_like_status(recipe_id, is_liked)
        print(f"✅ Updated like status for recipe {recipe_id}: {is_liked}")
    
    def on_recipe_favorited(self, recipe_id: int, is_favorited: bool):
        """
        Handle successful recipe favorite/unfavorite
        
        Args:
            recipe_id (int): Recipe ID
            is_favorited (bool): New favorite status
        """
        self.view.update_recipe_favorite_status(recipe_id, is_favorited)
        print(f"✅ Updated favorite status for recipe {recipe_id}: {is_favorited}")
    
    def on_search_results_loaded(self, recipes: List[RecipeData]):
        """
        Handle successful search results loading
        
        Args:
            recipes (List[RecipeData]): Search results
        """
        self.is_loading = False
        self.view.set_loading_state(False)
        self.view.display_search_results(recipes, self.current_search_query)
        
        print(f"✅ Displayed {len(recipes)} search results for '{self.current_search_query}'")
    
    def on_network_error(self, error_message: str):
        """
        Handle network errors
        
        Args:
            error_message (str): Network error message
        """
        self.is_loading = False
        self.view.set_loading_state(False)
        self.view.show_error_message(f"Network Error: {error_message}")
        
        print(f"🌐 Network error: {error_message}")
    
    def show_view(self):
        """Show the home view"""
        self.view.show()
        self.view.raise_()
        self.view.activateWindow()
    
    def hide_view(self):
        """Hide the home view"""
        self.view.hide()
    
    def close_view(self):
        """Close the home view"""
        self.view.close()
    
    def get_view(self) -> HomeView:
        """Get the view instance"""
        return self.view
    
    def get_model(self) -> HomeModel:
        """Get the model instance"""
        return self.model
    
    def get_current_user(self) -> UserData:
        """Get current user data"""
        return self.current_user
    
    def cleanup(self):
        """Cleanup resources"""
        print("🧹 Cleaning up home presenter resources")
        # Any cleanup needed for the presenter