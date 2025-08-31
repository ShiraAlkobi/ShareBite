from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, 
    QScrollArea, QGridLayout, QTabWidget, QDialog, QLineEdit, QTextEdit,
    QSpacerItem, QSizePolicy, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap
from models.login_model import UserData
from models.profile_model import Recipe
from typing import List, Optional

class RecipeCard(QFrame):
    """Individual recipe card component"""
    
    recipe_selected = Signal(int)
    like_toggled = Signal(int)
    
    def __init__(self, recipe: Recipe, parent=None):
        super().__init__(parent)
        self.recipe = recipe
        self.setObjectName("ProfileRecipeCard")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup recipe card UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Recipe image placeholder
        image_frame = QFrame()
        image_frame.setObjectName("ProfileRecipeImage")
        image_frame.setFixedHeight(120)
        
        image_layout = QVBoxLayout(image_frame)
        image_layout.setAlignment(Qt.AlignCenter)
        
        image_label = QLabel("🍳")
        image_label.setObjectName("ProfileRecipeImageLabel")
        image_layout.addWidget(image_label)
        
        # Recipe content
        content_frame = QFrame()
        content_frame.setObjectName("ProfileRecipeContent")
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(8)
        
        # Title
        title_label = QLabel(self.recipe.title)
        title_label.setObjectName("ProfileRecipeTitle")
        title_label.setWordWrap(True)
        
        # Description
        desc_label = QLabel(self.recipe.description[:100] + "..." if len(self.recipe.description) > 100 else self.recipe.description)
        desc_label.setObjectName("ProfileRecipeDescription")
        desc_label.setWordWrap(True)
        
        # Stats and actions
        stats_frame = QFrame()
        stats_frame.setObjectName("ProfileRecipeStats")
        
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(8)
        
        # Like button
        self.like_button = QPushButton(f"❤️ {self.recipe.likes_count}")
        self.like_button.setObjectName("ProfileRecipeLikeButton")
        self.like_button.clicked.connect(lambda: self.like_toggled.emit(self.recipe.recipe_id))
        
        # Update like button style based on status
        self.update_like_status(self.recipe.is_liked)
        
        # View button
        view_button = QPushButton("View Recipe")
        view_button.setObjectName("ProfileRecipeViewButton")
        view_button.clicked.connect(lambda: self.recipe_selected.emit(self.recipe.recipe_id))
        
        stats_layout.addWidget(self.like_button)
        stats_layout.addStretch()
        stats_layout.addWidget(view_button)
        
        content_layout.addWidget(title_label)
        content_layout.addWidget(desc_label)
        content_layout.addWidget(stats_frame)
        
        layout.addWidget(image_frame)
        layout.addWidget(content_frame)
    
    def update_like_status(self, is_liked: bool):
        """Update like button based on status"""
        self.recipe.is_liked = is_liked
        if is_liked:
            self.like_button.setProperty("liked", "true")
        else:
            self.like_button.setProperty("liked", "false")
        
        # Force style refresh
        self.like_button.style().unpolish(self.like_button)
        self.like_button.style().polish(self.like_button)

