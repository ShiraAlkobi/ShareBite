from PySide6.QtCore import QObject, Signal
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

class RecipeModel(QObject):
    """
    Recipe data model - handles recipe-related data and operations
    Part of MVP pattern - Model layer
    """
    
    # Signals for UI updates
    recipes_updated = Signal(list)
    recipe_updated = Signal(dict)
    recipe_deleted = Signal(int)
    recipe_liked = Signal(int, bool)
    recipe_favorited = Signal(int, bool)
    
    def __init__(self):
        super().__init__()
        self.recent_recipes = []
        self.trending_recipes = []
        self.search_results = []
        self.current_recipe = None
        self.user_interactions = {}  # recipe_id -> {liked: bool, favorited: bool}
        
    def set_recent_recipes(self, recipes: List[Dict[str, Any]]):
        """Set recent recipes"""
        self.recent_recipes = recipes
        self.recipes_updated.emit(recipes)
        
    def get_recent_recipes(self) -> List[Dict[str, Any]]:
        """Get recent recipes"""
        return self.recent_recipes
        
    def set_trending_recipes(self, recipes: List[Dict[str, Any]]):
        """Set trending recipes"""
        self.trending_recipes = recipes
        
    def get_trending_recipes(self) -> List[Dict[str, Any]]:
        """Get trending recipes"""
        return self.trending_recipes
        
    def set_search_results(self, recipes: List[Dict[str, Any]]):
        """Set search results"""
        self.search_results = recipes
        self.recipes_updated.emit(recipes)
        
    def get_search_results(self) -> List[Dict[str, Any]]:
        """Get search results"""
        return self.search_results
        
    def set_current_recipe(self, recipe: Dict[str, Any]):
        """Set current recipe being viewed"""
        self.current_recipe = recipe
        self.recipe_updated.emit(recipe)
        
    def get_current_recipe(self) -> Optional[Dict[str, Any]]:
        """Get current recipe"""
        return self.current_recipe
        
    def update_recipe(self, recipe_id: int, updated_data: Dict[str, Any]):
        """Update recipe data"""
        # Update in all lists
        for recipe_list in [self.recent_recipes, self.trending_recipes, self.search_results]:
            for recipe in recipe_list:
                if recipe.get('recipe_id') == recipe_id:
                    recipe.update(updated_data)
                    
        # Update current recipe if it's the same
        if self.current_recipe and self.current_recipe.get('recipe_id') == recipe_id:
            self.current_recipe.update(updated_data)
            self.recipe_updated.emit(self.current_recipe)
            
    def remove_recipe(self, recipe_id: int):
        """Remove recipe from all lists"""
        # Remove from all lists
        for recipe_list in [self.recent_recipes, self.trending_recipes, self.search_results]:
            recipe_list[:] = [r for r in recipe_list if r.get('recipe_id') != recipe_id]
            
        # Clear current recipe if it's the deleted one
        if self.current_recipe and self.current_recipe.get('recipe_id') == recipe_id:
            self.current_recipe = None
            
        self.recipe_deleted.emit(recipe_id)
        
    def set_user_interactions(self, interactions: Dict[int, Dict[str, bool]]):
        """Set user interactions with recipes"""
        self.user_interactions = interactions
        
    def update_like_status(self, recipe_id: int, liked: bool, like_count: int = None):
        """Update like status for recipe"""
        if recipe_id not in self.user_interactions:
            self.user_interactions[recipe_id] = {}
            
        self.user_interactions[recipe_id]['liked'] = liked
        
        # Update like count