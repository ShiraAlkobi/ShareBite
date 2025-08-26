from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QScrollArea, QGridLayout, QComboBox,
    QGraphicsDropShadowEffect, QSpacerItem, QSizePolicy, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPixmap, QPainter
from typing import List, Dict, Any
from models.home_model import RecipeData, UserStatsData
from models.login_model import UserData

class RecipeCard(QFrame):
    """Individual recipe card widget displaying dish name, image, date, and author"""
    
    recipe_clicked = Signal(int)  # recipe_id
    recipe_liked = Signal(int)  # recipe_id
    recipe_favorited = Signal(int)  # recipe_id
    
    def __init__(self, recipe: RecipeData, parent=None):
        super().__init__(parent)
        self.recipe = recipe
        self.setObjectName("RecipeCard")
        self.setup_ui()

    def setup_ui(self):
        """Setup recipe card UI components"""
        self.setFixedSize(300, 300)
        self.setProperty("class", "recipe-card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Recipe image container
        image_container = QFrame()
        image_container.setObjectName("RecipeImageContainer")
        image_container.setFixedHeight(180)
        
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)

        if self.recipe.image_url:
            image_label = QLabel("🍽️")
            image_label.setObjectName("RecipeImagePlaceholder")
        else:
            image_label = QLabel("📸")
            image_label.setObjectName("RecipeImagePlaceholder")
        
        image_label.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(image_label)

        # Content container
        content_container = QFrame()
        content_container.setObjectName("RecipeContent")
        
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(12)

        # Recipe title
        self.title_label = QLabel(self.recipe.title)
        self.title_label.setObjectName("RecipeTitle")
        self.title_label.setWordWrap(True)

        # Recipe metadata container
        meta_container = QFrame()
        meta_container.setObjectName("RecipeMetadata")
        meta_layout = QVBoxLayout(meta_container)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        meta_layout.setSpacing(4)

        # Author
        author_label = QLabel(f"by Chef {self.recipe.author_name}")
        author_label.setObjectName("RecipeAuthor")

        # Date
        date_label = QLabel(f"Created: {self.recipe.created_at or 'Date unknown'}")
        date_label.setObjectName("RecipeDate")

        meta_layout.addWidget(author_label)
        meta_layout.addWidget(date_label)

        # Actions container
        actions_container = QFrame()
        actions_container.setObjectName("RecipeActions")
        
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        # Like button
        self.like_button = QPushButton(f"♥ {self.recipe.likes_count}")
        self.like_button.setObjectName("LikeButton")
        self.like_button.setProperty("liked", str(self.recipe.is_liked).lower())
        self.like_button.clicked.connect(lambda: self.recipe_liked.emit(self.recipe.recipe_id))

        # Favorite button
        self.favorite_button = QPushButton("★" if self.recipe.is_favorited else "☆")
        self.favorite_button.setObjectName("FavoriteButton")
        self.favorite_button.setProperty("favorited", str(self.recipe.is_favorited).lower())
        self.favorite_button.clicked.connect(lambda: self.recipe_favorited.emit(self.recipe.recipe_id))

        # View button
        view_button = QPushButton("View Recipe")
        view_button.setObjectName("ViewRecipeButton")
        view_button.clicked.connect(lambda: self.recipe_clicked.emit(self.recipe.recipe_id))

        actions_layout.addWidget(self.like_button)
        actions_layout.addWidget(self.favorite_button)
        actions_layout.addStretch()
        actions_layout.addWidget(view_button)

        # Add all containers to main layout
        content_layout.addWidget(self.title_label)
        content_layout.addWidget(meta_container)
        content_layout.addStretch()
        content_layout.addWidget(actions_container)

        layout.addWidget(image_container)
        layout.addWidget(content_container)
    
    def update_like_status(self, is_liked: bool, likes_count: int):
        """Update like button status"""
        self.recipe.is_liked = is_liked
        self.recipe.likes_count = likes_count
        
        self.like_button.setText(f"♥ {likes_count}")
        self.like_button.setProperty("liked", str(is_liked).lower())
        self.like_button.style().unpolish(self.like_button)
        self.like_button.style().polish(self.like_button)
    
    def update_favorite_status(self, is_favorited: bool):
        """Update favorite button status"""
        self.recipe.is_favorited = is_favorited
        
        star_symbol = "★" if is_favorited else "☆"
        self.favorite_button.setText(star_symbol)
        self.favorite_button.setProperty("favorited", str(is_favorited).lower())
        self.favorite_button.style().unpolish(self.favorite_button)
        self.favorite_button.style().polish(self.favorite_button)

