"""
Recipe Details Window - Detailed Recipe View
Implements MVP pattern - View layer for displaying full recipe information
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QGridLayout, QTextEdit, QProgressBar,
    QMessageBox, QSplitter, QGroupBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QPainter, QBrush, QColor
from services.api_service import APIManager
from typing import Dict, Any, Optional


class RecipeDetailsWindow(QWidget):
    """
    Recipe details window showing full recipe information
    Includes ingredients, instructions, nutrition info, and user interactions
    """
    
    # Signals for navigation
    back_to_home = Signal()
    edit_recipe = Signal(int)  # recipe_id
    
    def __init__(self, api_service, recipe_model, parent=None):
        super().__init__(parent)
        self.api_service = api_service
        self.api_manager = APIManager(api_service)
        self.recipe_model = recipe_model
        
        self.current_recipe = None
        self.recipe_id = None
        self.is_loading = False
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Setup recipe details UI"""
        self.setObjectName("RecipeDetailsWindow")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header with navigation
        self.setup_header(main_layout)
        
        # Main content area
        self.setup_content_area(main_layout)
        
        # Loading indicator
        self.loading_bar = QProgressBar()
        self.loading_bar.setObjectName("loadingBar")
        self.loading_bar.setVisible(False)
        self.loading_bar.setRange(0, 0)
        main_layout.addWidget(self.loading_bar)
        
        # Apply styling
        self.setStyleSheet(self.get_details_styles())
        
    def setup_header(self, main_layout):
        """Setup header with navigation and actions"""
        header_layout = QHBoxLayout()
        
        # Back button
        self.back_button = QPushButton("← חזור לעמוד הבית")
        self.back_button.setObjectName("backButton")
        header_layout.addWidget(self.back_button)
        
        header_layout.addStretch()
        
        # Recipe actions
        self.like_button = QPushButton("🤍 אהבתי")
        self.like_button.setObjectName("likeButton")
        header_layout.addWidget(self.like_button)
        
        self.favorite_button = QPushButton("☆ מועדפים")
        self.favorite_button.setObjectName("favoriteButton")
        header_layout.addWidget(self.favorite_button)
        
        self.share_button = QPushButton("📤 שתף")
        self.share_button.setObjectName("shareButton")
        header_layout.addWidget(self.share_button)
        
        self.edit_button = QPushButton("✏️ ערוך")
        self.edit_button.setObjectName("editButton")
        self.edit_button.setVisible(False)  # Only show for recipe owner
        header_layout.addWidget(self.edit_button)
        
        main_layout.addLayout(header_layout)
        
    def setup_content_area(self, main_layout):
        """Setup main content area"""
        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setObjectName("contentScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(20)
        
        # Recipe header section
        self.setup_recipe_header(content_layout)
        
        # Recipe body sections
        self.setup_recipe_body(content_layout)
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
    def setup_recipe_header(self, content_layout):
        """Setup recipe header with image, title, and basic info"""
        header_frame = QFrame()
        header_frame.setObjectName("recipeHeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setSpacing(20)
        
        # Recipe image
        self.recipe_image = QLabel()
        self.recipe_image.setObjectName("recipeDetailImage")
        self.recipe_image.setFixedSize(300, 200)
        self.recipe_image.setAlignment(Qt.AlignCenter)
        self.recipe_image.setStyleSheet("""
            QLabel#recipeDetailImage {
                background-color: #f0f0f0;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
        """)
        header_layout.addWidget(self.recipe_image)
        
        # Recipe info
        info_layout = QVBoxLayout()
        
        # Title
        self.recipe_title = QLabel()
        self.recipe_title.setObjectName("recipeDetailTitle")
        self.recipe_title.setWordWrap(True)
        info_layout.addWidget(self.recipe_title)
        
        # Description
        self.recipe_description = QLabel()
        self.recipe_description.setObjectName("recipeDetailDesc")
        self.recipe_description.setWordWrap(True)
        info_layout.addWidget(self.recipe_description)
        
        # Metadata grid
        metadata_frame = QFrame()
        metadata_frame.setObjectName("metadataFrame")
        metadata_layout = QGridLayout(metadata_frame)
        
        # Author
        metadata_layout.addWidget(QLabel("מחבר:"), 0, 0)
        self.author_label = QLabel()
        self.author_label.setObjectName("authorLabel")
        metadata_layout.addWidget(self.author_label, 0, 1)
        
        # Difficulty
        metadata_layout.addWidget(QLabel("רמת קושי:"), 1, 0)
        self.difficulty_label = QLabel()
        metadata_layout.addWidget(self.difficulty_label, 1, 1)
        
        # Prep time
        metadata_layout.addWidget(QLabel("זמן הכנה:"), 2, 0)
        self.prep_time_label = QLabel()
        metadata_layout.addWidget(self.prep_time_label, 2, 1)
        
        # Cook time
        metadata_layout.addWidget(QLabel("זמן בישול:"), 0, 2)
        self.cook_time_label = QLabel()
        metadata_layout.addWidget(self.cook_time_label, 0, 3)
        
        # Servings
        metadata_layout.addWidget(QLabel("מספר מנות:"), 1, 2)
        self.servings_label = QLabel()
        metadata_layout.addWidget(self.servings_label, 1, 3)
        
        # Likes count
        metadata_layout.addWidget(QLabel("אהבו:"), 2, 2)
        self.likes_count_label = QLabel()
        metadata_layout.addWidget(self.likes_count_label, 2, 3)
        
        info_layout.addWidget(metadata_frame)
        
        # Tags
        self.tags_label = QLabel()
        self.tags_label.setObjectName("tagsLabel")
        self.tags_label.setWordWrap(True)
        info_layout.addWidget(self.tags_label)
        
        info_layout.addStretch()
        header_layout.addLayout(info_layout)
        
        content_layout.addWidget(header_frame)
        
    def setup_recipe_body(self, content_layout):
        """Setup recipe body with ingredients and instructions"""
        # Splitter for ingredients and instructions
        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("recipeSplitter")
        
        # Ingredients section
        ingredients_group = QGroupBox("מרכיבים")
        ingredients_group.setObjectName("ingredientsGroup")
        ingredients_layout = QVBoxLayout(ingredients_group)
        
        self.ingredients_list = QListWidget()
        self.ingredients_list.setObjectName("ingredientsList")
        ingredients_layout.addWidget(self.ingredients_list)
        
        splitter.addWidget(ingredients_group)
        
        # Instructions section
        instructions_group = QGroupBox("הוראות הכנה")
        instructions_group.setObjectName("instructionsGroup")
        instructions_layout = QVBoxLayout(instructions_group)
        
        self.instructions_list = QListWidget()
        self.instructions_list.setObjectName("instructionsList")
        instructions_layout.addWidget(self.instructions_list)
        
        splitter.addWidget(instructions_group)
        
        # Set splitter proportions
        splitter.setSizes([300, 500])
        content_layout.addWidget(splitter)
        
        # Nutrition info section (if available)
        self.setup_nutrition_section(content_layout)
        
    def setup_nutrition_section(self, content_layout):
        """Setup nutrition information section"""
        nutrition_group = QGroupBox("מידע תזונתי")
        nutrition_group.setObjectName("nutritionGroup")
        nutrition_layout = QGridLayout(nutrition_group)
        
        # Placeholder for nutrition data
        self.calories_label = QLabel("--")
        self.protein_label = QLabel("--")
        self.carbs_label = QLabel("--")
        self.fat_label = QLabel("--")
        
        nutrition_layout.addWidget(QLabel("קלוריות:"), 0, 0)
        nutrition_layout.addWidget(self.calories_label, 0, 1)
        nutrition_layout.addWidget(QLabel("חלבון:"), 0, 2)
        nutrition_layout.addWidget(self.protein_label, 0, 3)
        nutrition_layout.addWidget(QLabel("פחמימות:"), 1, 0)
        nutrition_layout.addWidget(self.carbs_label, 1, 1)
        nutrition_layout.addWidget(QLabel("שומן:"), 1, 2)
        nutrition_layout.addWidget(self.fat_label, 1, 3)
        
        content_layout.addWidget(nutrition_group)
        
    def setup_connections(self):
        """Setup signal connections"""
        # Navigation
        self.back_button.clicked.connect(self.back_to_home.emit)
        self.edit_button.clicked.connect(self.handle_edit_recipe)
        
        # Actions
        self.like_button.clicked.connect(self.handle_like_recipe)
        self.favorite_button.clicked.connect(self.handle_favorite_recipe)
        self.share_button.clicked.connect(self.handle_share_recipe)
        
        # Model signals
        self.recipe_model.recipe_updated.connect(self.on_recipe_updated)
        self.recipe_model.recipe_liked.connect(self.on_recipe_liked)
        self.recipe_model.recipe_favorited.connect(self.on_recipe_favorited)
        
    def load_recipe(self, recipe_id: int):
        """Load recipe details"""
        self.recipe_id = recipe_id
        self.set_loading(True)
        
        # Clear current content
        self.clear_recipe_data()
        
        # Load recipe from API
        self.api_manager.call_api(
            'get_recipe_by_id',
            success_callback=self.on_recipe_loaded,
            error_callback=self.on_recipe_error,
            recipe_id=recipe_id
        )
        
    def on_recipe_loaded(self, result: Dict[str, Any]):
        """Handle recipe loaded from API"""
        self.current_recipe = result.get('recipe', {})
        self.recipe_model.set_current_recipe(self.current_recipe)
        self.display_recipe_data()
        self.set_loading(False)
        
    def on_recipe_error(self, error: str):
        """Handle recipe loading error"""
        self.set_loading(False)
        QMessageBox.warning(self, "שגיאה", f"שגיאה בטעינת המתכון: {error}")
        self.back_to_home.emit()
        
    def display_recipe_data(self):
        """Display loaded recipe data"""
        if not self.current_recipe:
            return
            
        # Header info
        title = self.current_recipe.get('title', 'ללא כותרת')
        self.recipe_title.setText(title)
        
        description = self.current_recipe.get('description', 'אין תיאור')
        self.recipe_description.setText(description)
        
        # Image
        image_url = self.current_recipe.get('image_url', '')
        if image_url:
            self.recipe_image.setText("תמונה בטעינה...")
            # TODO: Load actual image
        else:
            self.recipe_image.setText("🍽️\nאין תמונה")
            
        # Metadata
        author = self.current_recipe.get('author_name', 'משתמש אנונימי')
        self.author_label.setText(author)
        
        difficulty = self.current_recipe.get('difficulty', 'easy')
        difficulty_text = {'easy': 'קל', 'medium': 'בינוני', 'hard': 'קשה'}.get(difficulty, 'קל')
        self.difficulty_label.setText(difficulty_text)
        
        prep_time = self.current_recipe.get('prep_time', 0)
        self.prep_time_label.setText(f"{prep_time} דקות")
        
        cook_time = self.current_recipe.get('cook_time', 0)
        self.cook_time_label.setText(f"{cook_time} דקות")
        
        servings = self.current_recipe.get('servings', 1)
        self.servings_label.setText(f"{servings} מנות")
        
        like_count = self.current_recipe.get('like_count', 0)
        self.likes_count_label.setText(f"{like_count} אנשים")
        
        # Tags
        tags = self.current_recipe.get('tags', [])
        if tags:
            tags_text = " • ".join(tags)
            self.tags_label.setText(f"תגיות: {tags_text}")
        else:
            self.tags_label.setText("אין תגיות")
            
        # Ingredients
        self.ingredients_list.clear()
        ingredients = self.current_recipe.get('ingredients', [])
        for i, ingredient in enumerate(ingredients, 1):
            item = QListWidgetItem(f"{i}. {ingredient}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.ingredients_list.addItem(item)
            
        # Instructions
        self.instructions_list.clear()
        instructions = self.current_recipe.get('instructions', [])
        for i, instruction in enumerate(instructions, 1):
            item = QListWidgetItem(f"{i}. {instruction}")
            self.instructions_list.addItem(item)
            
        # Update action buttons
        self.update_action_buttons()
        
        # Show edit button if user owns the recipe
        user_id = self.current_recipe.get('author_id')
        current_user = self.recipe_model.get_current_user() if hasattr(self.recipe_model, 'get_current_user') else None
        if current_user and current_user.get('user_id') == user_id:
            self.edit_button.setVisible(True)
        else:
            self.edit_button.setVisible(False)
            
    def update_action_buttons(self):
        """Update action buttons based on user interactions"""
        if not self.recipe_id:
            return
            
        # Get user interactions
        interactions = self.recipe_model.user_interactions.get(self.recipe_id, {})
        
        # Update like button
        is_liked = interactions.get('liked', False)
        like_icon = "❤️" if is_liked else "🤍"
        like_count = self.current_recipe.get('like_count', 0) if self.current_recipe else 0
        self.like_button.setText(f"{like_icon} אהבתי ({like_count})")
        
        # Update favorite button
        is_favorited = interactions.get('favorited', False)
        fav_icon = "⭐" if is_favorited else "☆"
        self.favorite_button.setText(f"{fav_icon} מועדפים")
        
    def handle_like_recipe(self):
        """Handle like button click"""
        if not self.recipe_id:
            return
            
        self.api_manager.call_api(
            'toggle_like_recipe',
            success_callback=lambda result: self.on_like_toggled(result),
            error_callback=self.on_action_error,
            recipe_id=self.recipe_id
        )
        
    def handle_favorite_recipe(self):
        """Handle favorite button click"""
        if not self.recipe_id:
            return
            
        self.api_manager.call_api(
            'toggle_favorite_recipe',
            success_callback=lambda result: self.on_favorite_toggled(result),
            error_callback=self.on_action_error,
            recipe_id=self.recipe_id
        )
        
    def handle_share_recipe(self):
        """Handle share button click"""
        if not self.current_recipe:
            return
            
        # For now, show a simple message with recipe info
        title = self.current_recipe.get('title', 'מתכון')
        author = self.current_recipe.get('author_name', 'משתמש')
        
        share_text = f"בדקו את המתכון המדהים הזה: '{title}' מאת {author}\n\nנמצא באפליקציית המתכונים שלנו!"
        
        QMessageBox.information(
            self,
            "שתף מתכון",
            f"טקסט לשיתוף:\n\n{share_text}\n\n(הועתק ללוח)"
        )
        
    def handle_edit_recipe(self):
        """Handle edit recipe button click"""
        if self.recipe_id:
            self.edit_recipe.emit(self.recipe_id)
            
    def on_like_toggled(self, result: Dict[str, Any]):
        """Handle like toggle result"""
        liked = result.get('liked', False)
        like_count = result.get('like_count', 0)
        
        # Update model
        self.recipe_model.update_like_status(self.recipe_id, liked, like_count)
        
        # Update current recipe data
        if self.current_recipe:
            self.current_recipe['like_count'] = like_count
            
        # Update button
        self.update_action_buttons()
        
    def on_favorite_toggled(self, result: Dict[str, Any]):
        """Handle favorite toggle result"""
        favorited = result.get('favorited', False)
        
        # Update model
        self.recipe_model.update_favorite_status(self.recipe_id, favorited)
        
        # Update button
        self.update_action_buttons()
        
    def on_action_error(self, error: str):
        """Handle action error"""
        QMessageBox.warning(self, "שגיאה", f"שגיאה בביצוע הפעולה: {error}")
        
    def on_recipe_updated(self, recipe_data: Dict[str, Any]):
        """Handle recipe model update signal"""
        if (self.current_recipe and 
            recipe_data.get('recipe_id') == self.current_recipe.get('recipe_id')):
            self.current_recipe.update(recipe_data)
            self.display_recipe_data()
            
    def on_recipe_liked(self, recipe_id: int, liked: bool):
        """Handle recipe liked signal"""
        if recipe_id == self.recipe_id:
            self.update_action_buttons()
            
    def on_recipe_favorited(self, recipe_id: int, favorited: bool):
        """Handle recipe favorited signal"""
        if recipe_id == self.recipe_id:
            self.update_action_buttons()
            
    def clear_recipe_data(self):
        """Clear all recipe data from display"""
        self.recipe_title.setText("טוען...")
        self.recipe_description.setText("טוען נתונים...")
        self.recipe_image.setText("🍽️\nטוען תמונה...")
        
        self.author_label.setText("--")
        self.difficulty_label.setText("--")
        self.prep_time_label.setText("--")
        self.cook_time_label.setText("--")
        self.servings_label.setText("--")
        self.likes_count_label.setText("--")
        self.tags_label.setText("--")
        
        self.ingredients_list.clear()
        self.instructions_list.clear()
        
        self.like_button.setText("🤍 אהבתי")
        self.favorite_button.setText("☆ מועדפים")
        self.edit_button.setVisible(False)
        
    def set_loading(self, loading: bool):
        """Set loading state"""
        self.is_loading = loading
        self.loading_bar.setVisible(loading)
        
        # Disable/enable buttons
        self.like_button.setEnabled(not loading)
        self.favorite_button.setEnabled(not loading)
        self.share_button.setEnabled(not loading)
        self.edit_button.setEnabled(not loading)
        
    def get_details_styles(self) -> str:
        """Get recipe details window styles"""
        return """
            QWidget#RecipeDetailsWindow {
                background-color: #f8f9fa;
            }
            
            QPushButton#backButton {
                background-color: #6c757d;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 10pt;
                padding: 8px 16px;
            }
            
            QPushButton#backButton:hover {
                background-color: #5a6268;
            }
            
            QPushButton#likeButton, QPushButton#favoriteButton, QPushButton#shareButton {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                color: #495057;
                font-size: 10pt;
                padding: 8px 16px;
                min-width: 100px;
            }
            
            QPushButton#likeButton:hover, QPushButton#favoriteButton:hover, QPushButton#shareButton:hover {
                border-color: #3498db;
                background-color: #f8f9ff;
            }
            
            QPushButton#editButton {
                background-color: #ffc107;
                border: none;
                border-radius: 6px;
                color: #212529;
                font-size: 10pt;
                font-weight: bold;
                padding: 8px 16px;
            }
            
            QPushButton#editButton:hover {
                background-color: #e0a800;
            }
            
            QFrame#recipeHeaderFrame {
                background-color: white;
                border: 1px solid #e1e8ed;
                border-radius: 12px;
                padding: 20px;
            }
            
            QLabel#recipeDetailTitle {
                font-size: 24pt;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
            
            QLabel#recipeDetailDesc {
                font-size: 12pt;
                color: #6c757d;
                line-height: 1.5;
                margin-bottom: 15px;
            }
            
            QFrame#metadataFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
            }
            
            QLabel#authorLabel {
                font-weight: bold;
                color: #3498db;
            }
            
            QLabel#tagsLabel {
                font-size: 10pt;
                color: #6c757d;
                font-style: italic;
                margin-top: 10px;
            }
            
            QSplitter#recipeSplitter::handle {
                background-color: #e9ecef;
                width: 3px;
            }
            
            QGroupBox#ingredientsGroup, QGroupBox#instructionsGroup, QGroupBox#nutritionGroup {
                font-size: 12pt;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #e1e8ed;
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 10px;
            }
            
            QGroupBox#ingredientsGroup::title, QGroupBox#instructionsGroup::title, QGroupBox#nutritionGroup::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                background-color: white;
            }
            
            QListWidget#ingredientsList, QListWidget#instructionsList {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 10px;
                font-size: 11pt;
                line-height: 1.4;
            }
            
            QListWidget#ingredientsList::item, QListWidget#instructionsList::item {
                padding: 8px;
                border-bottom: 1px solid #f1f3f4;
            }
            
            QListWidget#ingredientsList::item:hover, QListWidget#instructionsList::item:hover {
                background-color: #f8f9ff;
            }
            
            QListWidget#ingredientsList::item:checked {
                background-color: #e8f5e8;
                color: #28a745;
                text-decoration: line-through;
            }
            
            QScrollArea#contentScrollArea {
                background-color: transparent;
                border: none;
            }
            
            QProgressBar#loadingBar {
                border: none;
                border-radius: 4px;
                background-color: #ecf0f1;
                text-align: center;
                height: 6px;
            }
            
            QProgressBar#loadingBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 3px;
            }
        """