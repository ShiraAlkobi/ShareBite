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
        self.setup_ui()
    
    def setup_ui(self):
        """Setup recipe card UI with simplified layout"""
        self.setFixedSize(300, 280)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #FFFEF7,
                    stop: 0.05 #FFF8E1,
                    stop: 1 #F5F5DC);
                border: 2px solid #D4AF37;
                border-radius: 12px;
            }
            QFrame:hover {
                border: 2px solid #B8860B;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #FFFFFF,
                    stop: 1 #FFF8DC);
            }
        """)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(139, 69, 19, 60))
        shadow.setOffset(3, 5)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Recipe image (placeholder for now)
        image_frame = QFrame()
        image_frame.setFixedHeight(120)
        image_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #FF6347,
                    stop: 0.5 #FF4500,
                    stop: 1 #DC143C);
                border: 2px solid #8B4513;
                border-radius: 8px;
            }
        """)
        
        image_layout = QVBoxLayout(image_frame)
        if self.recipe.image_url:
            # TODO: Load actual image from URL
            image_label = QLabel("📸 Recipe Image")
        else:
            image_label = QLabel("🍽️ No Image")
            
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: 600;
                font-family: 'Georgia', serif;
                background: transparent;
                border: none;
            }
        """)
        image_layout.addWidget(image_label)
        
        # Dish name (recipe title)
        self.title_label = QLabel(self.recipe.title)
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(50)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #8B4513;
                font-size: 18px;
                font-weight: 700;
                font-family: 'Georgia', serif;
                background: transparent;
                border: none;
                text-align: center;
            }
        """)
        
        # Author name
        author_label = QLabel(f"by Chef {self.recipe.author_name}")
        author_label.setAlignment(Qt.AlignCenter)
        author_label.setStyleSheet("""
            QLabel {
                color: #A0522D;
                font-size: 14px;
                font-weight: 500;
                font-family: 'Georgia', serif;
                background: transparent;
                border: none;
                font-style: italic;
            }
        """)
        
        # Date created
        try:
            # Parse the date and format it nicely
            if self.recipe.created_at:
                if isinstance(self.recipe.created_at, str):
                    # Try to parse ISO format date
                    from datetime import datetime
                    try:
                        date_obj = datetime.fromisoformat(self.recipe.created_at.replace('Z', '+00:00'))
                        formatted_date = date_obj.strftime("%B %d, %Y")
                    except:
                        # If parsing fails, use the string as is
                        formatted_date = self.recipe.created_at[:10]  # Just take YYYY-MM-DD part
                else:
                    formatted_date = str(self.recipe.created_at)[:10]
            else:
                formatted_date = "Date unknown"
        except:
            formatted_date = "Date unknown"
            
        date_label = QLabel(f"Created: {formatted_date}")
        date_label.setAlignment(Qt.AlignCenter)
        date_label.setStyleSheet("""
            QLabel {
                color: #CD853F;
                font-size: 12px;
                font-weight: 500;
                font-family: 'Georgia', serif;
                background: transparent;
                border: none;
            }
        """)
        
        # Action buttons row
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)
        
        # Like button
        self.like_button = QPushButton(f"♥ {self.recipe.likes_count}")
        self.like_button.setFixedSize(70, 32)
        like_color = "#DC143C" if self.recipe.is_liked else "#CD853F"
        self.like_button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {like_color};
                border: 1px solid {like_color};
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Georgia', serif;
            }}
            QPushButton:hover {{
                background: rgba(220, 20, 60, 0.1);
                color: #DC143C;
                border-color: #DC143C;
            }}
        """)
        self.like_button.clicked.connect(lambda: self.recipe_liked.emit(self.recipe.recipe_id))
        
        # Favorite button
        star_symbol = "★" if self.recipe.is_favorited else "☆"
        self.favorite_button = QPushButton(star_symbol)
        self.favorite_button.setFixedSize(32, 32)
        fav_color = "#FFD700" if self.recipe.is_favorited else "#CD853F"
        self.favorite_button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {fav_color};
                border: 1px solid {fav_color};
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(255, 215, 0, 0.2);
                color: #FFD700;
                border-color: #FFD700;
            }}
        """)
        self.favorite_button.clicked.connect(lambda: self.recipe_favorited.emit(self.recipe.recipe_id))
        
        # View recipe button
        view_button = QPushButton("View Recipe")
        view_button.setFixedHeight(32)
        view_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #32CD32,
                    stop: 1 #228B22);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Georgia', serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #7FFF00,
                    stop: 1 #32CD32);
            }
        """)
        view_button.clicked.connect(lambda: self.recipe_clicked.emit(self.recipe.recipe_id))
        
        actions_layout.addWidget(self.like_button)
        actions_layout.addWidget(self.favorite_button)
        actions_layout.addStretch()
        actions_layout.addWidget(view_button)
        
        # Add all widgets to main layout
        layout.addWidget(image_frame)
        layout.addSpacing(5)
        layout.addWidget(self.title_label)
        layout.addWidget(author_label)
        layout.addWidget(date_label)
        layout.addSpacing(8)
        layout.addLayout(actions_layout)
    
    def update_like_status(self, is_liked: bool, likes_count: int):
        """Update like button status"""
        self.recipe.is_liked = is_liked
        self.recipe.likes_count = likes_count
        
        self.like_button.setText(f"♥ {likes_count}")
        like_color = "#DC143C" if is_liked else "#CD853F"
        self.like_button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {like_color};
                border: 1px solid {like_color};
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Georgia', serif;
            }}
            QPushButton:hover {{
                background: rgba(220, 20, 60, 0.1);
                color: #DC143C;
                border-color: #DC143C;
            }}
        """)
    
    def update_favorite_status(self, is_favorited: bool):
        """Update favorite button status"""
        self.recipe.is_favorited = is_favorited
        
        star_symbol = "★" if is_favorited else "☆"
        self.favorite_button.setText(star_symbol)
        fav_color = "#FFD700" if is_favorited else "#CD853F"
        self.favorite_button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {fav_color};
                border: 1px solid {fav_color};
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(255, 215, 0, 0.2);
                color: #FFD700;
                border-color: #FFD700;
            }}
        """)

class SearchBar(QFrame):
    """Search bar widget"""
    
    search_requested = Signal(str, dict)  # query, filters
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup search bar UI"""
        self.setFixedHeight(60)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.8);
                border: 2px solid #D4AF37;
                border-radius: 15px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for delicious recipes...")
        self.search_input.setFixedHeight(35)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #FFFFFF;
                border: 2px solid #CD853F;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 14px;
                color: #8B4513;
                font-family: 'Georgia', serif;
            }
            QLineEdit:focus {
                border: 2px solid #D2691E;
                background: #FFF8DC;
            }
            QLineEdit::placeholder {
                color: rgba(139, 69, 19, 0.6);
                font-style: italic;
            }
        """)
        self.search_input.returnPressed.connect(self.perform_search)
        
        # Filter dropdown
        self.filter_combo = QComboBox()
        self.filter_combo.setFixedSize(120, 35)
        self.filter_combo.addItems(["All Recipes", "Breakfast", "Lunch", "Dinner", "Dessert", "Snacks"])
        self.filter_combo.setStyleSheet("""
            QComboBox {
                background: #FFFFFF;
                border: 2px solid #CD853F;
                border-radius: 8px;
                padding: 0 8px;
                font-size: 12px;
                color: #8B4513;
                font-family: 'Georgia', serif;
            }
            QComboBox:focus {
                border: 2px solid #D2691E;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)
        
        # Search button
        search_button = QPushButton("Find Recipes")
        search_button.setFixedSize(100, 35)
        search_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #FF6347,
                    stop: 1 #DC143C);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Georgia', serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #FF7F50,
                    stop: 1 #FF6347);
            }
        """)
        search_button.clicked.connect(self.perform_search)
        
        layout.addWidget(self.search_input)
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
    """User statistics display widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup user stats UI"""
        self.setFixedHeight(100)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(139, 69, 19, 0.8),
                    stop: 1 rgba(210, 105, 30, 0.8));
                border: 2px solid #8B4513;
                border-radius: 12px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(30)
        
        # Stats containers
        self.recipes_stat = self.create_stat_widget("Recipes Created", "0")
        self.likes_stat = self.create_stat_widget("Likes Received", "0")
        self.favorites_stat = self.create_stat_widget("Total Favorites", "0")
        
        layout.addWidget(self.recipes_stat)
        layout.addWidget(self.likes_stat)
        layout.addWidget(self.favorites_stat)
        layout.addStretch()
    
    def create_stat_widget(self, label: str, value: str) -> QWidget:
        """Create individual stat widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 24px;
                font-weight: 800;
                font-family: 'Georgia', serif;
                background: transparent;
                border: none;
            }
        """)
        
        label_widget = QLabel(label)
        label_widget.setAlignment(Qt.AlignCenter)
        label_widget.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 11px;
                font-weight: 500;
                font-family: 'Georgia', serif;
                background: transparent;
                border: none;
            }
        """)
        
        layout.addWidget(value_label)
        layout.addWidget(label_widget)
        
        # Store reference to value label for updates
        widget.value_label = value_label
        
        return widget
    
    def update_stats(self, stats: UserStatsData):
        """Update displayed statistics"""
        self.recipes_stat.value_label.setText(str(stats.recipes_created))
        self.likes_stat.value_label.setText(str(stats.total_likes_received))
        self.favorites_stat.value_label.setText(str(stats.total_favorites_received))