class SearchBar(QFrame):
    """Modern search bar widget with filters"""
    
    search_requested = Signal(str, dict)  # query, filters
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SearchBar")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup search bar UI components"""
        self.setFixedHeight(70)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)
        
        # Search icon and input container
        search_container = QFrame()
        search_container.setObjectName("SearchContainer")
        
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(16, 0, 16, 0)
        search_layout.setSpacing(12)
        
        # Search icon
        search_icon = QLabel("🔍")
        search_icon.setObjectName("SearchIcon")
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Search for delicious recipes...")
        self.search_input.returnPressed.connect(self.perform_search)
        
        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_input)
        
        # Filter dropdown
        self.filter_combo = QComboBox()
        self.filter_combo.setObjectName("FilterCombo")
        self.filter_combo.addItems(["All Recipes", "Breakfast", "Lunch", "Dinner", "Dessert", "Snacks"])
        
        # Search button
        search_button = QPushButton("Find Recipes")
        search_button.setObjectName("SearchButton")
        search_button.clicked.connect(self.perform_search)
        
        layout.addWidget(search_container)
        layout.addWidget(self.filter_combo)
        layout.addWidget(search_button)
    
    def perform_search(self):
        """Perform search with current query and filters"""
        query = self.search_input.text().strip()
        selected_filter = self.filter_combo.currentText()
        
        filters = {}
        if selected_filter != "All Recipes":
            filters["category"] = selected_filter.lower()
        
        self.search_requested.emit(query, filters)

class UserStatsWidget(QFrame):
    """Modern user statistics display widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("UserStatsWidget")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup user stats UI components"""
        self.setFixedHeight(120)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 20, 32, 20)
        layout.setSpacing(40)
        
        # Stats containers
        self.recipes_stat = self.create_stat_widget("Recipes Created", "0", "📝")
        self.likes_stat = self.create_stat_widget("Likes Received", "0", "♥")
        self.favorites_stat = self.create_stat_widget("Total Favorites", "0", "⭐")
        
        layout.addWidget(self.recipes_stat)
        layout.addWidget(self.likes_stat)
        layout.addWidget(self.favorites_stat)
        layout.addStretch()
    
    def create_stat_widget(self, label: str, value: str, icon: str) -> QWidget:
        """Create individual stat widget with modern design"""
        container = QFrame()
        container.setObjectName("StatContainer")
        
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(24, 16, 24, 16)
        
        # Icon and value container
        top_container = QHBoxLayout()
        top_container.setSpacing(12)
        top_container.setAlignment(Qt.AlignCenter)
        
        icon_label = QLabel(icon)
        icon_label.setObjectName("StatIcon")
        
        value_label = QLabel(value)
        value_label.setObjectName("StatValue")
        
        top_container.addWidget(icon_label)
        top_container.addWidget(value_label)
        
        # Label
        label_widget = QLabel(label)
        label_widget.setObjectName("StatLabel")
        label_widget.setAlignment(Qt.AlignCenter)
        
        layout.addLayout(top_container)
        layout.addWidget(label_widget)
        
        # Store reference to value label for updates
        container.value_label = value_label
        
        return container
    
    def update_stats(self, stats: UserStatsData):
        """Update displayed statistics"""
        self.recipes_stat.value_label.setText(str(stats.recipes_created))
        self.likes_stat.value_label.setText(str(stats.total_likes_received))
        self.favorites_stat.value_label.setText(str(stats.total_favorites_received))

