from PySide6.QtCore import QObject, Signal
import requests
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RecipeData:
    """Data class for recipe information"""
    recipe_id: int
    title: str
    description: str
    author_name: str
    author_id: int
    image_url: Optional[str] = None
    ingredients: Optional[str] = None
    instructions: Optional[str] = None
    raw_ingredients: Optional[str] = None
    servings: Optional[int] = None
    created_at: Optional[str] = None
    likes_count: int = 0
    is_liked: bool = False
    is_favorited: bool = False

@dataclass
class UserStatsData:
    """Data class for user statistics"""
    recipes_created: int = 0
    total_likes_received: int = 0
    total_favorites_received: int = 0
    recipes_liked: int = 0
    recipes_favorited: int = 0

class HomeModel(QObject):
    """
    Model for home page functionality following MVP pattern
    Handles recipe feed data, user stats, and search functionality
    """
    
    # Signals for communication with Presenter
    recipes_loaded = Signal(list)  # List[RecipeData]
    recipes_load_failed = Signal(str)  # error_message
    user_stats_loaded = Signal(UserStatsData)  # user_stats
    recipe_liked = Signal(int, bool)  # recipe_id, is_liked
    recipe_favorited = Signal(int, bool)  # recipe_id, is_favorited
    search_results_loaded = Signal(list)  # List[RecipeData]
    network_error = Signal(str)  # network_error_message
    
    def __init__(self, access_token: str, base_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.base_url = base_url
        self.access_token = access_token
        self.session = requests.Session()
        
        # Set authorization header for all requests
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        })
        
        # Cache
        self.current_recipes: List[RecipeData] = []
        self.current_user_stats: Optional[UserStatsData] = None
        
        # Request timeout
        self.timeout = 30  # seconds
        
        print(f"HomeModel initialized with token: {self.access_token[:20]}...")
    
    def test_authentication(self) -> bool:
        """
        Test if authentication is working by calling /auth/me endpoint
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        try:
            print("Testing authentication...")
            response = self.session.get(
                f"{self.base_url}/api/v1/auth/me",
                timeout=self.timeout
            )
            
            print(f"Auth test response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Auth test successful: {data.get('username')}")
                return True
            else:
                print(f"Auth test failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"Auth test error: {e}")
            return False
    
    def load_recipe_feed(self, limit: int = 5, offset: int = 0) -> None:
        """
        Load recipe feed from API
        
        Args:
            limit (int): Number of recipes to fetch
            offset (int): Number of recipes to skip (for pagination)
        """
        try:
            print(f"🍳 Loading recipe feed (limit: {limit}, offset: {offset})")
            
            response = self.session.get(
                f"{self.base_url}/api/v1/recipes",
                params={"limit": limit, "offset": offset},
                timeout=self.timeout
            )
            
            print(f"📡 Recipe feed response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                recipes = []
                
                for recipe_data in data.get("recipes", []):
                    recipe = RecipeData(
                        recipe_id=recipe_data.get("recipe_id"),
                        title=recipe_data.get("title", "Untitled Recipe"),
                        description=recipe_data.get("description", ""),
                        author_name=recipe_data.get("author_name", "Unknown Chef"),
                        author_id=recipe_data.get("author_id"),
                        image_url=recipe_data.get("image_url"),
                        ingredients=recipe_data.get("ingredients"),
                        instructions=recipe_data.get("instructions"),
                        raw_ingredients=recipe_data.get("raw_ingredients"),
                        servings=recipe_data.get("servings"),
                        created_at=recipe_data.get("created_at"),
                        likes_count=recipe_data.get("likes_count", 0),
                        is_liked=recipe_data.get("is_liked", False),
                        is_favorited=recipe_data.get("is_favorited", False)
                    )
                    recipes.append(recipe)
                
                self.current_recipes = recipes
                self.recipes_loaded.emit(recipes)
                print(f"✅ Loaded {len(recipes)} recipes")
                
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_message = error_data.get("detail", f"Failed to load recipes (Status: {response.status_code})")
                self.recipes_load_failed.emit(error_message)
                
        except requests.exceptions.Timeout:
            self.network_error.emit("Request timed out. Please check your connection.")
        except requests.exceptions.ConnectionError:
            self.network_error.emit("Cannot connect to server. Please check your internet connection.")
        except requests.exceptions.RequestException as e:
            self.network_error.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.recipes_load_failed.emit(f"An unexpected error occurred: {str(e)}")
    
    def search_recipes(self, query: str, filters: Optional[Dict[str, Any]] = None) -> None:
        """
        Search for recipes based on query and filters
        
        Args:
            query (str): Search query
            filters (dict): Additional filters like cuisine, difficulty, etc.
        """
        try:
            print(f"🔍 Searching recipes: '{query}'")
            
            params = {"q": query}
            if filters:
                params.update(filters)
            
            response = self.session.get(
                f"{self.base_url}/api/v1/recipes/search",
                params=params,
                timeout=self.timeout
            )
            
            print(f"📡 Search response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                recipes = []
                
                for recipe_data in data.get("recipes", []):
                    recipe = RecipeData(
                        recipe_id=recipe_data.get("recipe_id"),
                        title=recipe_data.get("title", "Untitled Recipe"),
                        description=recipe_data.get("description", ""),
                        author_name=recipe_data.get("author_name", "Unknown Chef"),
                        author_id=recipe_data.get("author_id"),
                        image_url=recipe_data.get("image_url"),
                        ingredients=recipe_data.get("ingredients"),
                        instructions=recipe_data.get("instructions"),
                        raw_ingredients=recipe_data.get("raw_ingredients"),
                        servings=recipe_data.get("servings"),
                        created_at=recipe_data.get("created_at"),
                        likes_count=recipe_data.get("likes_count", 0),
                        is_liked=recipe_data.get("is_liked", False),
                        is_favorited=recipe_data.get("is_favorited", False)
                    )
                    recipes.append(recipe)
                
                self.search_results_loaded.emit(recipes)
                print(f"✅ Found {len(recipes)} recipes matching '{query}'")
                
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_message = error_data.get("detail", f"Search failed (Status: {response.status_code})")
                self.recipes_load_failed.emit(error_message)
                
        except requests.exceptions.RequestException as e:
            self.network_error.emit(f"Search network error: {str(e)}")
        except Exception as e:
            self.recipes_load_failed.emit(f"Search error: {str(e)}")
    
    def load_user_stats(self) -> None:
        """Load current user statistics"""
        try:
            print("📊 Loading user statistics")
            
            response = self.session.get(
                f"{self.base_url}/api/v1/recipes/user/stats",
                timeout=self.timeout
            )
            
            print(f"📡 User stats response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                stats = UserStatsData(
                    recipes_created=data.get("recipes_created", 0),
                    total_likes_received=data.get("total_likes_received", 0),
                    total_favorites_received=data.get("total_favorites_received", 0),
                    recipes_liked=data.get("recipes_liked", 0),
                    recipes_favorited=data.get("recipes_favorited", 0)
                )
                
                self.current_user_stats = stats
                self.user_stats_loaded.emit(stats)
                print(f"✅ Loaded user stats: {stats}")
                
            else:
                print(f"❌ Failed to load user stats: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error loading user stats: {e}")
    
    def toggle_like_recipe(self, recipe_id: int) -> None:
        """
        Toggle like status for a recipe
        
        Args:
            recipe_id (int): Recipe ID to like/unlike
        """
        try:
            print(f"❤️ Toggling like for recipe {recipe_id}")
            
            response = self.session.post(
                f"{self.base_url}/api/v1/recipes/{recipe_id}/like",
                timeout=self.timeout
            )
            
            print(f"📡 Like toggle response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                is_liked = data.get("is_liked", False)
                
                # Update local cache
                for recipe in self.current_recipes:
                    if recipe.recipe_id == recipe_id:
                        recipe.is_liked = is_liked
                        if is_liked:
                            recipe.likes_count += 1
                        else:
                            recipe.likes_count = max(0, recipe.likes_count - 1)
                        break
                
                self.recipe_liked.emit(recipe_id, is_liked)
                print(f"✅ Recipe {recipe_id} {'liked' if is_liked else 'unliked'}")
                
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_message = error_data.get("detail", "Failed to toggle like")
                self.recipes_load_failed.emit(error_message)
                
        except Exception as e:
            self.network_error.emit(f"Like error: {str(e)}")
    
    def toggle_favorite_recipe(self, recipe_id: int) -> None:
        """
        Toggle favorite status for a recipe
        
        Args:
            recipe_id (int): Recipe ID to favorite/unfavorite
        """
        try:
            print(f"⭐ Toggling favorite for recipe {recipe_id}")
            
            response = self.session.post(
                f"{self.base_url}/api/v1/recipes/{recipe_id}/favorite",
                timeout=self.timeout
            )
            
            print(f"📡 Favorite toggle response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                is_favorited = data.get("is_favorited", False)
                
                # Update local cache
                for recipe in self.current_recipes:
                    if recipe.recipe_id == recipe_id:
                        recipe.is_favorited = is_favorited
                        break
                
                self.recipe_favorited.emit(recipe_id, is_favorited)
                print(f"✅ Recipe {recipe_id} {'favorited' if is_favorited else 'unfavorited'}")
                
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_message = error_data.get("detail", "Failed to toggle favorite")
                self.recipes_load_failed.emit(error_message)
                
        except Exception as e:
            self.network_error.emit(f"Favorite error: {str(e)}")
    
    def refresh_feed(self) -> None:
        """Refresh the recipe feed"""
        self.load_recipe_feed()
    
    def get_cached_recipes(self) -> List[RecipeData]:
        """Get currently cached recipes"""
        return self.current_recipes.copy()
    
    def get_cached_user_stats(self) -> Optional[UserStatsData]:
        """Get currently cached user stats"""
        return self.current_user_stats