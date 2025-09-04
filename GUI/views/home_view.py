from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QScrollArea, QGridLayout, QComboBox,
    QSpacerItem, QSizePolicy, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject
from PySide6.QtGui import QFont, QColor, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from typing import List, Dict, Any
from models.home_model import RecipeData
from models.login_model import UserData
import requests
from io import BytesIO
from views.components.recipe_card import HomeRecipeCard



class SearchBar(QFrame):
    """Modern compact search bar widget with filters"""
    
    search_requested = Signal(str, dict)  # query, filters
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SearchBar")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup search bar UI components"""
        self.setFixedHeight(60)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 5)
        layout.setSpacing(15)
        
        # Search icon and input container
        search_container = QFrame()
        search_container.setObjectName("SearchContainer")
        
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(15, 0, 15, 0)
        search_layout.setSpacing(5)
        
        # Search icon
        search_icon = QLabel("🔍")
        search_icon.setObjectName("SearchIcon")
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Search for recipes...")
        self.search_input.returnPressed.connect(self.perform_search)
        self.search_input.setMinimumWidth(300)
        self.search_input.setMinimumHeight(25)
        
        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_input)
        
        # Filter dropdown
        self.filter_combo = QComboBox()
        self.filter_combo.setObjectName("FilterCombo")
        self.filter_combo.addItems(["All", "Breakfast", "Lunch", "Dinner", "Dessert", "Snacks"])
        self.filter_combo.setMinimumWidth(100)
        
        # Search button
        search_button = QPushButton("Search")
        search_button.setObjectName("SearchButton")
        search_button.clicked.connect(self.perform_search)
        search_button.setMinimumWidth(80)
        
        layout.addWidget(search_container, 1)
        layout.addWidget(self.filter_combo)
        layout.addWidget(search_button)
    
    def perform_search(self):
        """Perform search with current query and filters"""
        query = self.search_input.text().strip()
        selected_filter = self.filter_combo.currentText()
        
        filters = {}
        if selected_filter != "All":
            filters["category"] = selected_filter.lower()
        
        self.search_requested.emit(query, filters)

