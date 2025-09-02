"""
Data Models for Recipe Sharing Application
Implements MVP pattern - Models handle data and business logic
"""

from PySide6.QtCore import QObject, Signal
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class UserModel(QObject):
    """
    User data model - handles user-related data and operations
    Part of MVP pattern - Model layer
    """
    
    # Signals for UI updates
    user_updated = Signal(dict)
    user_stats_updated = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.user_stats = {}
        self.user_recipes = []
        self.user_favorites = []
        
    def set_current_user(self, user_data: Dict[str, Any]):
        """Set current logged-in user"""
        self.current_user = user_data
        self.user_updated.emit(user_data)
        
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user data"""
        return self.current_user
        
    def update_user_data(self, updated_data: Dict[str, Any]):
        """Update current user data"""
        if self.current_user:
            self.current_user.update(updated_data)
            self.user_updated.emit(self.current_user)
            
    def set_user_stats(self, stats: Dict[str, Any]):
        """Set user statistics"""
        self.user_stats = stats
        self.user_stats_updated.emit(stats)
        
    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        return self.user_stats
        
    def set_user_recipes(self, recipes: List[Dict[str, Any]]):
        """Set user's recipes"""
        self.user_recipes = recipes
        
    def get_user_recipes(self) -> List[Dict[str, Any]]:
        """Get user's recipes"""
        return self.user_recipes
        
    def set_user_favorites(self, favorites: List[Dict[str, Any]]):
        """Set user's favorite recipes"""
        self.user_favorites = favorites
        
    def get_user_favorites(self) -> List[Dict[str, Any]]:
        """Get user's favorite recipes"""
        return self.user_favorites
        
    def clear_user(self):
        """Clear all user data"""
        self.current_user = None
        self.user_stats = {}
        self.user_recipes = []
        self.user_favorites = []
        
    def is_logged_in(self) -> bool:
        """Check if user is logged in"""
        return self.current_user is not None

