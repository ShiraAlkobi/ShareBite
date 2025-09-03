from PySide6.QtCore import QObject, Signal
import requests
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class TagAnalyticsData:
    """Data class for tag analytics information"""
    tag_name: str
    recipe_count: int
    percentage: float

@dataclass
class RecipePopularityData:
    """Data class for recipe popularity information"""
    recipe_id: int
    title: str
    author_name: str
    likes_count: int

@dataclass
class AnalyticsData:
    """Data class for complete analytics information"""
    tag_distribution: List[TagAnalyticsData]
    popular_recipes: List[RecipePopularityData]
    total_recipes: int
    total_tags: int

class GraphsModel(QObject):
    """
    Model for analytics/graphs functionality following MVP pattern
    Handles analytics data and API communication
    """
    
    # Signals for communication with Presenter
    analytics_data_loaded = Signal(AnalyticsData)  # Analytics data
    analytics_load_failed = Signal(str)  # error_message
    network_error = Signal(str)  # network_error_message
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", access_token: str = None):
        super().__init__()
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = access_token
        self.cached_analytics: Optional[AnalyticsData] = None
        
        # Set authorization header if token provided
        if self.access_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            })
        
        # Request timeout settings
        self.timeout = 10
    
    def load_user_analytics(self, user_id: int) -> None:
        """
        Load analytics data for a specific user
        
        Args:
            user_id (int): User ID to get analytics for
        """
        print(f"Loading analytics data for user: {user_id}")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/analytics/user/{user_id}",
                timeout=self.timeout
            )
            
            print(f"Analytics response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse tag distribution
                tag_distribution = []
                for tag_data in data.get("tag_distribution", []):
                    tag_analytics = TagAnalyticsData(
                        tag_name=tag_data["tag_name"],
                        recipe_count=tag_data["recipe_count"],
                        percentage=tag_data["percentage"]
                    )
                    tag_distribution.append(tag_analytics)
                
                # Parse popular recipes
                popular_recipes = []
                for recipe_data in data.get("popular_recipes", []):
                    recipe_popularity = RecipePopularityData(
                        recipe_id=recipe_data["recipe_id"],
                        title=recipe_data["title"],
                        author_name=recipe_data["author_name"],
                        likes_count=recipe_data["likes_count"]
                    )
                    popular_recipes.append(recipe_popularity)
                
                # Create complete analytics data
                analytics = AnalyticsData(
                    tag_distribution=tag_distribution,
                    popular_recipes=popular_recipes,
                    total_recipes=data.get("total_recipes", 0),
                    total_tags=data.get("total_tags", 0)
                )
                
                self.cached_analytics = analytics
                self.analytics_data_loaded.emit(analytics)
                print(f"Loaded analytics: {len(tag_distribution)} tag categories, {len(popular_recipes)} popular recipes")
                
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_message = error_data.get("detail", f"Failed to load analytics (status: {response.status_code})")
                self.analytics_load_failed.emit(error_message)
                
        except requests.exceptions.Timeout:
            self.network_error.emit("Request timed out. Please check your connection.")
        except requests.exceptions.ConnectionError:
            self.network_error.emit("Cannot connect to server. Please check your internet connection.")
        except requests.exceptions.RequestException as e:
            self.network_error.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.analytics_load_failed.emit(f"An unexpected error occurred: {str(e)}")
    
    def load_global_analytics(self) -> None:
        """
        Load global analytics data for all recipes on the platform
        """
        print("Loading global analytics data")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/analytics/global",
                timeout=self.timeout
            )
            
            print(f"Global analytics response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse tag distribution
                tag_distribution = []
                for tag_data in data.get("tag_distribution", []):
                    tag_analytics = TagAnalyticsData(
                        tag_name=tag_data["tag_name"],
                        recipe_count=tag_data["recipe_count"],
                        percentage=tag_data["percentage"]
                    )
                    tag_distribution.append(tag_analytics)
                
                # Parse popular recipes
                popular_recipes = []
                for recipe_data in data.get("popular_recipes", []):
                    recipe_popularity = RecipePopularityData(
                        recipe_id=recipe_data["recipe_id"],
                        title=recipe_data["title"],
                        author_name=recipe_data["author_name"],
                        likes_count=recipe_data["likes_count"]
                    )
                    popular_recipes.append(recipe_popularity)
                
                # Create complete analytics data
                analytics = AnalyticsData(
                    tag_distribution=tag_distribution,
                    popular_recipes=popular_recipes,
                    total_recipes=data.get("total_recipes", 0),
                    total_tags=data.get("total_tags", 0)
                )
                
                self.cached_analytics = analytics
                self.analytics_data_loaded.emit(analytics)
                print(f"Loaded global analytics: {len(tag_distribution)} tag categories, {len(popular_recipes)} popular recipes")
                
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_message = error_data.get("detail", f"Failed to load global analytics (status: {response.status_code})")
                self.analytics_load_failed.emit(error_message)
                
        except requests.exceptions.Timeout:
            self.network_error.emit("Request timed out. Please check your connection.")
        except requests.exceptions.ConnectionError:
            self.network_error.emit("Cannot connect to server. Please check your internet connection.")
        except requests.exceptions.RequestException as e:
            self.network_error.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.analytics_load_failed.emit(f"An unexpected error occurred: {str(e)}")
    
    def refresh_analytics(self, user_id: Optional[int] = None) -> None:
        """
        Refresh analytics data
        
        Args:
            user_id (int, optional): User ID to refresh data for, if None loads global data
        """
        if user_id:
            self.load_user_analytics(user_id)
        else:
            self.load_global_analytics()
    
    def get_cached_analytics(self) -> Optional[AnalyticsData]:
        """Get cached analytics data"""
        return self.cached_analytics