from PySide6.QtCore import QObject, Signal
from models.home_model import HomeModel, RecipeData
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
    analytics_requested = Signal()
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
        # self.model.user_stats_loaded.connect(self.on_user_stats_loaded)
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
        self.view.analytics_requested.connect(self.analytics_requested.emit)  # Add this line
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
        # self.view.set_loading_state(True)
        
        # Load recipe feed and user stats
        self.model.load_recipe_feed()
        # self.model.load_user_stats()

    def get_view(self):
        """Return the QWidget of the home view"""
        return self.view
    
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
        Handle recipe like action with optimistic updates
        Updates UI immediately, then syncs with server
        """
        print(f"❤️ Recipe like requested: {recipe_id}")
        
        # Find current recipe in cached data
        cached_recipes = self.model.get_cached_recipes()
        current_recipe = None
        for recipe in cached_recipes:
            if recipe.recipe_id == recipe_id:
                current_recipe = recipe
                break
        
        if not current_recipe:
            print(f"Recipe {recipe_id} not found in cache, using fallback")
            # Fallback to original behavior
            self.model.toggle_like_recipe(recipe_id)
            return
        
        # Store original state for potential rollback
        original_like_status = current_recipe.is_liked
        original_likes_count = current_recipe.likes_count
        
        # Calculate optimistic new state
        new_like_status = not original_like_status
        optimistic_likes_count = original_likes_count + (1 if new_like_status else -1)
        optimistic_likes_count = max(0, optimistic_likes_count)  # Don't go below 0
        
        print(f"Optimistic update: Recipe {recipe_id} -> liked: {new_like_status}, count: {optimistic_likes_count}")
        
        # Update UI immediately (optimistic update)
        self.view.update_recipe_like_status(recipe_id, new_like_status, optimistic_likes_count)
        
        # Update local cache immediately
        current_recipe.is_liked = new_like_status
        current_recipe.likes_count = optimistic_likes_count
        
        # Define callback functions for server response
        def on_like_success(actual_recipe_id: int, actual_like_status: bool):
            """Called when server confirms the like action"""
            print(f"✅ Like action confirmed by server: {actual_recipe_id} -> {actual_like_status}")
            
            # Verify server state matches our optimistic update
            if actual_like_status != new_like_status:
                print(f"⚠️ Server state differs from optimistic update, correcting...")
                # Recalculate likes count based on server response
                corrected_count = original_likes_count + (1 if actual_like_status else -1)
                corrected_count = max(0, corrected_count)
                
                self.view.update_recipe_like_status(actual_recipe_id, actual_like_status, corrected_count)
                current_recipe.is_liked = actual_like_status
                current_recipe.likes_count = corrected_count
        
        def on_like_failed(error_message: str):
            """Called when server rejects the like action - rollback optimistic changes"""
            print(f"❌ Like action failed, rolling back: {error_message}")
            
            # Rollback to original state
            current_recipe.is_liked = original_like_status
            current_recipe.likes_count = original_likes_count
            
            # Update view back to original state
            self.view.update_recipe_like_status(recipe_id, original_like_status, original_likes_count)
            
            # Show error to user
            self.view.show_temporary_message(f"Failed to update like: {error_message}", is_error=True)
        
        # Send async request to server with callbacks
        self.model.toggle_like_recipe_optimistic(
            recipe_id, 
            success_callback=on_like_success,
            error_callback=on_like_failed
        )

    def handle_recipe_favorited(self, recipe_id: int):
        """
        Handle recipe favorite action with optimistic updates
        Similar pattern to likes
        """
        print(f"⭐ Recipe favorite requested: {recipe_id}")
        
        # Find current recipe in cached data
        cached_recipes = self.model.get_cached_recipes()
        current_recipe = None
        for recipe in cached_recipes:
            if recipe.recipe_id == recipe_id:
                current_recipe = recipe
                break
        
        if not current_recipe:
            print(f"Recipe {recipe_id} not found in cache, using fallback")
            # Fallback to original behavior
            self.model.toggle_favorite_recipe(recipe_id)
            return
        
        # Store original state
        original_favorite_status = current_recipe.is_favorited
        
        # Calculate optimistic new state
        new_favorite_status = not original_favorite_status
        
        print(f"Optimistic update: Recipe {recipe_id} -> favorited: {new_favorite_status}")
        
        # Update UI immediately
        self.view.update_recipe_favorite_status(recipe_id, new_favorite_status)
        
        # Update local cache immediately
        current_recipe.is_favorited = new_favorite_status
        
        # Define callback functions
        def on_favorite_success(actual_recipe_id: int, actual_favorite_status: bool):
            """Called when server confirms the favorite action"""
            print(f"✅ Favorite action confirmed by server: {actual_recipe_id} -> {actual_favorite_status}")
            
            if actual_favorite_status != new_favorite_status:
                print(f"⚠️ Server state differs from optimistic update, correcting...")
                self.view.update_recipe_favorite_status(actual_recipe_id, actual_favorite_status)
                current_recipe.is_favorited = actual_favorite_status
        
        def on_favorite_failed(error_message: str):
            """Called when server rejects the favorite action"""
            print(f"❌ Favorite action failed, rolling back: {error_message}")
            
            # Rollback to original state
            current_recipe.is_favorited = original_favorite_status
            self.view.update_recipe_favorite_status(recipe_id, original_favorite_status)
            
            # Show error to user
            self.view.show_temporary_message(f"Failed to update favorite: {error_message}", is_error=True)
        
        # Send async request to server
        self.model.toggle_favorite_recipe_optimistic(
            recipe_id,
            success_callback=on_favorite_success,
            error_callback=on_favorite_failed
        )
    
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
    
    # def on_user_stats_loaded(self, stats: UserStatsData):
    #     """
    #     Handle successful user stats loading
        
    #     Args:
    #         stats (UserStatsData): User statistics
    #     """
    #     self.view.display_user_stats(stats)
    #     print(f"✅ Displayed user stats: {stats}")
    
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
    
    def get_view(self):
        """Return the QWidget of the home view"""
        return self.view

    
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