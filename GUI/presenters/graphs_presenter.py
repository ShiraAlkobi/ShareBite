from PySide6.QtCore import QObject, Signal
from models.graphs_model import GraphsModel, AnalyticsData
from views.graphs_view import GraphsView
from models.login_model import UserData
from typing import Optional

class GraphsPresenter(QObject):
    """
    Presenter for analytics/graphs functionality following MVP pattern
    Mediates between GraphsModel and GraphsView, contains business logic
    """
    
    # Signals for parent application
    home_requested = Signal()
    logout_requested = Signal()
    
    def __init__(self, user_data: UserData, access_token: str, 
                 base_url: str = "http://127.0.0.1:8000", parent=None):
        super().__init__(parent)
        
        # Store user data and token
        self.user_data = user_data
        self.access_token = access_token
        
        # Initialize Model and View
        self.model = GraphsModel(base_url, access_token)
        self.view = GraphsView(user_data)
        
        # Setup connections
        self.setup_model_connections()
        self.setup_view_connections()
        
        # State management
        self.is_loading = False
        self.current_mode = "global"  # Only global mode now
        
        # Load initial data
        self.load_initial_data()
    
    def setup_model_connections(self):
        """Connect model signals to presenter methods"""
        self.model.analytics_data_loaded.connect(self.on_analytics_data_loaded)
        self.model.analytics_load_failed.connect(self.on_analytics_load_failed)
        self.model.network_error.connect(self.on_network_error)
    
    def setup_view_connections(self):
        """Connect view signals to presenter methods"""
        self.view.home_requested.connect(self.home_requested.emit)
        self.view.logout_requested.connect(self.logout_requested.emit)
        self.view.refresh_requested.connect(self.handle_refresh_request)
        self.view.recipe_selected.connect(self.handle_recipe_selection)
    
    def load_initial_data(self):
        """Load initial analytics data - global only"""
        print("Loading initial global analytics data...")
        
        self.is_loading = True
        self.view.set_loading(True)
        
        # Load global analytics
        self.model.load_global_analytics()
    
    def handle_refresh_request(self):
        """Handle refresh request from view - global only"""
        if self.is_loading:
            return
        
        print("Refreshing global analytics data")
        
        self.is_loading = True
        self.view.set_loading(True)
        
        # Always load global analytics
        self.model.load_global_analytics()
    
    def handle_recipe_selection(self, recipe_id: int):
        """
        Handle recipe selection from charts
        
        Args:
            recipe_id (int): Selected recipe ID
        """
        print(f"Recipe selected from analytics: {recipe_id}")
        # This could emit a signal to show recipe details if implemented
        # For now, we'll just log it
        self.view.show_message(f"Recipe {recipe_id} selected", is_error=False)
    
    def on_analytics_data_loaded(self, analytics: AnalyticsData):
        """
        Handle successful analytics data loading - global only
        
        Args:
            analytics (AnalyticsData): Loaded analytics data
        """
        self.is_loading = False
        self.view.set_loading(False)
        
        print(f"Global analytics data loaded successfully")
        print(f"  - {len(analytics.tag_distribution)} tag categories")
        print(f"  - {len(analytics.popular_recipes)} popular recipes")
        print(f"  - {analytics.total_recipes} total recipes")
        print(f"  - {analytics.total_tags} total tags")
        
        # Update view with new data - always global
        self.view.update_analytics_display(analytics, "global")
        
        # Show success message
        self.view.show_message("Loaded global analytics successfully!", is_error=False)
    
    def on_analytics_load_failed(self, error_message: str):
        """
        Handle analytics data loading failure
        
        Args:
            error_message (str): Error message
        """
        self.is_loading = False
        self.view.set_loading(False)
        
        print(f"Analytics data loading failed: {error_message}")
        self.view.show_message(f"Failed to load analytics: {error_message}", is_error=True)
    
    def on_network_error(self, error_message: str):
        """
        Handle network errors
        
        Args:
            error_message (str): Network error message
        """
        self.is_loading = False
        self.view.set_loading(False)
        
        print(f"Network error in analytics: {error_message}")
        self.view.show_message(f"Network Error: {error_message}", is_error=True)
    
    def get_view(self):
        """Return the QWidget of the analytics view"""
        return self.view
    
    def get_model(self):
        """Return the analytics model"""
        return self.model
    
    def show_view(self):
        """Show the analytics view"""
        self.view.show()
        self.view.raise_()
        self.view.activateWindow()
    
    def hide_view(self):
        """Hide the analytics view"""
        self.view.hide()
    
    def close_view(self):
        """Close the analytics view"""
        self.view.close()
    
    def cleanup(self):
        """Clean up resources"""
        self.view.cleanup()
        print("Analytics presenter cleaned up")
    
    def get_current_user(self) -> UserData:
        """Get current user data"""
        return self.user_data
    
    def get_current_mode(self) -> str:
        """Get current view mode - always global now"""
        return self.current_mode
    
    def get_cached_analytics(self) -> Optional[AnalyticsData]:
        """Get cached analytics data"""
        return self.model.get_cached_analytics()