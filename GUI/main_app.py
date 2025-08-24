import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from presenters.login_presenter import LoginPresenter
from presenters.home_presenter import HomePresenter
from models.login_model import UserData

class MainWindow(QMainWindow):
    """
    Main application window implementing Microfrontends architecture
    Manages different views (Login, Home, Recipe Details, etc.)
    """
    
    def __init__(self):
        super().__init__()
        
        # Application state
        self.current_user = None
        self.access_token = None
        
        # Presenters for different views
        self.login_presenter = None
        self.home_presenter = None
        
        self.setup_ui()
        self.setup_authentication()
    
    def setup_ui(self):
        """Setup main window UI"""
        self.setWindowTitle("Recipe Share Platform")
        self.setMinimumSize(1200, 800)
        
        # Main content will be managed by individual presenters
        # No central widget needed since each view is a separate window
        
    def setup_authentication(self):
        """Setup authentication system"""
        # Initialize login presenter (microfrontend)
        self.login_presenter = LoginPresenter(base_url="http://127.0.0.1:8000")
        
        # Connect authentication signals
        self.login_presenter.authentication_successful.connect(self.on_authentication_success)
        self.login_presenter.authentication_failed.connect(self.on_authentication_failed)
        
        # Show login view initially
        self.show_login()
    
    def show_login(self):
        """Show login microfrontend"""
        self.login_presenter.show_view()
        self.hide()  # Hide main window while logging in
    
    def on_authentication_success(self, user_data: UserData, access_token: str):
        """
        Handle successful authentication
        
        Args:
            user_data (UserData): Authenticated user data
            access_token (str): JWT access token
        """
        self.current_user = user_data
        self.access_token = access_token
        
        print(f"🎉 Authentication successful!")
        print(f"   User: {user_data.username}")
        print(f"   Email: {user_data.email}")
        print(f"   Token: {access_token[:20]}...")
        
        # Hide login view
        self.login_presenter.hide_view()
        
        # Initialize and show home view
        self.show_home_view()
    
    def on_authentication_failed(self, error_message: str):
        """
        Handle authentication failure
        
        Args:
            error_message (str): Error message
        """
        print(f"❌ Authentication failed: {error_message}")
        # Login view will handle showing the error
    
    def show_home_view(self):
        """Initialize and show home view"""
        print("🏠 Initializing home view...")
        
        # Create home presenter with user data and token
        self.home_presenter = HomePresenter(
            user_data=self.current_user,
            access_token=self.access_token,
            base_url="http://127.0.0.1:8000"
        )
        
        # Connect home view signals
        self.home_presenter.recipe_details_requested.connect(self.show_recipe_details)
        self.home_presenter.add_recipe_requested.connect(self.show_add_recipe)
        self.home_presenter.user_profile_requested.connect(self.show_user_profile)
        self.home_presenter.logout_requested.connect(self.handle_logout)
        
        # Show home view
        self.home_presenter.show_view()
        
        # Update window title
        self.setWindowTitle(f"Recipe Share - {self.current_user.username}")
    
    def show_recipe_details(self, recipe_id: int):
        """
        Show recipe details window (future implementation)
        
        Args:
            recipe_id (int): Recipe ID to display
        """
        print(f"📖 Opening recipe details for recipe {recipe_id}")
        # TODO: Implement recipe details presenter/view
        # recipe_details_presenter = RecipeDetailsPresenter(recipe_id, self.access_token)
        # recipe_details_presenter.show_view()
    
    def show_add_recipe(self):
        """Show add recipe window (future implementation)"""
        print("➕ Opening add recipe form")
        # TODO: Implement add recipe presenter/view
        # add_recipe_presenter = AddRecipePresenter(self.access_token)
        # add_recipe_presenter.show_view()
    
    def show_user_profile(self):
        """Show user profile window (future implementation)"""
        print(f"👤 Opening profile for user {self.current_user.username}")
        # TODO: Implement user profile presenter/view
        # profile_presenter = ProfilePresenter(self.current_user, self.access_token)
        # profile_presenter.show_view()
    
    def handle_logout(self):
        """Handle user logout"""
        print("👋 User logout requested")
        
        # Clean up current session
        if self.home_presenter:
            self.home_presenter.close_view()
            self.home_presenter.cleanup()
            self.home_presenter = None
        
        self.current_user = None
        self.access_token = None
        
        # Reset window title
        self.setWindowTitle("Recipe Share Platform")
        
        # Show login again
        self.show_login()
    
    def closeEvent(self, event):
        """Handle application close event"""
        print("🚪 Application closing...")
        
        # Clean up all presenters
        if self.login_presenter:
            self.login_presenter.close_view()
        
        if self.home_presenter:
            self.home_presenter.close_view()
            self.home_presenter.cleanup()
        
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Recipe Share")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Recipe Share Inc.")
    
    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Create and show main window
    window = MainWindow()
    
    # Handle application exit
    sys.exit(app.exec())

if __name__ == "__main__":
    main()