class EditProfileDialog(QDialog):
    """Dialog for editing profile information"""
    
    profile_updated = Signal(str, str, str)  # username, email, bio
    
    def __init__(self, user_data: UserData, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.setObjectName("ProfileEditDialog")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup edit dialog UI"""
        self.setWindowTitle("Edit Profile")
        self.setModal(True)
        self.setMinimumSize(400, 350)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("Edit Your Profile")
        header.setObjectName("ProfileEditTitle")
        header.setAlignment(Qt.AlignCenter)
        
        # Form fields
        form_frame = QFrame()
        form_frame.setObjectName("ProfileEditForm")
        
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(12)
        
        # Username field
        username_label = QLabel("Username:")
        username_label.setObjectName("ProfileEditLabel")
        
        self.username_input = QLineEdit(self.user_data.username)
        self.username_input.setObjectName("ProfileEditInput")
        
        # Email field
        email_label = QLabel("Email:")
        email_label.setObjectName("ProfileEditLabel")
        
        self.email_input = QLineEdit(self.user_data.email)
        self.email_input.setObjectName("ProfileEditInput")
        
        # Bio field
        bio_label = QLabel("Bio:")
        bio_label.setObjectName("ProfileEditLabel")
        
        self.bio_input = QTextEdit(self.user_data.bio or "")
        self.bio_input.setObjectName("ProfileEditBio")
        self.bio_input.setMaximumHeight(100)
        
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(email_label)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(bio_label)
        form_layout.addWidget(self.bio_input)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.setObjectName("ProfileEditButtons")
        button_box.accepted.connect(self.save_profile)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(header)
        layout.addWidget(form_frame)
        layout.addWidget(button_box)
    
    def save_profile(self):
        """Save profile changes"""
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        bio = self.bio_input.toPlainText().strip()
        
        if not username or not email:
            return
        
        self.profile_updated.emit(username, email, bio)
        self.accept()

class ProfileView(QWidget):
    """Main profile view with tabs and user information"""
    
    home_requested = Signal()
    logout_requested = Signal()
    recipe_selected = Signal(int)
    recipe_like_toggled = Signal(int)
    profile_edit_requested = Signal()
    profile_update_submitted = Signal(str, str, str)
    refresh_requested = Signal()
    
    def __init__(self, user_data: UserData, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.user_recipe_cards = {}
        self.favorite_recipe_cards = {}
        self.edit_dialog = None
        self._user_recipes_loaded = False
        self._favorite_recipes_loaded = False
        
        self.setObjectName("ProfileView")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup main profile UI"""
        self.setWindowTitle(f"Profile - {self.user_data.username}")
        self.setMinimumSize(900, 600)
        
        # Create scroll area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Create scrollable content widget
        content_widget = QWidget()
        content_widget.setObjectName("ProfileContentWidget")
        
        # Main layout for the window
        window_layout = QVBoxLayout(self)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.addWidget(scroll_area)
        
        # Content layout
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Header section
        header_section = self.create_header_section()
        content_layout.addWidget(header_section)
        
        # User info section
        info_section = self.create_user_info_section()
        content_layout.addWidget(info_section)
        
        # Content tabs section
        tabs_section = self.create_tabs_section()
        content_layout.addWidget(tabs_section)
        
        # Message label
        self.message_label = QLabel()
        self.message_label.setObjectName("ProfileMessageLabel")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.hide()
        content_layout.addWidget(self.message_label)
        
        # Set the content widget to scroll area
        scroll_area.setWidget(content_widget)
        
        # Loading indicator
        self.setup_loading_indicator()
    
    def create_header_section(self):
        """Create header with navigation and branding"""
        header = QFrame()
        header.setObjectName("ProfileHeaderSection")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # Brand/Logo
        brand_container = QFrame()
        brand_container.setObjectName("ProfileBrandContainer")
        
        brand_layout = QHBoxLayout(brand_container)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(10)
        
        logo_label = QLabel("ShareBite")
        logo_label.setObjectName("ProfileBrandLogo")
        
        tagline_label = QLabel("Your Culinary Profile")
        tagline_label.setObjectName("ProfileBrandTagline")
        
        brand_layout.addWidget(logo_label)
        brand_layout.addWidget(tagline_label)
        brand_layout.addStretch()
        
        # Navigation buttons
        nav_container = QFrame()
        nav_container.setObjectName("ProfileNavContainer")
        
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(10)
        
        home_button = QPushButton("Home")
        home_button.setObjectName("ProfileNavButton")
        home_button.clicked.connect(self.home_requested.emit)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("ProfileNavButton")
        refresh_button.clicked.connect(self.refresh_requested.emit)
        
        logout_button = QPushButton("Logout")
        logout_button.setObjectName("ProfileLogoutButton")
        logout_button.clicked.connect(self.logout_requested.emit)
        
        nav_layout.addWidget(home_button)
        nav_layout.addWidget(refresh_button)
        nav_layout.addWidget(logout_button)
        
        layout.addWidget(brand_container)
        layout.addWidget(nav_container)
        
        return header
    
    def create_user_info_section(self):
        """Create user information display section"""
        info_section = QFrame()
        info_section.setObjectName("ProfileInfoSection")
        
        layout = QHBoxLayout(info_section)
        layout.setContentsMargins(25, 15, 25, 15)
        layout.setSpacing(20)
        
        # Profile picture placeholder - smaller
        pic_container = QFrame()
        pic_container.setObjectName("ProfilePicContainer")
        pic_container.setFixedSize(80, 80)
        
        pic_layout = QVBoxLayout(pic_container)
        pic_layout.setAlignment(Qt.AlignCenter)
        pic_layout.setContentsMargins(0, 0, 0, 0)
        
        pic_label = QLabel("👤")
        pic_label.setObjectName("ProfilePicLabel")
        pic_layout.addWidget(pic_label)
        
        # User details
        details_container = QFrame()
        details_container.setObjectName("ProfileDetailsContainer")
        
        details_layout = QVBoxLayout(details_container)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(4)
        
        # Username
        self.username_label = QLabel(self.user_data.username)
        self.username_label.setObjectName("ProfileUsername")
        
        # Email
        self.email_label = QLabel(self.user_data.email)
        self.email_label.setObjectName("ProfileEmail")
        
        # Bio
        bio_text = self.user_data.bio if self.user_data.bio else "No bio available"
        self.bio_label = QLabel(bio_text)
        self.bio_label.setObjectName("ProfileBio")
        self.bio_label.setWordWrap(True)
        
        # Member since
        member_since = self.user_data.createdat if self.user_data.createdat else "Unknown"
        member_label = QLabel(f"Member since: {member_since[:10] if member_since != 'Unknown' else member_since}")
        member_label.setObjectName("ProfileMemberSince")
        
        details_layout.addWidget(self.username_label)
        details_layout.addWidget(self.email_label)
        details_layout.addWidget(self.bio_label)
        details_layout.addWidget(member_label)
        details_layout.addStretch()
        
        # Edit button
        edit_container = QFrame()
        edit_container.setObjectName("ProfileEditContainer")
        
        edit_layout = QVBoxLayout(edit_container)
        edit_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)
        edit_layout.setContentsMargins(0, 0, 0, 0)
        
        edit_button = QPushButton("Edit Profile")
        edit_button.setObjectName("ProfileEditButton")
        edit_button.clicked.connect(self.profile_edit_requested.emit)
        
        edit_layout.addWidget(edit_button)
        edit_layout.addStretch()
        
        layout.addWidget(pic_container)
        layout.addWidget(details_container, 1)
        layout.addWidget(edit_container)
        
        return info_section
    
    def create_tabs_section(self):
        """Create tabs section for recipes"""
        tabs_container = QFrame()
        tabs_container.setObjectName("ProfileTabsContainer")
        
        layout = QVBoxLayout(tabs_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("ProfileTabWidget")
        
        # My Recipes tab
        self.my_recipes_tab = self.create_recipes_tab("my_recipes")
        self.tab_widget.addTab(self.my_recipes_tab, "My Recipes")
        
        # Favorite Recipes tab
        self.favorite_recipes_tab = self.create_recipes_tab("favorites")
        self.tab_widget.addTab(self.favorite_recipes_tab, "Favorite Recipes")
        
        layout.addWidget(self.tab_widget)
        
        return tabs_container
    
    def create_recipes_tab(self, tab_type):
        """Create a recipes tab with grid layout"""
        tab_widget = QWidget()
        tab_widget.setObjectName(f"Profile{tab_type.title()}Tab")
        
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Tab header
        header_label = QLabel("My Recipes" if tab_type == "my_recipes" else "Favorite Recipes")
        header_label.setObjectName("ProfileTabHeader")
        layout.addWidget(header_label)
        
        # Scroll area for recipes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Container for recipe cards
        recipes_container = QWidget()
        recipes_container.setObjectName(f"Profile{tab_type.title()}Container")
        
        # Grid layout for recipes
        grid_layout = QGridLayout(recipes_container)
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(10, 10, 10, 10)
        
        # Empty state label
        empty_label = QLabel("No recipes found" if tab_type == "my_recipes" else "No favorite recipes yet")
        empty_label.setObjectName("ProfileEmptyLabel")
        empty_label.setAlignment(Qt.AlignCenter)
        grid_layout.addWidget(empty_label, 0, 0)
        
        scroll_area.setWidget(recipes_container)
        layout.addWidget(scroll_area)
        
        # Store references
        if tab_type == "my_recipes":
            self.my_recipes_container = recipes_container
            self.my_recipes_grid = grid_layout
            self.my_recipes_empty = empty_label
        else:
            self.favorite_recipes_container = recipes_container
            self.favorite_recipes_grid = grid_layout
            self.favorite_recipes_empty = empty_label
        
        return tab_widget
    
    def setup_loading_indicator(self):
        """Setup loading indicator"""
        self.loading_indicator = QFrame(self)
        self.loading_indicator.setObjectName("ProfileLoadingIndicator")
        
        layout = QVBoxLayout(self.loading_indicator)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        
        loading_label = QLabel("Loading profile...")
        loading_label.setObjectName("ProfileLoadingLabel")
        loading_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(loading_label)
        self.loading_indicator.hide()
    
    def update_user_info(self, user_data: UserData):
        """Update user information display"""
        self.user_data = user_data
        self.username_label.setText(user_data.username)
        self.email_label.setText(user_data.email)
        
        bio_text = user_data.bio if user_data.bio else "No bio available"
        self.bio_label.setText(bio_text)
    
    def update_user_recipes(self, recipes: List[Recipe]):
        """Update user recipes display"""
        self._user_recipes_loaded = True
        
        # Clear existing cards
        self.clear_recipe_grid(self.my_recipes_grid, self.user_recipe_cards)
        
        if not recipes:
            self.my_recipes_empty.show()
            return
        
        self.my_recipes_empty.hide()
        
        # Add recipe cards
        for i, recipe in enumerate(recipes):
            card = RecipeCard(recipe)
            card.recipe_selected.connect(self.recipe_selected.emit)
            card.like_toggled.connect(self.recipe_like_toggled.emit)
            
            row = i // 3
            col = i % 3
            self.my_recipes_grid.addWidget(card, row, col)
            self.user_recipe_cards[recipe.recipe_id] = card
    
    def update_favorite_recipes(self, recipes: List[Recipe]):
        """Update favorite recipes display"""
        self._favorite_recipes_loaded = True
        
        # Clear existing cards
        self.clear_recipe_grid(self.favorite_recipes_grid, self.favorite_recipe_cards)
        
        if not recipes:
            self.favorite_recipes_empty.show()
            return
        
        self.favorite_recipes_empty.hide()
        
        # Add recipe cards
        for i, recipe in enumerate(recipes):
            card = RecipeCard(recipe)
            card.recipe_selected.connect(self.recipe_selected.emit)
            card.like_toggled.connect(self.recipe_like_toggled.emit)
            
            row = i // 3
            col = i % 3
            self.favorite_recipes_grid.addWidget(card, row, col)
            self.favorite_recipe_cards[recipe.recipe_id] = card
    
    def clear_recipe_grid(self, grid_layout, card_dict):
        """Clear recipe grid and card dictionary"""
        for card in card_dict.values():
            grid_layout.removeWidget(card)
            card.deleteLater()
        card_dict.clear()
    
    def update_recipe_like_status(self, recipe_id: int, is_liked: bool):
        """Update like status for a specific recipe"""
        # Update in both card dictionaries
        if recipe_id in self.user_recipe_cards:
            self.user_recipe_cards[recipe_id].update_like_status(is_liked)
        
        if recipe_id in self.favorite_recipe_cards:
            self.favorite_recipe_cards[recipe_id].update_like_status(is_liked)
    
    def show_edit_dialog(self):
        """Show edit profile dialog"""
        if not self.edit_dialog:
            self.edit_dialog = EditProfileDialog(self.user_data, self)
            self.edit_dialog.profile_updated.connect(self.profile_update_submitted.emit)
        
        self.edit_dialog.show()
    
    def hide_edit_dialog(self):
        """Hide edit profile dialog"""
        if self.edit_dialog:
            self.edit_dialog.hide()
    
    def show_message(self, message: str, is_error: bool = True):
        """Show message with styling"""
        self.message_label.setText(message)
        self.message_label.setProperty("error", str(is_error).lower())
        
        # Force style refresh
        self.message_label.style().unpolish(self.message_label)
        self.message_label.style().polish(self.message_label)
        
        self.message_label.show()
        QTimer.singleShot(5000, self.hide_message)
    
    def hide_message(self):
        """Hide message label"""
        self.message_label.hide()
    
    def set_loading(self, loading: bool):
        """Set loading state"""
        if loading:
            self.loading_indicator.show()
            self.loading_indicator.raise_()
        else:
            self.loading_indicator.hide()
    
    def cleanup(self):
        """Clean up resources"""
        if self.edit_dialog:
            self.edit_dialog.close()
        print("Profile view cleaned up")