class HomeView(QWidget):
    """
    Main home view with modern design matching login view
    Scaled for screen compatibility with scroll support
    """
    
    # Signals for communication with Presenter
    search_requested = Signal(str, dict)
    refresh_requested = Signal()
    add_recipe_requested = Signal()
    user_profile_requested = Signal()
    analytics_requested = Signal()
    logout_requested = Signal()
    
    recipe_clicked = Signal(int)
    recipe_liked = Signal(int)
    recipe_favorited = Signal(int)
    
    filter_changed = Signal(dict)
    load_more_requested = Signal()
    
    def __init__(self, user_data: UserData, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.recipe_cards = {}  # recipe_id -> RecipeCard mapping
        self.setObjectName("HomeView")
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the main home UI with modern design and scroll support"""
        self.setWindowTitle(f"ShareBite - Welcome {self.user_data.username}")
        # Set reasonable window size
        self.setMinimumSize(700, 500)
        self.setMaximumSize(1000, 700)
        self.resize(900, 650)
        
        # Create scroll area for entire content
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Create scrollable content widget
        content_widget = QWidget()
        content_widget.setObjectName("HomeContentWidget")
        # Main layout for the window
        window_layout = QVBoxLayout(self)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.addWidget(scroll_area)
        
        # Content layout
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header section
        self.setup_header_section(main_layout)
        
        # Content wrapper
        content_wrapper = QFrame()
        content_wrapper.setObjectName("ContentWrapper")
        
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(16)
        
        # Search section
        self.search_bar = SearchBar()
        content_layout.addWidget(self.search_bar)
        
        # Recipes section
        self.setup_recipes_section(content_layout)
        
        main_layout.addWidget(content_wrapper)
        
        # Set the content widget to scroll area
        scroll_area.setWidget(content_widget)
    
    def setup_header_section(self, main_layout):
        """Setup modern compact header with branding and navigation"""
        header = QFrame()
        header.setObjectName("HeaderSection")
        header.setFixedHeight(60)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 8, 20, 8)
        header_layout.setSpacing(16)
        
        # Logo and brand container
        brand_container = QHBoxLayout()
        brand_container.setSpacing(10)
        
        # Logo/Icon
        logo_label = QLabel("🍽️")
        logo_label.setObjectName("AppLogo")
        
        # App name
        brand_label = QLabel("ShareBite")
        brand_label.setObjectName("AppBrand")
        
        # Welcome message
        welcome_label = QLabel(f"Welcome, {self.user_data.username}!")
        welcome_label.setObjectName("WelcomeMessage")
        
        brand_container.addWidget(logo_label)
        brand_container.addWidget(brand_label)
        brand_container.addWidget(welcome_label)
        
        # Navigation actions
        nav_container = QHBoxLayout()
        nav_container.setSpacing(8)
        
        # Add recipe button
        add_button = QPushButton("+ Add")
        add_button.setObjectName("AddRecipeButton")
        add_button.clicked.connect(self.add_recipe_requested.emit)
        
        # Analytics button
        analytics_button = QPushButton("Analytics")
        analytics_button.setObjectName("AnalyticsButton")
        analytics_button.clicked.connect(self.analytics_requested.emit)
        
        # Profile button
        profile_button = QPushButton("Profile")
        profile_button.setObjectName("ProfileButton")
        profile_button.clicked.connect(self.user_profile_requested.emit)
        
        # Logout button
        logout_button = QPushButton("Logout")
        logout_button.setObjectName("LogoutButton")
        logout_button.clicked.connect(self.logout_requested.emit)
        
        nav_container.addWidget(add_button)
        nav_container.addWidget(analytics_button)
        nav_container.addWidget(profile_button)
        nav_container.addWidget(logout_button)
        
        header_layout.addLayout(brand_container)
        header_layout.addStretch()
        header_layout.addLayout(nav_container)
        
        main_layout.addWidget(header)

    def setup_recipes_section(self, content_layout):
        """Setup compact scrollable recipes section"""
        # Section header
        recipes_header = QFrame()
        recipes_header.setObjectName("RecipesHeader")
        
        header_layout = QHBoxLayout(recipes_header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)
        
        self.content_title = QLabel("Latest Recipes")
        self.content_title.setObjectName("SectionTitle")
        
        refresh_button = QPushButton("🔄 Refresh")
        refresh_button.setObjectName("RefreshButton")
        refresh_button.clicked.connect(self.refresh_requested.emit)
        
        header_layout.addWidget(self.content_title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_button)
        
        content_layout.addWidget(recipes_header)
        
        # Recipe grid container
        self.recipe_container = QWidget()
        self.recipe_container.setObjectName("RecipeContainer")
        
        self.recipe_layout = QGridLayout(self.recipe_container)
        self.recipe_layout.setSpacing(16)
        self.recipe_layout.setContentsMargins(0, 8, 0, 8)
        
        content_layout.addWidget(self.recipe_container)
    
    def setup_loading_overlay(self):
        """Setup compact loading indicator"""
        self.loading_indicator = QFrame(self)
        self.loading_indicator.setObjectName("LoadingIndicator")
        self.loading_indicator.setFixedSize(60, 60)
        
        indicator_layout = QVBoxLayout(self.loading_indicator)
        indicator_layout.setAlignment(Qt.AlignCenter)
        indicator_layout.setContentsMargins(0, 0, 0, 0)
        
        loading_icon = QLabel("🍳")
        loading_icon.setObjectName("LoadingIcon")
        loading_icon.setAlignment(Qt.AlignCenter)
        
        indicator_layout.addWidget(loading_icon)
        
        self.loading_indicator.hide()
        
        # Create animation timer for spinning effect
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self.animate_loading)
        self.loading_icons = ["🍳", "👨‍🍳", "🥘", "🍽️"]
        self.loading_index = 0
    
    def setup_connections(self):
        """Setup signal connections"""
        self.search_bar.search_requested.connect(self.search_requested.emit)
    
    def set_loading_state(self, loading: bool, message: str = "Loading..."):
        """Set loading state with overlay - prevents black window"""
        print(f"DEBUG: Setting loading state: {loading} - {message}")
        
        if loading:
            # Disable all interactions but keep window responsive
            self.setEnabled(False)
            print("DEBUG: Window disabled, creating overlay")
            
            # Show loading overlay
            if not hasattr(self, 'loading_overlay'):
                self.create_loading_overlay()
                print("DEBUG: Created new loading overlay")
            
            self.loading_label.setText(message)
            self.loading_overlay.show()
            self.loading_overlay.raise_()
            print("DEBUG: Overlay shown and raised")
        else:
            # Re-enable interactions
            self.setEnabled(True)
            print("DEBUG: Window re-enabled")
            if hasattr(self, 'loading_overlay'):
                self.loading_overlay.hide()
                print("DEBUG: Overlay hidden")

    def create_loading_overlay(self):
        """Create semi-transparent loading overlay"""
        self.loading_overlay = QFrame(self)
        self.loading_overlay.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.6);
                border-radius: 15px;
            }
        """)
        
        layout = QVBoxLayout(self.loading_overlay)
        layout.setAlignment(Qt.AlignCenter)
        
        # Spinner
        spinner = QLabel("🔄")
        spinner.setAlignment(Qt.AlignCenter)
        spinner.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                background: transparent;
                padding: 20px;
            }
        """)
        
        # Loading text
        self.loading_label = QLabel("Loading...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: 600;
                background: transparent;
                padding: 10px;
            }
        """)
        
        layout.addWidget(spinner)
        layout.addWidget(self.loading_label)
        
        # Create timer for spinner animation
        self.spinner_timer = QTimer()
        self.spinner_timer.timeout.connect(lambda: self.animate_spinner(spinner))
        self.spinner_angles = 0
    
    def animate_spinner(self, spinner_label):
        """Simple spinner animation"""
        spinners = ["🔄", "🔃", "🔄", "🔃"]
        self.spinner_angles = (self.spinner_angles + 1) % len(spinners)
        spinner_label.setText(spinners[self.spinner_angles])
    
    def display_recipes(self, recipes: List[RecipeData]):
        """Display recipe cards in compact grid layout"""
        self.clear_recipe_grid()
        
        if not recipes:
            self.show_empty_state("No recipes found")
            return
        
        # Calculate optimal columns based on available width (aim for 3 columns)
        columns = 3
        
        for i, recipe in enumerate(recipes):
            row = i // columns
            col = i % columns
            
            # Use the shared HomeRecipeCard component
            card = HomeRecipeCard(recipe)
            card.recipe_clicked.connect(self.recipe_clicked.emit)
            card.recipe_liked.connect(self.recipe_liked.emit)
            card.recipe_favorited.connect(self.recipe_favorited.emit)
            
            self.recipe_cards[recipe.recipe_id] = card
            self.recipe_layout.addWidget(card, row, col)
        
        # Update content title
        self.content_title.setText(f"Latest Recipes ({len(recipes)})")
        
    def display_search_results(self, recipes: List[RecipeData], query: str):
        """Display search results with query context"""
        self.display_recipes(recipes)
        self.content_title.setText(f"'{query}' ({len(recipes)})")
    
    def animate_loading(self):
        """Animate the loading indicator"""
        if hasattr(self, 'loading_indicator') and self.loading_indicator.isVisible():
            loading_icon = self.loading_indicator.findChild(QLabel, "LoadingIcon")
            if loading_icon:
                self.loading_index = (self.loading_index + 1) % len(self.loading_icons)
                loading_icon.setText(self.loading_icons[self.loading_index])

    
    def update_recipe_like_status(self, recipe_id: int, is_liked: bool, likes_count: int = None):
        """Update like status for specific recipe card with optional likes count"""
        if recipe_id in self.recipe_cards:
            card = self.recipe_cards[recipe_id]
            
            # If likes_count not provided, calculate it
            if likes_count is None:
                current_count = card.recipe.likes_count
                if is_liked and not card.recipe.is_liked:
                    likes_count = current_count + 1
                elif not is_liked and card.recipe.is_liked:
                    likes_count = max(0, current_count - 1)
                else:
                    likes_count = current_count
            
            card.update_like_status(is_liked, likes_count)
    
    def update_recipe_favorite_status(self, recipe_id: int, is_favorited: bool):
        """Update favorite status for specific recipe card"""
        if recipe_id in self.recipe_cards:
            card = self.recipe_cards[recipe_id]
            card.update_favorite_status(is_favorited)
    
    def clear_recipe_grid(self):
        """Clear all recipe cards from grid with proper cleanup"""
        # Create a list of cards to avoid dictionary modification during iteration
        cards_to_remove = list(self.recipe_cards.values())
        
        for card in cards_to_remove:
            try:
                # Only cleanup if the card still exists - check if widget is valid
                if card and hasattr(card, 'cleanup'):
                    card.cleanup()
                
                # Remove from layout safely - check if still in layout
                try:
                    if self.recipe_layout.indexOf(card) != -1:
                        self.recipe_layout.removeWidget(card)
                except RuntimeError:
                    # Widget already removed from layout
                    pass
                
                # Hide the card first to prevent rendering issues
                try:
                    card.hide()
                except RuntimeError:
                    # Widget already deleted
                    pass
                
                # Schedule for deletion
                try:
                    card.deleteLater()
                except RuntimeError:
                    # Widget already scheduled for deletion
                    pass
                    
            except RuntimeError:
                # Widget already deleted, just continue
                print(f"Widget already deleted during cleanup")
                continue
            except Exception as e:
                print(f"Error cleaning up recipe card: {e}")
                continue
        
        # Clear the dictionary
        self.recipe_cards.clear()
        
        # Force layout update
        try:
            self.recipe_layout.update()
        except RuntimeError:
            pass
    
    def show_empty_state(self, message: str):
        """Show compact empty state message"""
        empty_container = QFrame()
        empty_container.setObjectName("EmptyState")
        
        empty_layout = QVBoxLayout(empty_container)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(12)
        empty_layout.setContentsMargins(20, 20, 20, 20)
        
        empty_icon = QLabel("🍽️")
        empty_icon.setObjectName("EmptyStateIcon")
        empty_icon.setAlignment(Qt.AlignCenter)
        
        empty_message = QLabel(message)
        empty_message.setObjectName("EmptyStateMessage")
        empty_message.setAlignment(Qt.AlignCenter)
        
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_message)
        
        self.recipe_layout.addWidget(empty_container, 0, 0, 1, 3)  # Span across 3 columns
    
    def show_error_message(self, message: str):
        """Show error message to user"""
        self.show_temporary_message(message, 5000, True)
    
    def show_success_message(self, message: str):
        """Show success message to user"""
        self.show_temporary_message(message, 3000, False)
    
    def show_temporary_message(self, message: str, duration: int = 3000, is_error: bool = False):
        """Show a temporary message to the user (toast-style notification)"""
        try:
            # Create temporary message label if it doesn't exist
            if not hasattr(self, 'temp_message_label'):
                self.temp_message_label = QLabel(self)
                self.temp_message_label.setAlignment(Qt.AlignCenter)
                self.temp_message_label.hide()
                self.temp_message_label.setWordWrap(True)
                self.temp_message_label.setObjectName("TempMessageLabel")
            
            # Set message and property for CSS styling
            self.temp_message_label.setText(message)
            self.temp_message_label.setProperty("error", str(is_error).lower())
            
            # Force style refresh
            self.temp_message_label.style().unpolish(self.temp_message_label)
            self.temp_message_label.style().polish(self.temp_message_label)
            
            # Position the message (center-bottom of the view)
            self.temp_message_label.adjustSize()
            parent_rect = self.rect()
            label_rect = self.temp_message_label.rect()
            x = (parent_rect.width() - label_rect.width()) // 2
            y = parent_rect.height() - label_rect.height() - 40  # 40px from bottom
            self.temp_message_label.move(x, y)
            
            # Show the message
            self.temp_message_label.show()
            self.temp_message_label.raise_()
            
            # Set timer to hide message
            if not hasattr(self, 'temp_message_timer'):
                self.temp_message_timer = QTimer()
                self.temp_message_timer.timeout.connect(self._hide_temporary_message)
            
            self.temp_message_timer.stop()
            self.temp_message_timer.start(duration)
            
        except Exception as e:
            print(f"Error showing temporary message: {e}")

    def _hide_temporary_message(self):
        """Hide the temporary message"""
        if hasattr(self, 'temp_message_label'):
            self.temp_message_label.hide()
        if hasattr(self, 'temp_message_timer'):
            self.temp_message_timer.stop()
    
    def resizeEvent(self, event):
        """Handle window resize to position loading overlay"""
        super().resizeEvent(event)
        
        # Position loading overlay to cover the entire window
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.resize(self.size())
            self.loading_overlay.move(0, 0)
        
        # Start spinner animation when overlay is visible
        if hasattr(self, 'loading_overlay') and self.loading_overlay.isVisible():
            if hasattr(self, 'spinner_timer') and not self.spinner_timer.isActive():
                self.spinner_timer.start(200)  # Animate every 200ms
        elif hasattr(self, 'spinner_timer'):
            self.spinner_timer.stop()