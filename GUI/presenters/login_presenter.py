from PySide6.QtCore import QObject, Signal
from models.login_model import LoginModel, UserData
from views.login_view import LoginView
from typing import Optional

class LoginPresenter(QObject):
    """
    Presenter for login functionality following MVP pattern
    Mediates between Model and View, contains business logic
    """
    
    # Signals for parent application
    authentication_successful = Signal(UserData, str)  # user_data, access_token
    authentication_failed = Signal(str)  # error_message
    window_close_requested = Signal()
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", parent=None):
        super().__init__(parent)
        
        # Initialize Model and View
        self.model = LoginModel(base_url)
        self.view = LoginView()
        
        # Setup connections
        self.setup_model_connections()
        self.setup_view_connections()
        
        # State management
        self.is_processing = False
    
    def setup_model_connections(self):
        """Connect model signals to presenter methods"""
        self.model.login_success.connect(self.on_login_success)
        self.model.login_failed.connect(self.on_login_failed)
        self.model.register_success.connect(self.on_register_success)
        self.model.register_failed.connect(self.on_register_failed)
        self.model.validation_error.connect(self.on_validation_error)
        self.model.network_error.connect(self.on_network_error)
    
    def setup_view_connections(self):
        """Connect view signals to presenter methods"""
        self.view.login_requested.connect(self.handle_login_request)
        self.view.register_requested.connect(self.handle_register_request)
    
    def handle_login_request(self, username: str, password: str):
        """
        Handle login request from view
        
        Args:
            username (str): Username
            password (str): Password
        """
        if self.is_processing:
            return
        
        self.is_processing = True
        self.view.set_loading(True)
        self.view.hide_message()
        
        # Delegate to model
        self.model.login(username, password)
    
    def handle_register_request(self, username: str, email: str, password: str, confirm_password: str, bio: str):
        """
        Handle registration request from view
        
        Args:
            username (str): Username
            email (str): Email
            password (str): Password
            confirm_password (str): Confirm password
            bio (str): Bio
        """
        if self.is_processing:
            return
        
        self.is_processing = True
        self.view.set_loading(True)
        self.view.hide_message()
        
        # Delegate to model
        self.model.register(username, email, password, confirm_password, bio)
    
    def on_login_success(self, user_data: UserData, access_token: str):
        """
        Handle successful login
        
        Args:
            user_data (UserData): User information
            access_token (str): JWT access token
        """
        self.is_processing = False
        self.view.set_loading(False)
        
        # Show success message briefly
        self.view.show_message(f"Welcome back, {user_data.username}!", is_error=False)
        
        # Emit authentication successful signal
        self.authentication_successful.emit(user_data, access_token)
        
        print(f"✅ Login successful for user: {user_data.username}")
    
    def on_login_failed(self, error_message: str):
        """
        Handle failed login
        
        Args:
            error_message (str): Error message
        """
        self.is_processing = False
        self.view.set_loading(False)
        self.view.show_message(error_message, is_error=True)
        
        print(f"❌ Login failed: {error_message}")
    
    def on_register_success(self, user_data: UserData, access_token: str):
        """
        Handle successful registration
        
        Args:
            user_data (UserData): User information
            access_token (str): JWT access token
        """
        self.is_processing = False
        self.view.set_loading(False)
        
        # Show success message briefly
        self.view.show_message(f"Welcome to Recipe Share, {user_data.username}!", is_error=False)
        
        # Emit authentication successful signal
        self.authentication_successful.emit(user_data, access_token)
        
        print(f"✅ Registration successful for user: {user_data.username}")
    
    def on_register_failed(self, error_message: str):
        """
        Handle failed registration
        
        Args:
            error_message (str): Error message
        """
        self.is_processing = False
        self.view.set_loading(False)
        self.view.show_message(error_message, is_error=True)
        
        print(f"❌ Registration failed: {error_message}")
    
    def on_validation_error(self, error_message: str):
        """
        Handle validation error
        
        Args:
            error_message (str): Validation error message
        """
        self.is_processing = False
        self.view.set_loading(False)
        self.view.show_message(error_message, is_error=True)
        
        print(f"⚠️ Validation error: {error_message}")
    
    def on_network_error(self, error_message: str):
        """
        Handle network error
        
        Args:
            error_message (str): Network error message
        """
        self.is_processing = False
        self.view.set_loading(False)
        self.view.show_message(f"Connection Error: {error_message}", is_error=True)
        
        print(f"🌐 Network error: {error_message}")
    
    def show_view(self):
        """Show the login view"""
        self.view.show()
        self.view.raise_()
        self.view.activateWindow()
    
    def hide_view(self):
        """Hide the login view"""
        self.view.hide()
    
    def close_view(self):
        """Close the login view"""
        self.view.close()
    
    def get_view(self) -> LoginView:
        """Get the view instance"""
        return self.view
    
    def get_model(self) -> LoginModel:
        """Get the model instance"""
        return self.model
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.model.is_authenticated()
    
    def get_current_user(self) -> Optional[UserData]:
        """Get current user data"""
        return self.model.get_current_user()
    
    def logout(self):
        """Logout current user"""
        self.model.logout()
        self.view.show_login_form()
        self.view.hide_message()
        print("👋 User logged out")