class HomeView(QWidget):
    """
    Main home view implementing the View part of MVP pattern
    Modern ShareBite recipe feed with search and user stats
    """
    
    # Signals for communication with Presenter
    search_requested = Signal(str, dict)
    refresh_requested = Signal()
    add_recipe_requested = Signal()
    user_profile_requested = Signal()
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
        """Setup the main home UI with modern design"""
        self.setWindowTitle(f"ShareBite - Welcome {self.user_data.username}")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)  # Open larger by default
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header section
        self.setup_header_section(main_layout)
        
        # Content wrapper
        content_wrapper = QFrame()
        content_wrapper.setObjectName("ContentWrapper")
        
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(32, 24, 32, 24)
        content_layout.setSpacing(24)
        
        # Search section
        self.search_bar = SearchBar()
        content_layout.addWidget(self.search_bar)
        
        # Recipes section (removed stats widget)
        self.setup_recipes_section(content_layout)
        
        main_layout.addWidget(content_wrapper)
        
        # Loading overlay
        self.setup_loading_overlay()
    
    def setup_header_section(self, main_layout):
        """Setup modern header with branding and navigation"""
        header = QFrame()
        header.setObjectName("HeaderSection")
        header.setFixedHeight(80)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(32, 16, 32, 16)
        header_layout.setSpacing(24)
        
        # Logo and brand container
        brand_container = QHBoxLayout()
        brand_container.setSpacing(12)
        
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
        nav_container.setSpacing(12)
        
        # Add recipe button
        add_button = QPushButton("+ Add Recipe")
        add_button.setObjectName("AddRecipeButton")
        add_button.clicked.connect(self.add_recipe_requested.emit)
        
        # Profile button
        profile_button = QPushButton("Profile")
        profile_button.setObjectName("ProfileButton")
        profile_button.clicked.connect(self.user_profile_requested.emit)
        
        # Logout button
        logout_button = QPushButton("Logout")
        logout_button.setObjectName("LogoutButton")
        logout_button.clicked.connect(self.logout_requested.emit)
        
        nav_container.addWidget(add_button)
        nav_container.addWidget(profile_button)
        nav_container.addWidget(logout_button)
        
        header_layout.addLayout(brand_container)
        header_layout.addStretch()
        header_layout.addLayout(nav_container)
        
        main_layout.addWidget(header)
    
    def setup_recipes_section(self, content_layout):
        """Setup modern scrollable recipes section"""
        # Section header
        recipes_header = QFrame()
        recipes_header.setObjectName("RecipesHeader")
        
        header_layout = QHBoxLayout(recipes_header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(16)
        
        self.content_title = QLabel("Latest Recipes")
        self.content_title.setObjectName("SectionTitle")
        
        refresh_button = QPushButton("🔄 Refresh")
        refresh_button.setObjectName("RefreshButton")
        refresh_button.clicked.connect(self.refresh_requested.emit)
        
        header_layout.addWidget(self.content_title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_button)
        
        content_layout.addWidget(recipes_header)
        
        # Scrollable recipes area
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("RecipesScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Recipe grid container
        self.recipe_container = QWidget()
        self.recipe_container.setObjectName("RecipeContainer")
        
        self.recipe_layout = QGridLayout(self.recipe_container)
        self.recipe_layout.setSpacing(24)
        self.recipe_layout.setContentsMargins(0, 16, 0, 16)
        
        self.scroll_area.setWidget(self.recipe_container)
        content_layout.addWidget(self.scroll_area)
    
    def setup_loading_overlay(self):
        """Setup modern minimal loading indicator"""
        self.loading_indicator = QFrame()
        self.loading_indicator.setObjectName("LoadingIndicator")
        self.loading_indicator.setFixedSize(80, 80)
        
        indicator_layout = QVBoxLayout(self.loading_indicator)
        indicator_layout.setAlignment(Qt.AlignCenter)
        indicator_layout.setContentsMargins(0, 0, 0, 0)
        
        # Spinning emoji or loading animation
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
    
    def display_recipes(self, recipes: List[RecipeData]):
        """Display recipe cards in modern grid layout"""
        self.clear_recipe_grid()
        
        if not recipes:
            self.show_empty_state("No recipes found")
            return
        
        # Calculate optimal columns (force 3 columns for better layout)
        columns = 3
        
        for i, recipe in enumerate(recipes):
            row = i // columns
            col = i % columns
            
            card = RecipeCard(recipe)
            card.recipe_clicked.connect(self.recipe_clicked.emit)
            card.recipe_liked.connect(self.recipe_liked.emit)
            card.recipe_favorited.connect(self.recipe_favorited.emit)
            
            self.recipe_cards[recipe.recipe_id] = card
            self.recipe_layout.addWidget(card, row, col)
        
        # Update content title
        self.content_title.setText(f"Latest Recipes ({len(recipes)} found)")
    
    def display_search_results(self, recipes: List[RecipeData], query: str):
        """Display search results with query context"""
        self.display_recipes(recipes)
        self.content_title.setText(f"Search Results for '{query}' ({len(recipes)} found)")
    
    def animate_loading(self):
        """Animate the loading indicator"""
        if hasattr(self, 'loading_indicator') and self.loading_indicator.isVisible():
            loading_icon = self.loading_indicator.findChild(QLabel, "LoadingIcon")
            if loading_icon:
                self.loading_index = (self.loading_index + 1) % len(self.loading_icons)
                loading_icon.setText(self.loading_icons[self.loading_index])
    
    def display_user_stats(self, stats: UserStatsData):
        """Display user statistics (removed - no longer needed)"""
        pass  # Stats widget removed, keeping method for compatibility
    
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
        else:
            print(f"Recipe card {recipe_id} not found for like update")
    
    def update_recipe_favorite_status(self, recipe_id: int, is_favorited: bool):
        """Update favorite status for specific recipe card"""
        if recipe_id in self.recipe_cards:
            card = self.recipe_cards[recipe_id]
            card.update_favorite_status(is_favorited)
    
    def clear_recipe_grid(self):
        """Clear all recipe cards from grid"""
        for card in self.recipe_cards.values():
            self.recipe_layout.removeWidget(card)
            card.deleteLater()
        self.recipe_cards.clear()
    
    def show_empty_state(self, message: str):
        """Show modern empty state message"""
        empty_container = QFrame()
        empty_container.setObjectName("EmptyState")
        
        empty_layout = QVBoxLayout(empty_container)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(16)
        
        empty_icon = QLabel("🍽️")
        empty_icon.setObjectName("EmptyStateIcon")
        empty_icon.setAlignment(Qt.AlignCenter)
        
        empty_message = QLabel(message)
        empty_message.setObjectName("EmptyStateMessage")
        empty_message.setAlignment(Qt.AlignCenter)
        
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_message)
        
        self.recipe_layout.addWidget(empty_container, 0, 0, 1, 3)  # Span across 3 columns
    
    def set_loading_state(self, loading: bool):
        """Set modern minimal loading state"""
        if loading:
            self.loading_indicator.show()
            self.loading_indicator.raise_()
            self.loading_timer.start(500)  # Change icon every 500ms
        else:
            self.loading_indicator.hide()
            self.loading_timer.stop()
    
    def show_error_message(self, message: str):
        """Show modern error message"""
        error_container = self.create_notification("❌ Error", message, "ErrorNotification")
        self.show_notification(error_container, 5000)
    
    def show_success_message(self, message: str):
        """Show modern success message"""
        success_container = self.create_notification("✅ Success", message, "SuccessNotification")
        self.show_notification(success_container, 3000)
    
    def create_notification(self, title: str, message: str, object_name: str) -> QFrame:
        """Create modern notification widget"""
        notification = QFrame()
        notification.setObjectName(object_name)
        
        layout = QHBoxLayout(notification)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        title_label = QLabel(title)
        title_label.setObjectName("NotificationTitle")
        
        message_label = QLabel(message)
        message_label.setObjectName("NotificationMessage")
        
        layout.addWidget(title_label)
        layout.addWidget(message_label)
        layout.addStretch()
        
        return notification
    
    def show_notification(self, notification: QFrame, duration: int):
        """Show notification temporarily"""
        self.recipe_layout.addWidget(notification, 0, 0, 1, 4)
        
        QTimer.singleShot(duration, lambda: (
            self.recipe_layout.removeWidget(notification),
            notification.deleteLater()
        ))
    
    def resizeEvent(self, event):
        """Handle window resize for responsive layout"""
        super().resizeEvent(event)
        
        if hasattr(self, 'loading_indicator'):
            # Center loading indicator
            x = (self.width() - self.loading_indicator.width()) // 2
            y = (self.height() - self.loading_indicator.height()) // 2
            self.loading_indicator.move(x, y)

    def show_temporary_message(self, message: str, duration: int = 3000, is_error: bool = False):
        """
        Show a temporary message to the user (toast-style notification)
        
        Args:
            message: Message to display
            duration: How long to show message (milliseconds)  
            is_error: Whether this is an error message (affects styling)
        """
        try:
            # Create temporary message label if it doesn't exist
            if not hasattr(self, 'temp_message_label'):
                self.temp_message_label = QLabel(self)
                self.temp_message_label.setAlignment(Qt.AlignCenter)
                self.temp_message_label.hide()
                self.temp_message_label.setWordWrap(True)
            
            # Set message and styling
            self.temp_message_label.setText(message)
            if is_error:
                self.temp_message_label.setStyleSheet("""
                    QLabel {
                        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                            stop: 0 #FFE4E1,
                            stop: 1 #FFC0CB);
                        color: #8B0000;
                        font-size: 14px;
                        font-weight: 600;
                        font-family: 'Georgia', serif;
                        padding: 15px;
                        border: 2px solid #DC143C;
                        border-radius: 10px;
                        max-width: 400px;
                    }
                """)
            else:
                self.temp_message_label.setStyleSheet("""
                    QLabel {
                        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                            stop: 0 #F0FFF0,
                            stop: 1 #E6FFE6);
                        color: #006400;
                        font-size: 14px;
                        font-weight: 600;
                        font-family: 'Georgia', serif;
                        padding: 15px;
                        border: 2px solid #32CD32;
                        border-radius: 10px;
                        max-width: 400px;
                    }
                """)
            
            # Position the message (center-bottom of the view)
            self.temp_message_label.adjustSize()
            parent_rect = self.rect()
            label_rect = self.temp_message_label.rect()
            x = (parent_rect.width() - label_rect.width()) // 2
            y = parent_rect.height() - label_rect.height() - 50  # 50px from bottom
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