class HomeView(QWidget):
    """
    Main home view implementing the View part of MVP pattern
    Displays recipe feed with search and user stats
    """
    
    # Signals for communication with Presenter
    search_requested = Signal(str, dict)  # query, filters
    refresh_requested = Signal()
    add_recipe_requested = Signal()
    user_profile_requested = Signal()
    logout_requested = Signal()
    
    recipe_clicked = Signal(int)  # recipe_id
    recipe_liked = Signal(int)  # recipe_id
    recipe_favorited = Signal(int)  # recipe_id
    
    filter_changed = Signal(dict)  # filters
    load_more_requested = Signal()
    
    def __init__(self, user_data: UserData, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.recipe_cards = {}  # recipe_id -> RecipeCard mapping
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the main home UI"""
        self.setWindowTitle(f"Recipe Share - Welcome {self.user_data.username}")
        self.setMinimumSize(1000, 700)
        
        # Main background
        self.setStyleSheet("""
            QWidget {
                background: qradialgradient(cx: 0.3, cy: 0.3, radius: 1.2,
                    stop: 0 #FFF8DC,
                    stop: 0.4 #FFFACD,
                    stop: 0.8 #F5DEB3,
                    stop: 1 #DEB887);
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Top section: Welcome + Quick Actions
        self.setup_top_section(main_layout)
        
        # Search section
        self.search_bar = SearchBar()
        main_layout.addWidget(self.search_bar)
        
        # User stats section
        self.stats_widget = UserStatsWidget()
        main_layout.addWidget(self.stats_widget)
        
        # Content area with scroll
        self.setup_content_area(main_layout)
        
        # Loading overlay
        self.setup_loading_overlay()
    
    def setup_top_section(self, main_layout):
        """Setup top welcome and actions section"""
        top_frame = QFrame()
        top_frame.setFixedHeight(80)
        top_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(255, 255, 255, 0.9),
                    stop: 1 rgba(255, 248, 220, 0.9));
                border: 2px solid #D4AF37;
                border-radius: 15px;
            }
        """)
        
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(25, 15, 25, 15)
        
        # Welcome message
        welcome_label = QLabel(f"Welcome back, Chef {self.user_data.username}!")
        welcome_label.setStyleSheet("""
            QLabel {
                color: #8B4513;
                font-size: 24px;
                font-weight: 700;
                font-family: 'Georgia', serif;
                background: transparent;
                border: none;
            }
        """)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        # Add recipe button
        add_button = QPushButton("Add Recipe")
        add_button.setFixedSize(120, 40)
        add_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #32CD32,
                    stop: 1 #228B22);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
                font-family: 'Georgia', serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #7FFF00,
                    stop: 1 #32CD32);
            }
        """)
        add_button.clicked.connect(self.add_recipe_requested.emit)
        
        # Profile button
        profile_button = QPushButton("Profile")
        profile_button.setFixedSize(80, 40)
        profile_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #D2691E;
                border: 2px solid #D2691E;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
                font-family: 'Georgia', serif;
            }
            QPushButton:hover {
                background: rgba(210, 105, 30, 0.1);
                color: #8B4513;
                border-color: #8B4513;
            }
        """)
        profile_button.clicked.connect(self.user_profile_requested.emit)
        
        # Logout button
        logout_button = QPushButton("Logout")
        logout_button.setFixedSize(80, 40)
        logout_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #DC143C;
                border: 2px solid #DC143C;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
                font-family: 'Georgia', serif;
            }
            QPushButton:hover {
                background: rgba(220, 20, 60, 0.1);
                color: #B22222;
                border-color: #B22222;
            }
        """)
        logout_button.clicked.connect(self.logout_requested.emit)
        
        actions_layout.addWidget(add_button)
        actions_layout.addWidget(profile_button)
        actions_layout.addWidget(logout_button)
        
        top_layout.addWidget(welcome_label)
        top_layout.addStretch()
        top_layout.addLayout(actions_layout)
        
        main_layout.addWidget(top_frame)
    
    def setup_content_area(self, main_layout):
        """Setup scrollable content area for recipe cards"""
        # Content header
        content_header = QFrame()
        content_header.setFixedHeight(50)
        
        header_layout = QHBoxLayout(content_header)
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        self.content_title = QLabel("Latest Recipes")
        self.content_title.setStyleSheet("""
            QLabel {
                color: #8B4513;
                font-size: 20px;
                font-weight: 700;
                font-family: 'Georgia', serif;
            }
        """)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.setFixedSize(80, 30)
        refresh_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #FF6347,
                    stop: 1 #DC143C);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 11px;
                font-weight: 600;
                font-family: 'Georgia', serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #FF7F50,
                    stop: 1 #FF6347);
            }
        """)
        refresh_button.clicked.connect(self.refresh_requested.emit)
        
        header_layout.addWidget(self.content_title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_button)
        
        main_layout.addWidget(content_header)
        
        # Scrollable recipe area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(139, 69, 19, 0.2);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(139, 69, 19, 0.6);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(139, 69, 19, 0.8);
            }
        """)
        
        # Recipe grid container
        self.recipe_container = QWidget()
        self.recipe_layout = QGridLayout(self.recipe_container)
        self.recipe_layout.setSpacing(20)
        self.recipe_layout.setContentsMargins(20, 20, 20, 20)
        
        self.scroll_area.setWidget(self.recipe_container)
        main_layout.addWidget(self.scroll_area)
    
    def setup_loading_overlay(self):
        """Setup loading overlay"""
        self.loading_label = QLabel("Loading delicious recipes...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("""
            QLabel {
                background: rgba(139, 69, 19, 0.9);
                color: white;
                font-size: 18px;
                font-weight: 600;
                font-family: 'Georgia', serif;
                padding: 20px;
                border-radius: 15px;
            }
        """)
        self.loading_label.hide()
    
    def setup_connections(self):
        """Setup signal connections"""
        self.search_bar.search_requested.connect(self.search_requested.emit)
    
    def display_recipes(self, recipes: List[RecipeData]):
        """Display recipe cards in grid"""
        self.clear_recipe_grid()
        
        if not recipes:
            self.show_empty_state("No recipes found")
            return
        
        # Add recipe cards to grid
        columns = 3  # 3 cards per row
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
        """Display search results"""
        self.display_recipes(recipes)
        self.content_title.setText(f"Search Results for '{query}' ({len(recipes)} found)")
    
    def display_user_stats(self, stats: UserStatsData):
        """Display user statistics"""
        self.stats_widget.update_stats(stats)
    
    def update_recipe_like_status(self, recipe_id: int, is_liked: bool):
        """Update like status for specific recipe card"""
        if recipe_id in self.recipe_cards:
            card = self.recipe_cards[recipe_id]
            likes_count = card.recipe.likes_count
            if is_liked and not card.recipe.is_liked:
                likes_count += 1
            elif not is_liked and card.recipe.is_liked:
                likes_count = max(0, likes_count - 1)
            card.update_like_status(is_liked, likes_count)
    
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
        """Show empty state message"""
        empty_label = QLabel(message)
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setStyleSheet("""
            QLabel {
                color: #8B4513;
                font-size: 18px;
                font-weight: 600;
                font-family: 'Georgia', serif;
                background: rgba(255, 255, 255, 0.8);
                border: 2px dashed #D4AF37;
                border-radius: 15px;
                padding: 40px;
                margin: 20px;
            }
        """)
        self.recipe_layout.addWidget(empty_label, 0, 0, 1, 3)  # Span across 3 columns
    
    def set_loading_state(self, loading: bool):
        """Set loading state"""
        if loading:
            self.loading_label.show()
            self.loading_label.raise_()
        else:
            self.loading_label.hide()
    
    def show_error_message(self, message: str):
        """Show error message to user"""
        error_label = QLabel(f"Error: {message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("""
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
                margin: 10px;
            }
        """)
        
        # Add to top of recipe area temporarily
        self.recipe_layout.addWidget(error_label, 0, 0, 1, 3)
        
        # Auto-remove after 5 seconds
        QTimer.singleShot(5000, lambda: (
            self.recipe_layout.removeWidget(error_label),
            error_label.deleteLater()
        ))
    
    def show_success_message(self, message: str):
        """Show success message to user"""
        success_label = QLabel(message)
        success_label.setAlignment(Qt.AlignCenter)
        success_label.setStyleSheet("""
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
                margin: 10px;
            }
        """)
        
        # Add to top of recipe area temporarily
        self.recipe_layout.addWidget(success_label, 0, 0, 1, 3)
        
        # Auto-remove after 3 seconds
        QTimer.singleShot(3000, lambda: (
            self.recipe_layout.removeWidget(success_label),
            success_label.deleteLater()
        ))
    
    def resizeEvent(self, event):
        """Handle window resize to position loading overlay"""
        super().resizeEvent(event)
        if hasattr(self, 'loading_label'):
            # Center loading label
            x = (self.width() - self.loading_label.width()) // 2
            y = (self.height() - self.loading_label.height()) // 2
            self.loading_label.move(x, y)