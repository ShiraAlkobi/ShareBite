import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from presenters.login_presenter import LoginPresenter
from presenters.home_presenter import HomePresenter
from presenters.profile_presenter import ProfilePresenter
from presenters.recipe_details_presenter import RecipeDetailsPresenter
from models.login_model import UserData


class MainWindow(QMainWindow):
    """
    Main application window implementing Microfrontends architecture
    Manages different views (Login, Home, Profile, Recipe Details, etc.)
    """
    
    def __init__(self):
        super().__init__()
        
        # Application state
        self.current_user = None
        self.access_token = None
        
        # Presenters for different views
        self.login_presenter = None
        self.home_presenter = None
        self.profile_presenter = None
        self.recipe_details_presenter = None
        
        self.setup_ui()
        self.setup_authentication()
    
    def setup_ui(self):
        """Setup main window UI"""
        self.setWindowTitle("ShareBite - Recipe Sharing Platform")
        self.setMinimumSize(1200, 800)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.show()
        
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
        # Show login view initially
        self.show_login()
    
    def show_login(self):
        """Show login microfrontend"""
        login_widget = self.login_presenter.get_view()

        try:
            with open('GUI/themes/login_theme.qss', 'r', encoding='utf-8') as f:
                login_widget.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Login theme file not found")

        if self.stack.indexOf(login_widget) == -1:
            self.stack.addWidget(login_widget)

        self.stack.setCurrentWidget(login_widget)
    
    def on_authentication_success(self, user_data: UserData, access_token: str):
        """
        Handle successful authentication
        
        Args:
            user_data (UserData): Authenticated user data
            access_token (str): JWT access token
        """
        self.current_user = user_data
        self.access_token = access_token
        
        print(f"Authentication successful!")
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
        print(f"Authentication failed: {error_message}")
        # Login view will handle showing the error
    
    def show_home_view(self):
        """Initialize and show home view"""
        print("Initializing home view...")
        
        # Create home presenter with user data and token
        self.home_presenter = HomePresenter(
            user_data=self.current_user,
            access_token=self.access_token,
            base_url="http://127.0.0.1:8000"
        )
        
        # Connect home view signals
        self.home_presenter.recipe_details_requested.connect(self.show_recipe_details)
        self.home_presenter.add_recipe_requested.connect(self.show_add_recipe)
        self.home_presenter.user_profile_requested.connect(self.show_profile_view)
        self.home_presenter.logout_requested.connect(self.handle_logout)
        
        # Show home view
        home_widget = self.home_presenter.get_view()

        try:
            with open('C:\\Users\\User\\Downloads\\ShareBite\\ShareBite\\GUI\\themes\\home_theme.qss', 'r', encoding='utf-8') as f:
                home_widget.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Home theme file not found")

        if self.stack.indexOf(home_widget) == -1:
            self.stack.addWidget(home_widget)

        self.stack.setCurrentWidget(home_widget)
        
        # Update window title
        self.setWindowTitle(f"ShareBite - {self.current_user.username}")

    def show_profile_view(self):
        """Show profile view in the same window"""
        print("👤 Opening profile view...")
        
        if not self.profile_presenter:
            # Create profile presenter with same user data and token
            self.profile_presenter = ProfilePresenter(
                user_data=self.current_user,
                access_token=self.access_token,
                base_url="http://127.0.0.1:8000"
            )
            
            # Connect profile signals
            self.profile_presenter.home_requested.connect(self.show_home_from_profile)
            self.profile_presenter.logout_requested.connect(self.handle_logout)
            self.profile_presenter.recipe_details_requested.connect(self.show_recipe_details)
        
        # Add profile widget to stack and switch to it
        profile_widget = self.profile_presenter.get_view()

        try:
            with open('GUI/themes/profile_theme.qss', 'r', encoding='utf-8') as f:
                profile_widget.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Profile theme file not found")
        
        if self.stack.indexOf(profile_widget) == -1:
            self.stack.addWidget(profile_widget)
        
        self.stack.setCurrentWidget(profile_widget)
        self.setWindowTitle(f"Profile - {self.current_user.username}")
    
    def show_home_from_profile(self):
        """Return to home view from profile"""
        if self.home_presenter:
            home_widget = self.home_presenter.get_view()
            self.stack.setCurrentWidget(home_widget)
            self.setWindowTitle(f"ShareBite - {self.current_user.username}")
    
        self.setWindowTitle(f"Recipe Share - {self.current_user.username}")

    def show_recipe_details(self, recipe_id: int):
        """
        Show recipe details window in the stack
        
        Args:
            recipe_id (int): Recipe ID to display
        """
        print(f"Opening recipe details for recipe {recipe_id}")
        
        # Create recipe details presenter if not exists
        if not self.recipe_details_presenter:
            self.recipe_details_presenter = RecipeDetailsPresenter(
                access_token=self.access_token,
                base_url="http://127.0.0.1:8000"
            )
            
            # Connect recipe details signals
            self.recipe_details_presenter.back_to_home_requested.connect(self.show_home_from_recipe_details)
            self.recipe_details_presenter.recipe_updated.connect(self.on_recipe_updated)
        
        # Load recipe details
        self.recipe_details_presenter.load_recipe_details(recipe_id)
        
        # Add to stack and show
        recipe_details_widget = self.recipe_details_presenter.get_view()
        
        # Apply recipe details theme
        try:
            with open('C:\\Users\\User\\Downloads\\ShareBite\\ShareBite\\GUI\\themes\\recipe_details_theme.qss', 'r', encoding='utf-8') as f:
                recipe_details_widget.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Recipe details theme file not found, trying home theme")
            try:
                with open('C:\\Users\\User\\Downloads\\ShareBite\\ShareBite\\GUI\\themes\\home_theme.qss', 'r', encoding='utf-8') as f:
                    recipe_details_widget.setStyleSheet(f.read())
            except FileNotFoundError:
                print("No theme files found")
        
        if self.stack.indexOf(recipe_details_widget) == -1:
            self.stack.addWidget(recipe_details_widget)
        
        self.stack.setCurrentWidget(recipe_details_widget)
        
        # Update window title
        self.setWindowTitle(f"Recipe Details - {self.current_user.username}")
    
    def show_home_from_recipe_details(self):
        """Return to home view from recipe details"""
        if self.home_presenter:
            home_widget = self.home_presenter.get_view()
            self.stack.setCurrentWidget(home_widget)
            self.setWindowTitle(f"Recipe Share - {self.current_user.username}")
    
    def on_recipe_updated(self, recipe_id: int):
        """
        Handle recipe update notification from recipe details
        This can refresh the home feed if needed
        """
        print(f"Recipe {recipe_id} was updated (liked/favorited)")
        
        # Optionally refresh home view data
        if self.home_presenter:
            # You could call a refresh method on home presenter here
            # self.home_presenter.refresh_recipe_in_feed(recipe_id)
            pass
    
    def show_add_recipe(self):
        """Show add recipe window (future implementation)"""
        print("Opening add recipe form")
        # TODO: Implement add recipe presenter/view
        # add_recipe_presenter = AddRecipePresenter(self.access_token)
        # add_recipe_presenter.show_view()

    def show_profile_view(self):
        """Show profile view in the same window"""
        # print("Opening profile view...")
        
        # if not self.profile_presenter:
        #     # Create profile presenter with same user data and token
        #     self.profile_presenter = ProfilePresenter(
        #         user_data=self.current_user,
        #         access_token=self.access_token,
        #         base_url="http://127.0.0.1:8000"
        #     )
            
        #     # Connect profile signals
        #     self.profile_presenter.home_requested.connect(self.show_home_from_profile)
        #     self.profile_presenter.logout_requested.connect(self.handle_logout)
        #     self.profile_presenter.recipe_details_requested.connect(self.show_recipe_details)
        
        # # Add profile widget to stack and switch to it
        # profile_widget = self.profile_presenter.get_view()

        # try:
        #     with open('GUI/themes/profile_theme.qss', 'r', encoding='utf-8') as f:
        #         profile_widget.setStyleSheet(f.read())
        # except FileNotFoundError:
        #     print("Profile theme file not found")
        
        # if self.stack.indexOf(profile_widget) == -1:
        #     self.stack.addWidget(profile_widget)
        
        # self.stack.setCurrentWidget(profile_widget)
        # self.setWindowTitle(f"Profile - {self.current_user.username}")
        pass
    
    def show_home_from_profile(self):
        """Return to home view from profile"""
        if self.home_presenter:
            home_widget = self.home_presenter.get_view()
            self.stack.setCurrentWidget(home_widget)
            self.setWindowTitle(f"ShareBite - {self.current_user.username}")

    def show_user_profile(self):
        """Show user profile window (future implementation)"""
        print(f"Opening profile for user {self.current_user.username}")
        # TODO: Implement user profile presenter/view
        # profile_presenter = ProfilePresenter(self.current_user, self.access_token)
        # profile_presenter.show_view()
    
    def handle_logout(self):
        """Handle user logout"""
        print("User logout requested")
        
        # Clean up current session
        if self.home_presenter:
            self.home_presenter.close_view()
            self.home_presenter.cleanup()
            self.home_presenter = None
        
        if self.profile_presenter:
            self.profile_presenter.close_view()
            self.profile_presenter.cleanup()
            self.profile_presenter = None
        
        if self.recipe_details_presenter:
            self.recipe_details_presenter.cleanup()
            self.recipe_details_presenter = None
        
        self.current_user = None
        self.access_token = None
        
        # Reset window title
        self.setWindowTitle("ShareBite - Recipe Sharing Platform")
        
        # Show login again
        self.show_login()
    
    def closeEvent(self, event):
        """Handle application close event"""
        print("Application closing...")
        
        # Clean up all presenters
        if self.login_presenter:
            self.login_presenter.close_view()
        
        if self.home_presenter:
            self.home_presenter.close_view()
            self.home_presenter.cleanup()
        
        if self.profile_presenter:
            self.profile_presenter.close_view()
            self.profile_presenter.cleanup()
        
        if self.recipe_details_presenter:
            self.recipe_details_presenter.cleanup()
        
        event.accept()

def load_theme_files(*theme_files):
    combined_styles = ""
    for file_path in theme_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                combined_styles += f.read() + "\n"
        except FileNotFoundError:
            print(f"Theme file not found: {file_path}")
    return combined_styles


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    

    with open("C:\\Users\\User\\Downloads\\ShareBite\\ShareBite\\GUI\\theme.qss", "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())

    # Set application properties
    app.setApplicationName("ShareBite")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ShareBite Inc.")
    
    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Create and show main window
    window = MainWindow()
    
    # Handle application exit
    sys.exit(app.exec())

if __name__ == "__main__":
    main()