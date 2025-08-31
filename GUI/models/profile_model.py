from PySide6.QtCore import QObject, Signal
import requests
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from models.login_model import UserData

@dataclass
class Recipe:
    """Data class for recipe information"""
    recipe_id: int
    title: str
    description: str
    ingredients: List[str]
    instructions: List[str]
    image_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    likes_count: int = 0
    author_username: str = ""
    is_liked: bool = False

class ProfileModel(QObject):
    """
    Model for profile functionality following MVP pattern
    Handles profile data and API communication
    """
    
    # Signals for communication with Presenter
    user_recipes_loaded = Signal(list)  # List[Recipe]
    favorite_recipes_loaded = Signal(list)  # List[Recipe]
    user_data_updated = Signal(UserData)  # Updated user data
    recipe_like_toggled = Signal(int, bool)  # recipe_id, is_liked
    profile_updated = Signal(str)  # success message
    data_loading_error = Signal(str)  # error_message
    network_error = Signal(str)  # network_error_message
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", access_token: str = None):
        super().__init__()
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = access_token
        self.user_recipes: List[Recipe] = []
        self.favorite_recipes: List[Recipe] = []
        
        # Set authorization header if token provided
        if self.access_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}"
            })
        
        # Request timeout settings
        self.timeout = 10
    
    def load_user_recipes(self, user_id: int) -> None:
        """
        Load recipes created by the user
        
        Args:
            user_id (int): User ID
        """
        print(f"Loading recipes for user: {user_id}")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/users/{user_id}/recipes",
                timeout=self.timeout
            )
            
            print(f"User recipes response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                recipes = []
                
                for recipe_data in data.get("recipes", []):
                    recipe = Recipe(
                        recipe_id=recipe_data["recipe_id"],
                        title=recipe_data["title"],
                        description=recipe_data.get("description", ""),
                        ingredients=recipe_data.get("ingredients", []),
                        instructions=recipe_data.get("instructions", []),
                        image_url=recipe_data.get("image_url"),
                        created_at=recipe_data.get("created_at"),
                        updated_at=recipe_data.get("updated_at"),
                        likes_count=recipe_data.get("likes_count", 0),
                        author_username=recipe_data.get("author_username", ""),
                        is_liked=recipe_data.get("is_liked", False)
                    )
                    recipes.append(recipe)
                
                self.user_recipes = recipes
                self.user_recipes_loaded.emit(recipes)
                print(f"Loaded {len(recipes)} user recipes")
                
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_message = error_data.get("detail", f"Failed to load recipes (status: {response.status_code})")
                self.data_loading_error.emit(error_message)
                
        except requests.exceptions.Timeout:
            self.network_error.emit("Request timed out. Please check your connection.")
        except requests.exceptions.ConnectionError:
            self.network_error.emit("Cannot connect to server. Please check your internet connection.")
        except requests.exceptions.RequestException as e:
            self.network_error.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.data_loading_error.emit(f"An unexpected error occurred: {str(e)}")
    
    def load_favorite_recipes(self, user_id: int) -> None:
        """
        Load recipes favorited by the user
        
        Args:
            user_id (int): User ID
        """
        print(f"Loading favorite recipes for user: {user_id}")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/users/{user_id}/favorites",
                timeout=self.timeout
            )
            
            print(f"Favorite recipes response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                recipes = []
                
                for recipe_data in data.get("recipes", []):
                    recipe = Recipe(
                        recipe_id=recipe_data["recipe_id"],
                        title=recipe_data["title"],
                        description=recipe_data.get("description", ""),
                        ingredients=recipe_data.get("ingredients", []),
                        instructions=recipe_data.get("instructions", []),
                        image_url=recipe_data.get("image_url"),
                        created_at=recipe_data.get("created_at"),
                        updated_at=recipe_data.get("updated_at"),
                        likes_count=recipe_data.get("likes_count", 0),
                        author_username=recipe_data.get("author_username", ""),
                        is_liked=True  # Always true for favorites
                    )
                    recipes.append(recipe)
                
                self.favorite_recipes = recipes
                self.favorite_recipes_loaded.emit(recipes)
                print(f"Loaded {len(recipes)} favorite recipes")
                
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_message = error_data.get("detail", f"Failed to load favorite recipes (status: {response.status_code})")
                self.data_loading_error.emit(error_message)
                
        except requests.exceptions.Timeout:
            self.network_error.emit("Request timed out. Please check your connection.")
        except requests.exceptions.ConnectionError:
            self.network_error.emit("Cannot connect to server. Please check your internet connection.")
        except requests.exceptions.RequestException as e:
            self.network_error.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.data_loading_error.emit(f"An unexpected error occurred: {str(e)}")
    
    def toggle_recipe_like(self, recipe_id: int) -> None:
        """
        Toggle like status for a recipe
        
        Args:
            recipe_id (int): Recipe ID
        """
        print(f"Toggling like for recipe: {recipe_id}")
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/recipes/{recipe_id}/toggle-like",
                timeout=self.timeout
            )
            
            print(f"Toggle like response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                is_liked = data.get("is_liked", False)
                self.recipe_like_toggled.emit(recipe_id, is_liked)
                print(f"Recipe {recipe_id} like status: {is_liked}")
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_message = error_data.get("detail", "Failed to toggle like")
                self.data_loading_error.emit(error_message)
                
        except requests.exceptions.Timeout:
            self.network_error.emit("Request timed out. Please check your connection.")
        except requests.exceptions.ConnectionError:
            self.network_error.emit("Cannot connect to server. Please check your internet connection.")
        except requests.exceptions.RequestException as e:
            self.network_error.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.data_loading_error.emit(f"An unexpected error occurred: {str(e)}")
    
    def update_user_profile(self, user_id: int, username: str = None, email: str = None, 
                           bio: str = None, profile_pic_url: str = None) -> None:
        """
        Update user profile information
        
        Args:
            user_id (int): User ID
            username (str): New username (optional)
            email (str): New email (optional)
            bio (str): New bio (optional)
            profile_pic_url (str): New profile picture URL (optional)
        """
        print(f"Updating profile for user: {user_id}")
        
        # Build update payload with only non-None values
        update_data = {}
        if username is not None:
            update_data["username"] = username
        if email is not None:
            update_data["email"] = email
        if bio is not None:
            update_data["bio"] = bio
        if profile_pic_url is not None:
            update_data["profile_pic_url"] = profile_pic_url
        
        if not update_data:
            self.data_loading_error.emit("No data provided for update")
            return
        
        try:
            response = self.session.put(
                f"{self.base_url}/api/v1/users/{user_id}",
                json=update_data,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            
            print(f"Update profile response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                user_info = data["user"]
                
                # Create updated UserData object
                updated_user = UserData(
                    userid=user_info["userid"],
                    username=user_info["username"],
                    email=user_info["email"],
                    profilepicurl=user_info.get("profilepicurl"),
                    bio=user_info.get("bio"),
                    createdat=user_info.get("createdat")
                )
                
                self.user_data_updated.emit(updated_user)
                self.profile_updated.emit("Profile updated successfully!")
                print("Profile updated successfully")
                
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_message = error_data.get("detail", f"Failed to update profile (status: {response.status_code})")
                self.data_loading_error.emit(error_message)
                
        except requests.exceptions.Timeout:
            self.network_error.emit("Request timed out. Please check your connection.")
        except requests.exceptions.ConnectionError:
            self.network_error.emit("Cannot connect to server. Please check your internet connection.")
        except requests.exceptions.RequestException as e:
            self.network_error.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.data_loading_error.emit(f"An unexpected error occurred: {str(e)}")
    
    def get_user_recipes(self) -> List[Recipe]:
        """Get cached user recipes"""
        return self.user_recipes
    
    def get_favorite_recipes(self) -> List[Recipe]:
        """Get cached favorite recipes"""
        return self.favorite_recipes