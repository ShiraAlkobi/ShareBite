"""
Fixed API Service for Recipe Sharing Application
Qt-compatible HTTP client for FastAPI backend
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Any, Union
from PySide6.QtCore import QObject, Signal, QThread
from urllib.parse import urljoin, urlencode


class APIService:
    """
    Simplified API service using requests instead of aiohttp
    Compatible with Qt event loop
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.auth_token = None
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        
    def set_auth_token(self, token: str):
        """Set authentication token"""
        self.auth_token = token
        
    def clear_auth_token(self):
        """Clear authentication token"""
        self.auth_token = None
        
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            
        return headers
        
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to API"""
        try:
            url = urljoin(self.base_url, endpoint)
            headers = self._get_headers()
            
            kwargs = {
                "headers": headers,
                "params": params,
                "timeout": 30
            }
            
            if files:
                # Remove content-type header for multipart
                headers.pop("Content-Type", None)
                kwargs["files"] = files
                if data:
                    kwargs["data"] = data
            elif data:
                kwargs["json"] = data
                
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code >= 400:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", error_msg)
                except:
                    pass
                raise Exception(error_msg)
                
            try:
                return response.json()
            except:
                return {"data": response.text}
                
        except requests.exceptions.ConnectionError:
            raise Exception("לא ניתן להתחבר לשרת")
        except requests.exceptions.Timeout:
            raise Exception("הבקשה נכשלה - זמן קצוב")
        except Exception as e:
            self.logger.error(f"API request failed: {e}")
            raise e
    
    # ===== USER ENDPOINTS =====
    
    def register_user(self, user_data: Dict[str, str]) -> Dict[str, Any]:
        """Register new user"""
        return self._make_request("POST", "/users/register", data=user_data)
        
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user"""
        data = {"email": email, "password": password}
        return self._make_request("POST", "/users/login", data=data)
        
    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Get user profile by ID"""
        return self._make_request("GET", f"/users/{user_id}")
        
    def update_user_profile(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        return self._make_request("PUT", f"/users/{user_id}", data=user_data)
        
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        return self._make_request("GET", f"/users/{user_id}/stats")
        
    def get_user_recipes(self, user_id: int, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """Get user's recipes"""
        params = {"page": page, "limit": limit}
        return self._make_request("GET", f"/users/{user_id}/recipes", params=params)
        
    def get_user_favorites(self, user_id: int, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """Get user's favorite recipes"""
        params = {"page": page, "limit": limit}
        return self._make_request("GET", f"/users/{user_id}/favorites", params=params)
    
    # ===== RECIPE ENDPOINTS =====
    
    def get_recent_recipes(self, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """Get recent recipes"""
        params = {"page": page, "limit": limit}
        return self._make_request("GET", "/recipes/recent", params=params)
        
    def get_trending_recipes(self, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """Get trending recipes"""
        params = {"page": page, "limit": limit}
        return self._make_request("GET", "/recipes/trending", params=params)
        
    def get_recipe_by_id(self, recipe_id: int) -> Dict[str, Any]:
        """Get recipe by ID"""
        return self._make_request("GET", f"/recipes/{recipe_id}")
        
    def search_recipes(
        self, 
        query: str = "", 
        tags: List[str] = None,
        author: str = "",
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search recipes"""
        params = {
            "query": query,
            "page": page,
            "limit": limit
        }
        
        if tags:
            params["tags"] = ",".join(tags)
        if author:
            params["author"] = author
            
        return self._make_request("GET", "/recipes/search", params=params)
        
    def create_recipe(self, recipe_data: Dict[str, Any], image_file: Optional[bytes] = None) -> Dict[str, Any]:
        """Create new recipe"""
        files = {}
        if image_file:
            files["image"] = ("image.jpg", image_file, "image/jpeg")
            
        return self._make_request("POST", "/recipes", data=recipe_data, files=files)
        
    def update_recipe(self, recipe_id: int, recipe_data: Dict[str, Any], image_file: Optional[bytes] = None) -> Dict[str, Any]:
        """Update recipe"""
        files = {}
        if image_file:
            files["image"] = ("image.jpg", image_file, "image/jpeg")
            
        return self._make_request("PUT", f"/recipes/{recipe_id}", data=recipe_data, files=files)
        
    def delete_recipe(self, recipe_id: int) -> Dict[str, Any]:
        """Delete recipe"""
        return self._make_request("DELETE", f"/recipes/{recipe_id}")
        
    def toggle_like_recipe(self, recipe_id: int) -> Dict[str, Any]:
        """Toggle like on recipe"""
        return self._make_request("POST", f"/recipes/{recipe_id}/like")
        
    def toggle_favorite_recipe(self, recipe_id: int) -> Dict[str, Any]:
        """Toggle favorite on recipe"""
        return self._make_request("POST", f"/recipes/{recipe_id}/favorite")
        
    def get_recipe_recommendations(self, user_id: int, limit: int = 10) -> Dict[str, Any]:
        """Get recipe recommendations for user"""
        params = {"limit": limit}
        return self._make_request("GET", f"/recipes/recommendations/{user_id}", params=params)
    
    # ===== TAG ENDPOINTS =====
    
    def get_all_tags(self) -> Dict[str, Any]:
        """Get all available tags"""
        return self._make_request("GET", "/tags")
        
    def get_popular_tags(self, limit: int = 20) -> Dict[str, Any]:
        """Get popular tags"""
        params = {"limit": limit}
        return self._make_request("GET", "/tags/popular", params=params)
    
    # ===== AI CHAT ENDPOINTS =====
    
    def chat_with_ai(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Send message to AI chat"""
        data = {
            "message": message,
            "context": context or {}
        }
        return self._make_request("POST", "/chat", data=data)
        
    def get_chat_history(self, user_id: int, limit: int = 50) -> Dict[str, Any]:
        """Get chat history for user"""
        params = {"limit": limit}
        return self._make_request("GET", f"/chat/history/{user_id}", params=params)
    
    def cleanup(self):
        """Cleanup resources"""
        self.session.close()


class APIWorker(QThread):
    """
    Worker thread for API calls
    Runs API calls in background thread to avoid blocking UI
    """
    
    result_ready = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, api_service: APIService, method: str, *args, **kwargs):
        super().__init__()
        self.api_service = api_service
        self.method = method
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        """Execute API call in thread"""
        try:
            # Get the method from API service
            api_method = getattr(self.api_service, self.method)
            
            # Execute method
            result = api_method(*self.args, **self.kwargs)
            
            # Emit result
            self.result_ready.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class APIManager:
    """
    Helper class to manage API calls in Qt application
    Provides simplified interface for making API calls from Qt widgets
    """
    
    def __init__(self, api_service: APIService):
        self.api_service = api_service
        self.active_workers = []
        
    def call_api(
        self, 
        method: str, 
        success_callback=None, 
        error_callback=None,
        *args, 
        **kwargs
    ):
        """Make API call with callbacks"""
        worker = APIWorker(self.api_service, method, *args, **kwargs)
        
        if success_callback:
            worker.result_ready.connect(success_callback)
        if error_callback:
            worker.error_occurred.connect(error_callback)
            
        # Cleanup when finished
        worker.finished.connect(lambda: self.cleanup_worker(worker))
        
        self.active_workers.append(worker)
        worker.start()
        
        return worker
        
    def cleanup_worker(self, worker):
        """Remove worker from active list"""
        if worker in self.active_workers:
            self.active_workers.remove(worker)
            
    def cleanup_all(self):
        """Cleanup all active workers"""
        for worker in self.active_workers[:]:
            worker.quit()
            worker.wait()
        self.active_workers.clear()