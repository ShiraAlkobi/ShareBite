from PySide6.QtCore import QObject, Signal, QTimer
import requests
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class UserData:
    """Data class for user information"""
    userid: int
    username: str
    email: str
    profilepicurl: Optional[str] = None
    bio: Optional[str] = None
    createdat: Optional[str] = None

class LoginModel(QObject):
    """
    Model for login functionality following MVP pattern
    Handles authentication logic and API communication
    """
    
    # Signals for communication with Presenter
    login_success = Signal(UserData, str)  # user_data, access_token
    login_failed = Signal(str)  # error_message
    register_success = Signal(UserData, str)  # user_data, access_token
    register_failed = Signal(str)  # error_message
    validation_error = Signal(str)  # validation_message
    network_error = Signal(str)  # network_error_message
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.base_url = base_url
        self.session = requests.Session()
        self.current_user: Optional[UserData] = None
        self.access_token: Optional[str] = None
        
        # Request timeout settings
        self.timeout = 10
    
    def test_connection(self) -> bool:
        """
        Test connection to the backend server
        
        Returns:
            bool: True if server is reachable, False otherwise
        """
        try:
            print(f"🔗 Testing connection to: {self.base_url}")
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            print(f"🔗 Health check response: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"🔗 Connection test failed: {e}")
            return False
    
    def validate_login_input(self, username: str, password: str) -> bool:
        """
        Validate login input data
        
        Args:
            username (str): Username
            password (str): Password
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not username or not username.strip():
            self.validation_error.emit("Please enter your username")
            return False
        
        if not password or len(password) < 3:
            self.validation_error.emit("Password must be at least 3 characters long")
            return False
        
        return True
    
    def validate_register_input(self, username: str, email: str, password: str, confirm_password: str) -> bool:
        """
        Validate registration input data
        
        Args:
            username (str): Username
            email (str): Email
            password (str): Password
            confirm_password (str): Confirm password
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not username or len(username.strip()) < 3:
            self.validation_error.emit("Username must be at least 3 characters long")
            return False
        
        if not email or '@' not in email:
            self.validation_error.emit("Please enter a valid email address")
            return False
        
        if not password or len(password) < 6:
            self.validation_error.emit("Password must be at least 6 characters long")
            return False
        
        if password != confirm_password:
            self.validation_error.emit("Passwords do not match")
            return False
        
        return True
    
    def login(self, username: str, password: str) -> None:
        """
        Attempt to log in user
        
        Args:
            username (str): Username
            password (str): Password
        """
        if not self.validate_login_input(username, password):
            return
        
        print(f"🔍 Attempting login for user: {username}")
        print(f"🌐 Using endpoint: {self.base_url}/api/v1/auth/login")
        
        try:
            print(f"📤 Sending request to: {self.base_url}/api/v1/auth/login")
            print(f"📤 Request data: {{'username': '{username}', 'password': '***'}}")
            
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={
                    "username": username.strip(),
                    "password": password
                },
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            
            print(f"📡 Response status: {response.status_code}")
            print(f"📡 Response URL: {response.url}")
            print(f"📡 Response text: {response.text[:200]}...")  # First 200 chars
            
            if response.status_code == 200:
                data = response.json()
                user_info = data["user"]
                
                # Create UserData object
                user_data = UserData(
                    userid=user_info["userid"],
                    username=user_info["username"],
                    email=user_info["email"],
                    profilepicurl=user_info.get("profilepicurl"),
                    bio=user_info.get("bio"),
                    createdat=user_info.get("createdat")
                )
                
                self.current_user = user_data
                self.access_token = data["access_token"]
                
                # Update session headers for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                
                self.login_success.emit(user_data, self.access_token)
                
            elif response.status_code == 401:
                print(f"🔒 Authentication failed: Invalid credentials")
                self.login_failed.emit("Invalid username or password")
            elif response.status_code == 404:
                print(f"🔍 Endpoint not found: {response.url}")
                print(f"🔍 Response content: {response.text}")
                self.login_failed.emit("Login endpoint not found. Please check server configuration.")
            elif response.status_code == 422:
                print(f"📝 Validation error: {response.text}")
                try:
                    error_data = response.json()
                    error_msg = str(error_data.get("detail", "Validation error"))
                except:
                    error_msg = "Invalid request format"
                self.login_failed.emit(error_msg)
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                print(f"❌ Response content: {response.text}")
                error_data = {}
                try:
                    if 'application/json' in response.headers.get('content-type', ''):
                        error_data = response.json()
                except:
                    pass
                error_message = error_data.get("detail", f"Login failed with status {response.status_code}")
                self.login_failed.emit(error_message)
                
        except requests.exceptions.Timeout:
            self.network_error.emit("Request timed out. Please check your connection and try again.")
        except requests.exceptions.ConnectionError:
            self.network_error.emit("Cannot connect to server. Please check your internet connection.")
        except requests.exceptions.RequestException as e:
            self.network_error.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.login_failed.emit(f"An unexpected error occurred: {str(e)}")
    
    def register(self, username: str, email: str, password: str, confirm_password: str, bio: str = "") -> None:
        """
        Attempt to register new user
        
        Args:
            username (str): Username
            email (str): Email
            password (str): Password
            confirm_password (str): Confirm password
            bio (str): Optional bio
        """
        if not self.validate_register_input(username, email, password, confirm_password):
            return
        
        print(f"🔍 Attempting registration for user: {username}")
        print(f"📧 Email: {email}")
        print(f"🌐 Using endpoint: {self.base_url}/api/v1/auth/register")
        
        try:
            payload = {
                "username": username.strip(),
                "email": email.strip(),
                "password": password
            }
            
            if bio.strip():
                payload["bio"] = bio.strip()
            
            print(f"📤 Sending registration request...")
            print(f"📤 Payload: {dict(payload, password='***')}")  # Hide password in logs
            
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            
            print(f"📡 Registration response status: {response.status_code}")
            print(f"📡 Registration response text: {response.text[:500]}...")  # First 500 chars
            
            if response.status_code == 200:
                data = response.json()
                user_info = data["user"]
                
                # Create UserData object
                user_data = UserData(
                    userid=user_info["userid"],
                    username=user_info["username"],
                    email=user_info["email"],
                    profilepicurl=user_info.get("profilepicurl"),
                    bio=user_info.get("bio"),
                    createdat=user_info.get("createdat")
                )
                
                self.current_user = user_data
                self.access_token = data["access_token"]
                
                # Update session headers for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                
                self.register_success.emit(user_data, self.access_token)
                
            elif response.status_code == 400:
                error_data = response.json()
                error_message = error_data.get("detail", "Registration failed")
                self.register_failed.emit(error_message)
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_message = error_data.get("detail", f"Registration failed with status {response.status_code}")
                self.register_failed.emit(error_message)
                
        except requests.exceptions.Timeout:
            self.network_error.emit("Request timed out. Please check your connection and try again.")
        except requests.exceptions.ConnectionError:
            self.network_error.emit("Cannot connect to server. Please check your internet connection.")
        except requests.exceptions.RequestException as e:
            self.network_error.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.register_failed.emit(f"An unexpected error occurred: {str(e)}")
    
    def logout(self) -> None:
        """Clear user session"""
        self.current_user = None
        self.access_token = None
        self.session.headers.pop("Authorization", None)
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.current_user is not None and self.access_token is not None
    
    def get_current_user(self) -> Optional[UserData]:
        """Get current user data"""
        return self.current_user