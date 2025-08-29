"""
Profile Window - User Profile Management
Implements MVP pattern - View layer for user profile display and management
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QScrollArea, QFrame, QGridLayout, QTextEdit,
    QProgressBar, QMessageBox, QTabWidget, QListWidget, QListWidgetItem,
    QGroupBox, QFileDialog, QSplitter, QComboBox  # הוסף QComboBox כאן
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QPainter, QBrush, QColor
from services.api_service import APIManager
from typing import Dict, List, Any, Optional


class StatCard(QFrame):
    """Widget for displaying user statistics"""
    
    def __init__(self, title: str, value: str, icon: str = "📊"):
        super().__init__()
        self.setup_ui(title, value, icon)
        
    def setup_ui(self, title: str, value: str, icon: str):
        """Setup stat card UI"""
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)
        
        # Icon and value
        value_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setObjectName("statIcon")
        value_layout.addWidget(icon_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        value_layout.addWidget(value_label)
        value_layout.addStretch()
        
        layout.addLayout(value_layout)
        
        # Title
        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        layout.addWidget(title_label)
        
        # Styling
        self.setStyleSheet("""
            QFrame#statCard {
                background-color: white;
                border: 1px solid #e1e8ed;
                border-radius: 8px;
                margin: 5px;
            }
            QLabel#statIcon {
                font-size: 24pt;
            }
            QLabel#statValue {
                font-size: 18pt;
                font-weight: bold;
                color: #2c3e50;
            }
            QLabel#statTitle {
                font-size: 10pt;
                color: #6c757d;
            }
        """)


class RecipeListItem(QFrame):
    """Custom widget for recipe list items"""
    
    recipe_selected = Signal(int)
    recipe_edit = Signal(int)
    recipe_delete = Signal(int)
    
    def __init__(self, recipe_data: Dict[str, Any]):
        super().__init__()
        self.recipe_data = recipe_data
        self.recipe_id = recipe_data.get('recipe_id')
        self.setup_ui()
        
    def setup_ui(self):
        """Setup recipe item UI"""
        self.setObjectName("recipeItem")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        
        # Recipe info
        info_layout = QVBoxLayout()
        
        # Title
        title = self.recipe_data.get('title', 'ללא כותרת')
        title_label = QLabel(title)
        title_label.setObjectName("recipeItemTitle")
        info_layout.addWidget(title_label)
        
        # Metadata
        metadata_layout = QHBoxLayout()
        
        like_count = self.recipe_data.get('like_count', 0)
        metadata_layout.addWidget(QLabel(f"❤️ {like_count}"))
        
        created_at = self.recipe_data.get('created_at', '')
        if created_at:
            metadata_layout.addWidget(QLabel(f"📅 {created_at[:10]}"))
            
        difficulty = self.recipe_data.get('difficulty', 'easy')
        difficulty_text = {'easy': 'קל', 'medium': 'בינוני', 'hard': 'קשה'}.get(difficulty, 'קל')
        metadata_layout.addWidget(QLabel(f"⭐ {difficulty_text}"))
        
        metadata_layout.addStretch()
        info_layout.addLayout(metadata_layout)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Action buttons
        actions_layout = QVBoxLayout()
        
        view_btn = QPushButton("צפה")
        view_btn.setObjectName("actionButton")
        view_btn.clicked.connect(lambda: self.recipe_selected.emit(self.recipe_id))
        actions_layout.addWidget(view_btn)
        
        edit_btn = QPushButton("ערוך")
        edit_btn.setObjectName("editButton")
        edit_btn.clicked.connect(lambda: self.recipe_edit.emit(self.recipe_id))
        actions_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("מחק")
        delete_btn.setObjectName("deleteButton")
        delete_btn.clicked.connect(lambda: self.confirm_delete())
        actions_layout.addWidget(delete_btn)
        
        layout.addLayout(actions_layout)
        
        # Styling
        self.setStyleSheet("""
            QFrame#recipeItem {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                margin: 3px;
            }
            QFrame#recipeItem:hover {
                border-color: #3498db;
                background-color: #f8f9ff;
            }
            QLabel#recipeItemTitle {
                font-size: 12pt;
                font-weight: bold;
                color: #2c3e50;
            }
            QPushButton#actionButton {
                background-color: #3498db;
                border: none;
                border-radius: 4px;
                color: white;
                padding: 4px 8px;
                font-size: 9pt;
            }
            QPushButton#editButton {
                background-color: #ffc107;
                border: none;
                border-radius: 4px;
                color: #212529;
                padding: 4px 8px;
                font-size: 9pt;
            }
            QPushButton#deleteButton {
                background-color: #dc3545;
                border: none;
                border-radius: 4px;
                color: white;
                padding: 4px 8px;
                font-size: 9pt;
            }
        """)
        
    def confirm_delete(self):
        """Confirm recipe deletion"""
        reply = QMessageBox.question(
            self,
            "מחיקת מתכון",
            f"האם אתם בטוחים שברצונכם למחוק את המתכון '{self.recipe_data.get('title')}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.recipe_delete.emit(self.recipe_id)


class ProfileWindow(QWidget):
    """
    User profile window
    Shows user information, statistics, and manages user recipes
    """
    
    # Signals for navigation
    back_to_home = Signal()
    logout = Signal()
    recipe_selected = Signal(int)
    edit_recipe = Signal(int)
    
    def __init__(self, api_service, user_model, parent=None):
        super().__init__(parent)
        self.api_service = api_service
        self.api_manager = APIManager(api_service)
        self.user_model = user_model
        
        self.current_user_id = None
        self.user_data = None
        self.user_stats = {}
        self.user_recipes = []
        self.user_favorites = []
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Setup profile window UI"""
        self.setObjectName("ProfileWindow")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        self.setup_header(main_layout)
        
        # Main content with tabs
        self.setup_content_tabs(main_layout)
        
        # Loading indicator
        self.loading_bar = QProgressBar()
        self.loading_bar.setObjectName("loadingBar")
        self.loading_bar.setVisible(False)
        self.loading_bar.setRange(0, 0)
        main_layout.addWidget(self.loading_bar)
        
        # Apply styling
        self.setStyleSheet(self.get_profile_styles())
        
    def setup_header(self, main_layout):
        """Setup profile header"""
        header_layout = QHBoxLayout()
        
        # Back button
        self.back_button = QPushButton("← חזור לעמוד הבית")
        self.back_button.setObjectName("backButton")
        header_layout.addWidget(self.back_button)
        
        # Title
        self.profile_title = QLabel("הפרופיל שלי")
        self.profile_title.setObjectName("profileTitle")
        header_layout.addWidget(self.profile_title)
        
        header_layout.addStretch()
        
        # Action buttons
        self.edit_profile_button = QPushButton("ערוך פרופיל")
        self.edit_profile_button.setObjectName("editButton")
        header_layout.addWidget(self.edit_profile_button)
        
        self.logout_button = QPushButton("התנתק")
        self.logout_button.setObjectName("logoutButton")
        header_layout.addWidget(self.logout_button)
        
        main_layout.addLayout(header_layout)
        
    def setup_content_tabs(self, main_layout):
        """Setup main content with tabs"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("profileTabs")
        
        # Profile info tab
        self.setup_profile_info_tab()
        
        # My recipes tab
        self.setup_my_recipes_tab()
        
        # Favorites tab
        self.setup_favorites_tab()
        
        # Statistics tab
        self.setup_statistics_tab()
        
        main_layout.addWidget(self.tab_widget)
        
    def setup_profile_info_tab(self):
        """Setup profile information tab"""
        profile_tab = QWidget()
        profile_layout = QVBoxLayout(profile_tab)
        profile_layout.setSpacing(20)
        
        # User info section
        user_info_group = QGroupBox("פרטי משתמש")
        user_info_group.setObjectName("profileGroup")
        user_info_layout = QGridLayout(user_info_group)
        
        # Profile picture
        self.profile_picture = QLabel()
        self.profile_picture.setObjectName("profilePicture")
        self.profile_picture.setFixedSize(120, 120)
        self.profile_picture.setAlignment(Qt.AlignCenter)
        self.profile_picture.setText("👤")
        self.profile_picture.setStyleSheet("""
            QLabel#profilePicture {
                border: 2px solid #e9ecef;
                border-radius: 60px;
                background-color: #f8f9fa;
                font-size: 48pt;
            }
        """)
        user_info_layout.addWidget(self.profile_picture, 0, 0, 3, 1)
        
        # User details
        user_info_layout.addWidget(QLabel("שם משתמש:"), 0, 1)
        self.username_label = QLabel("--")
        self.username_label.setObjectName("userDetailLabel")
        user_info_layout.addWidget(self.username_label, 0, 2)
        
        user_info_layout.addWidget(QLabel("אימייל:"), 1, 1)
        self.email_label = QLabel("--")
        self.email_label.setObjectName("userDetailLabel")
        user_info_layout.addWidget(self.email_label, 1, 2)
        
        user_info_layout.addWidget(QLabel("תאריך הצטרפות:"), 2, 1)
        self.joined_label = QLabel("--")
        self.joined_label.setObjectName("userDetailLabel")
        user_info_layout.addWidget(self.joined_label, 2, 2)
        
        profile_layout.addWidget(user_info_group)
        
        # Bio section
        bio_group = QGroupBox("אודותיי")
        bio_group.setObjectName("profileGroup")
        bio_layout = QVBoxLayout(bio_group)
        
        self.bio_text = QTextEdit()
        self.bio_text.setObjectName("bioText")
        self.bio_text.setPlaceholderText("ספרו קצת על עצמכם...")
        self.bio_text.setMaximumHeight(100)
        self.bio_text.setReadOnly(True)
        bio_layout.addWidget(self.bio_text)
        
        profile_layout.addWidget(bio_group)
        profile_layout.addStretch()
        
        self.tab_widget.addTab(profile_tab, "פרטי פרופיל")
        
    def setup_my_recipes_tab(self):
        """Setup my recipes tab"""
        recipes_tab = QWidget()
        recipes_layout = QVBoxLayout(recipes_tab)
        
        # Header with count
        recipes_header_layout = QHBoxLayout()
        self.recipes_count_label = QLabel("המתכונים שלי (0)")
        self.recipes_count_label.setObjectName("tabHeader")
        recipes_header_layout.addWidget(self.recipes_count_label)
        
        recipes_header_layout.addStretch()
        
        # Sort options
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(QLabel("מיון:"))
        
        self.recipes_sort_combo = QComboBox()
        self.recipes_sort_combo.addItems(["חדשים ביותר", "פופולריים", "לפי שם"])
        sort_layout.addWidget(self.recipes_sort_combo)
        
        recipes_header_layout.addLayout(sort_layout)
        recipes_layout.addLayout(recipes_header_layout)
        
        # Recipes list
        self.recipes_scroll = QScrollArea()
        self.recipes_scroll.setObjectName("recipesScroll")
        self.recipes_scroll.setWidgetResizable(True)
        
        self.recipes_container = QWidget()
        self.recipes_layout = QVBoxLayout(self.recipes_container)
        self.recipes_layout.setContentsMargins(10, 10, 10, 10)
        self.recipes_layout.setSpacing(5)
        self.recipes_layout.addStretch()
        
        self.recipes_scroll.setWidget(self.recipes_container)
        recipes_layout.addWidget(self.recipes_scroll)
        
        self.tab_widget.addTab(recipes_tab, "המתכונים שלי")
        
    def setup_favorites_tab(self):
        """Setup favorites tab"""
        favorites_tab = QWidget()
        favorites_layout = QVBoxLayout(favorites_tab)
        
        # Header
        self.favorites_count_label = QLabel("המועדפים שלי (0)")
        self.favorites_count_label.setObjectName("tabHeader")
        favorites_layout.addWidget(self.favorites_count_label)
        
        # Favorites list
        self.favorites_scroll = QScrollArea()
        self.favorites_scroll.setObjectName("favoritesScroll")
        self.favorites_scroll.setWidgetResizable(True)
        
        self.favorites_container = QWidget()
        self.favorites_layout = QVBoxLayout(self.favorites_container)
        self.favorites_layout.setContentsMargins(10, 10, 10, 10)
        self.favorites_layout.setSpacing(5)
        self.favorites_layout.addStretch()
        
        self.favorites_scroll.setWidget(self.favorites_container)
        favorites_layout.addWidget(self.favorites_scroll)
        
        self.tab_widget.addTab(favorites_tab, "מועדפים")
        
    def setup_statistics_tab(self):
        """Setup statistics tab"""
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        # Stats header
        stats_header = QLabel("הסטטיסטיקות שלי")
        stats_header.setObjectName("tabHeader")
        stats_layout.addWidget(stats_header)
        
        # Stats grid
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(15)
        
        # Initialize stat cards
        self.recipes_stat = StatCard("מתכונים", "0", "📝")
        self.likes_stat = StatCard("לייקים שקיבלתי", "0", "❤️")
        self.favorites_stat = StatCard("הוספות למועדפים", "0", "⭐")
        self.views_stat = StatCard("צפיות", "0", "👀")
        
        self.stats_grid.addWidget(self.recipes_stat, 0, 0)
        self.stats_grid.addWidget(self.likes_stat, 0, 1)
        self.stats_grid.addWidget(self.favorites_stat, 1, 0)
        self.stats_grid.addWidget(self.views_stat, 1, 1)
        
        stats_layout.addLayout(self.stats_grid)
        stats_layout.addStretch()
        
        self.tab_widget.addTab(stats_tab, "סטטיסטיקות")
        
    def setup_connections(self):
        """Setup signal connections"""
        # Navigation
        self.back_button.clicked.connect(self.back_to_home.emit)
        self.logout_button.clicked.connect(self.handle_logout)
        
        # Profile actions
        self.edit_profile_button.clicked.connect(self.toggle_edit_mode)
        
        # Sorting
        self.recipes_sort_combo.currentTextChanged.connect(self.sort_recipes)
        
        # Model signals
        self.user_model.user_updated.connect(self.on_user_updated)
        self.user_model.user_stats_updated.connect(self.on_stats_updated)
        
    def load_user_data(self, user_id: int):
        """Load user profile data"""
        self.current_user_id = user_id
        self.set_loading(True)
        
        # Load user profile
        self.api_manager.call_api(
            'get_user_profile',
            success_callback=self.on_user_profile_loaded,
            error_callback=self.on_data_error,
            user_id=user_id
        )
        
        # Load user stats
        self.api_manager.call_api(
            'get_user_stats',
            success_callback=self.on_user_stats_loaded,
            error_callback=self.on_data_error,
            user_id=user_id
        )
        
        # Load user recipes
        self.api_manager.call_api(
            'get_user_recipes',
            success_callback=self.on_user_recipes_loaded,
            error_callback=self.on_data_error,
            user_id=user_id
        )
        
        # Load user favorites
        self.api_manager.call_api(
            'get_user_favorites',
            success_callback=self.on_user_favorites_loaded,
            error_callback=self.on_data_error,
            user_id=user_id
        )
        
    def on_user_profile_loaded(self, result: Dict[str, Any]):
        """Handle user profile loaded"""
        self.user_data = result.get('user', {})
        self.display_user_info()
        self.set_loading(False)
        
    def on_user_stats_loaded(self, result: Dict[str, Any]):
        """Handle user stats loaded"""
        self.user_stats = result.get('stats', {})
        self.display_user_stats()
        
    def on_user_recipes_loaded(self, result: Dict[str, Any]):
        """Handle user recipes loaded"""
        self.user_recipes = result.get('recipes', [])
        self.display_user_recipes()
        
    def on_user_favorites_loaded(self, result: Dict[str, Any]):
        """Handle user favorites loaded"""
        self.user_favorites = result.get('favorites', [])
        self.display_user_favorites()
        
    def on_data_error(self, error: str):
        """Handle data loading error"""
        self.set_loading(False)
        QMessageBox.warning(self, "שגיאה", f"שגיאה בטעינת הנתונים: {error}")
        
    def display_user_info(self):
        """Display user information"""
        if not self.user_data:
            return
            
        self.username_label.setText(self.user_data.get('username', '--'))
        self.email_label.setText(self.user_data.get('email', '--'))
        
        created_at = self.user_data.get('created_at', '')
        if created_at:
            self.joined_label.setText(created_at[:10])
        else:
            self.joined_label.setText('--')
            
        bio = self.user_data.get('bio', '')
        self.bio_text.setPlainText(bio)
        
    def display_user_stats(self):
        """Display user statistics"""
        recipes_count = self.user_stats.get('recipes_count', 0)
        likes_count = self.user_stats.get('total_likes', 0)
        favorites_count = self.user_stats.get('total_favorites', 0)
        views_count = self.user_stats.get('total_views', 0)
        
        # Update stat cards
        self.recipes_stat.findChild(QLabel, "statValue").setText(str(recipes_count))
        self.likes_stat.findChild(QLabel, "statValue").setText(str(likes_count))
        self.favorites_stat.findChild(QLabel, "statValue").setText(str(favorites_count))
        self.views_stat.findChild(QLabel, "statValue").setText(str(views_count))
        
    def display_user_recipes(self):
        """Display user recipes"""
        # Clear existing recipes
        self.clear_recipes_list()
        
        # Update count
        count = len(self.user_recipes)
        self.recipes_count_label.setText(f"המתכונים שלי ({count})")
        
        # Add recipe items
        for recipe in self.user_recipes:
            recipe_item = RecipeListItem(recipe)
            recipe_item.recipe_selected.connect(self.recipe_selected.emit)
            recipe_item.recipe_edit.connect(self.edit_recipe.emit)
            recipe_item.recipe_delete.connect(self.handle_delete_recipe)
            
            # Insert before stretch
            self.recipes_layout.insertWidget(self.recipes_layout.count() - 1, recipe_item)
            
    def display_user_favorites(self):
        """Display user favorites"""
        # Clear existing favorites
        self.clear_favorites_list()
        
        # Update count
        count = len(self.user_favorites)
        self.favorites_count_label.setText(f"המועדפים שלי ({count})")
        
        # Add favorite items
        for recipe in self.user_favorites:
            recipe_item = RecipeListItem(recipe)
            recipe_item.recipe_selected.connect(self.recipe_selected.emit)
            # Hide edit/delete buttons for favorites
            recipe_item.findChild(QPushButton, "editButton").setVisible(False)
            recipe_item.findChild(QPushButton, "deleteButton").setVisible(False)
            
            # Insert before stretch
            self.favorites_layout.insertWidget(self.favorites_layout.count() - 1, recipe_item)
            
    def clear_recipes_list(self):
        """Clear recipes list"""
        while self.recipes_layout.count() > 1:  # Keep stretch
            child = self.recipes_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def clear_favorites_list(self):
        """Clear favorites list"""
        while self.favorites_layout.count() > 1:  # Keep stretch
            child = self.favorites_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def handle_delete_recipe(self, recipe_id: int):
        """Handle recipe deletion"""
        self.api_manager.call_api(
            'delete_recipe',
            success_callback=lambda result: self.on_recipe_deleted(recipe_id),
            error_callback=self.on_data_error,
            recipe_id=recipe_id
        )
        
    def on_recipe_deleted(self, recipe_id: int):
        """Handle recipe deleted successfully"""
        # Remove from local list
        self.user_recipes = [r for r in self.user_recipes if r.get('recipe_id') != recipe_id]
        
        # Refresh display
        self.display_user_recipes()
        
        QMessageBox.information(self, "הצלחה", "המתכון נמחק בהצלחה!")
        
    def sort_recipes(self, sort_type: str):
        """Sort user recipes"""
        if sort_type == "חדשים ביותר":
            self.user_recipes.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        elif sort_type == "פופולריים":
            self.user_recipes.sort(key=lambda x: x.get('like_count', 0), reverse=True)
        elif sort_type == "לפי שם":
            self.user_recipes.sort(key=lambda x: x.get('title', ''))
            
        self.display_user_recipes()
        
    def toggle_edit_mode(self):
        """Toggle profile edit mode"""
        if self.bio_text.isReadOnly():
            # Enable editing
            self.bio_text.setReadOnly(False)
            self.edit_profile_button.setText("שמור שינויים")
        else:
            # Save changes
            new_bio = self.bio_text.toPlainText()
            self.save_profile_changes({'bio': new_bio})
            
    def save_profile_changes(self, changes: Dict[str, Any]):
        """Save profile changes"""
        self.api_manager.call_api(
            'update_user_profile',
            success_callback=self.on_profile_saved,
            error_callback=self.on_data_error,
            user_id=self.current_user_id,
            user_data=changes
        )
        
    def on_profile_saved(self, result: Dict[str, Any]):
        """Handle profile saved successfully"""
        self.bio_text.setReadOnly(True)
        self.edit_profile_button.setText("ערוך פרופיל")
        QMessageBox.information(self, "הצלחה", "הפרופיל עודכן בהצלחה!")
        
    def handle_logout(self):
        """Handle logout confirmation"""
        reply = QMessageBox.question(
            self,
            "התנתקות",
            "האם אתם בטוחים שברצונכם להתנתק?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.logout.emit()
            
    def on_user_updated(self, user_data: Dict[str, Any]):
        """Handle user model update"""
        self.user_data = user_data
        self.display_user_info()
        
    def on_stats_updated(self, stats: Dict[str, Any]):
        """Handle stats model update"""
        self.user_stats = stats
        self.display_user_stats()
        
    def set_loading(self, loading: bool):
        """Set loading state"""
        self.loading_bar.setVisible(loading)
        
        # Disable/enable controls
        controls = [
            self.edit_profile_button, self.logout_button,
            self.recipes_sort_combo
        ]
        
        for control in controls:
            control.setEnabled(not loading)
            
    def get_profile_styles(self) -> str:
        """Get profile window styles"""
        return """
            QWidget#ProfileWindow {
                background-color: #f7fafc;
            }
            
            QLabel#profileTitle {
                font-size: 22pt;
                font-weight: 700;
                color: #2d3748;
                padding: 8px 0;
            }
            
            QPushButton#backButton {
                background-color: #a0aec0;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 10pt;
                padding: 8px 14px;
            }
            
            QPushButton#backButton:hover {
                background-color: #718096;
            }
            
            QPushButton#editButton {
                background-color: #ed8936;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 10pt;
                padding: 8px 14px;
            }
            
            QPushButton#editButton:hover {
                background-color: #dd6b20;
            }
            
            QPushButton#logoutButton {
                background-color: #f56565;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 10pt;
                padding: 8px 14px;
            }
            
            QPushButton#logoutButton:hover {
                background-color: #e53e3e;
            }
            
            QTabWidget#profileTabs {
                background-color: transparent;
                border: none;
            }
            
            QTabWidget#profileTabs::pane {
                border: none;
                background-color: white;
                border-radius: 10px;
                margin-top: 8px;
            }
            
            QTabBar::tab {
                background-color: #edf2f7;
                border: none;
                border-radius: 8px 8px 0 0;
                padding: 10px 18px;
                margin-right: 2px;
                font-size: 10pt;
                font-weight: 600;
                color: #4a5568;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                color: #2d3748;
            }
            
            QTabBar::tab:hover {
                background-color: #e2e8f0;
            }
            
            QGroupBox#profileGroup {
                font-size: 11pt;
                font-weight: 600;
                color: #2d3748;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin: 8px 0;
                padding-top: 12px;
                background-color: white;
            }
            
            QGroupBox#profileGroup::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px 0 6px;
                background-color: white;
            }
            
            QLabel#userDetailLabel {
                font-size: 11pt;
                color: #2d3748;
                font-weight: 600;
            }
            
            QLabel#tabHeader {
                font-size: 16pt;
                font-weight: 700;
                color: #2d3748;
                margin-bottom: 12px;
            }
            
            QTextEdit#bioText {
                background-color: #f7fafc;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px;
                font-size: 10pt;
                color: #2d3748;
            }
            
            QTextEdit#bioText:focus {
                border-color: #4299e1;
                background-color: white;
            }
            
            QScrollArea#recipesScroll, QScrollArea#favoritesScroll {
                background-color: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            }
            
            QProgressBar#loadingBar {
                border: none;
                border-radius: 4px;
                background-color: #edf2f7;
                height: 6px;
            }
            
            QProgressBar#loadingBar::chunk {
                background-color: #4299e1;
                border-radius: 3px;
            }
        """