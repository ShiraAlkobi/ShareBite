from PySide6.QtCore import QObject, Signal
import requests
import json
import os
from typing import Optional, Dict, Any, List

class AddRecipeModel(QObject):
    """
    Model for add recipe functionality following MVP pattern
    Handles recipe creation, photo upload, and tag management
    """
    
    # Signals for communication with Presenter
    tags_loaded = Signal(list)  # List[str]
    recipe_created = Signal(int, str)  # recipe_id, success_message
    creation_error = Signal(str)  # error_message
    network_error = Signal(str)  # network_error_message
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", access_token: str = None):
        super().__init__()
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = access_token
        
        # Set authorization header if token provided
        if self.access_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}"
            })
        
        # Request timeout settings
        self.timeout = 15
    
    def load_available_tags(self) -> None:
        """Load available tags from the server"""
        print("Loading available tags from server...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/tags",
                timeout=self.timeout
            )
            
            print(f"Tags response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                tags = []
                
                for tag_data in data.get("tags", []):
                    tag_name = tag_data.get("tag_name") or tag_data.get("name")
                    if tag_name:
                        tags.append(tag_name)
                
                print(f"Loaded {len(tags)} tags")
                self.tags_loaded.emit(tags)
                
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_message = error_data.get("detail", f"Failed to load tags (status: {response.status_code})")
                self.creation_error.emit(error_message)
                
        except requests.exceptions.Timeout:
            self.network_error.emit("Request timed out. Please check your connection.")
        except requests.exceptions.ConnectionError:
            self.network_error.emit("Cannot connect to server. Please check your internet connection.")
        except requests.exceptions.RequestException as e:
            self.network_error.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.creation_error.emit(f"An unexpected error occurred: {str(e)}")
    
    def create_recipe(self, recipe_data: Dict[str, Any]) -> None:
        """
        Create a new recipe
        
        Args:
            recipe_data (Dict): Recipe creation data
        """
        print(f"Creating recipe: {recipe_data.get('title')}")
        
        try:
            # Prepare API payload
            payload = {
                "title": recipe_data['title'],
                "description": recipe_data.get('description', ''),
                "ingredients": recipe_data['ingredients'],
                "instructions": recipe_data['instructions'],
                "servings": recipe_data.get('servings', 4),
                "image_url": recipe_data.get('image_url'),
                "tags": recipe_data.get('tags', [])
            }
            
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            print(f"API payload: {payload}")
            
            response = self.session.post(
                f"{self.base_url}/api/v1/recipes",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            
            print(f"Create recipe response status: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                recipe_id = data.get("recipe_id") or data.get("id")
                message = data.get("message", "Recipe created successfully!")
                
                print(f"Recipe created with ID: {recipe_id}")
                self.recipe_created.emit(recipe_id, message)
                
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_message = error_data.get("detail", f"Failed to create recipe (status: {response.status_code})")
                
                # Handle validation errors
                if response.status_code == 422 and "detail" in error_data:
                    if isinstance(error_data["detail"], list):
                        # FastAPI validation errors
                        error_messages = []
                        for error in error_data["detail"]:
                            field = error.get("loc", ["unknown"])[-1]
                            msg = error.get("msg", "Invalid value")
                            error_messages.append(f"{field}: {msg}")
                        error_message = "; ".join(error_messages)
                
                self.creation_error.emit(error_message)
                
        except requests.exceptions.Timeout:
            self.network_error.emit("Request timed out. Please check your connection.")
        except requests.exceptions.ConnectionError:
            self.network_error.emit("Cannot connect to server. Please check your internet connection.")
        except requests.exceptions.RequestException as e:
            self.network_error.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.creation_error.emit(f"An unexpected error occurred: {str(e)}")
    
    

    
    def search_tags(self, query: str) -> None:
        """
        Search for tags matching the query
        
        Args:
            query (str): Search query
        """
        print(f"Searching tags with query: {query}")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/tags/search",
                params={"q": query},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                tags = []
                
                for tag_data in data.get("tags", []):
                    tag_name = tag_data.get("tag_name") or tag_data.get("name")
                    if tag_name:
                        tags.append(tag_name)
                
                self.tags_loaded.emit(tags)
            else:
                # If search fails, fallback to loading all tags
                self.load_available_tags()
                
        except Exception as e:
            print(f"Tag search error: {e}")
            # Fallback to loading all tags
            self.load_available_tags()
    
    def validate_recipe_data(self, recipe_data: Dict[str, Any]) -> List[str]:
        """
        Validate recipe data before creation
        
        Args:
            recipe_data (Dict): Recipe data to validate
            
        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields
        if not recipe_data.get('title', '').strip():
            errors.append("Recipe title is required")
        
        if not recipe_data.get('ingredients', '').strip():
            errors.append("Ingredients are required")
        
        if not recipe_data.get('instructions', '').strip():
            errors.append("Instructions are required")
        
        # Length validation
        title = recipe_data.get('title', '')
        if len(title) > 100:
            errors.append("Recipe title cannot exceed 100 characters")
        
        # Servings validation
        servings = recipe_data.get('servings')
        if servings is not None and (servings < 1 or servings > 50):
            errors.append("Servings must be between 1 and 50")
        
        # Image URL validation
        image_url = recipe_data.get('image_url')
        if image_url and not image_url.startswith(('http://', 'https://')):
            errors.append("Image URL must start with http:// or https://")
        
        # Tags validation
        tags = recipe_data.get('tags', [])
        if len(tags) > 10:
            errors.append("Recipe cannot have more than 10 tags")
        
        for tag in tags:
            if len(tag) > 50:
                errors.append(f"Tag '{tag}' cannot exceed 50 characters")
        
        return errors
    
    def get_common_tags(self) -> List[str]:
        """
        Get list of common/popular tags
        
        Returns:
            List[str]: Common tag names
        """
        # This could be enhanced to fetch from server or use analytics
        return [
            "vegetarian", "vegan", "gluten-free", "dairy-free", "keto",
            "quick", "easy", "healthy", "comfort-food", "dessert",
            "breakfast", "lunch", "dinner", "snack", "appetizer",
            "main-course", "side-dish", "soup", "salad", "pasta"
        ]