from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, 
    QScrollArea, QGridLayout, QLineEdit, QTextEdit, QSpinBox,
    QFileDialog, QCompleter, QSizePolicy, QSpacerItem,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal, QStringListModel, QTimer
from PySide6.QtGui import QFont, QPixmap, QValidator
from models.login_model import UserData
from typing import List, Optional, Dict
import os

class FlowLayout(QVBoxLayout):
    """Custom flow layout for tags"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(5, 5, 5, 5)
        self.setSpacing(8)

class TagWidget(QFrame):
    """Individual tag widget with remove button"""
    
    tag_removed = Signal(str)
    
    def __init__(self, tag_name: str, parent=None):
        super().__init__(parent)
        self.tag_name = tag_name
        self.setObjectName("AddRecipeTagWidget")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup tag widget UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        
        # Tag label
        tag_label = QLabel(self.tag_name)
        tag_label.setObjectName("AddRecipeTagLabel")
        
        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setObjectName("AddRecipeTagRemoveButton")
        remove_btn.setFixedSize(20, 20)
        remove_btn.clicked.connect(lambda: self.tag_removed.emit(self.tag_name))
        
        layout.addWidget(tag_label)
        layout.addWidget(remove_btn)

class TagsWidget(QFrame):
    """Widget for managing recipe tags"""
    
    tags_changed = Signal(list)  # List[str]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tags = []
        self.available_tags = []
        self.setObjectName("AddRecipeTagsWidget")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup tags widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Header
        header_label = QLabel("Recipe Tags")
        header_label.setObjectName("AddRecipeTagsHeader")
        
        # Tag input section
        input_frame = QFrame()
        input_frame.setObjectName("AddRecipeTagInputFrame")
        
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(8)
        
        # Tag search/input
        self.tag_input = QLineEdit()
        self.tag_input.setObjectName("AddRecipeTagInput")
        self.tag_input.setPlaceholderText("Search existing tags or add new...")
        self.tag_input.returnPressed.connect(self.add_tag)
        
        # Completer for existing tags
        self.completer = QCompleter()
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.tag_input.setCompleter(self.completer)
        
        # Add tag button
        add_btn = QPushButton("Add Tag")
        add_btn.setObjectName("AddRecipeTagAddButton")
        add_btn.clicked.connect(self.add_tag)
        
        input_layout.addWidget(self.tag_input)
        input_layout.addWidget(add_btn)
        
        # Common tags section
        common_frame = QFrame()
        common_frame.setObjectName("AddRecipeCommonTagsFrame")
        
        common_layout = QVBoxLayout(common_frame)
        common_layout.setContentsMargins(10, 10, 10, 10)
        common_layout.setSpacing(8)
        
        common_label = QLabel("Common Tags:")
        common_label.setObjectName("AddRecipeCommonTagsLabel")
        
        self.common_tags_container = QFrame()
        self.common_tags_container.setObjectName("AddRecipeCommonTagsContainer")
        self.common_tags_layout = QHBoxLayout(self.common_tags_container)
        self.common_tags_layout.setContentsMargins(0, 0, 0, 0)
        self.common_tags_layout.setSpacing(6)
        
        common_layout.addWidget(common_label)
        common_layout.addWidget(self.common_tags_container)
        
        # Selected tags section
        selected_frame = QFrame()
        selected_frame.setObjectName("AddRecipeSelectedTagsFrame")
        
        selected_layout = QVBoxLayout(selected_frame)
        selected_layout.setContentsMargins(10, 10, 10, 10)
        selected_layout.setSpacing(8)
        
        selected_label = QLabel("Selected Tags:")
        selected_label.setObjectName("AddRecipeSelectedTagsLabel")
        
        # Scroll area for selected tags
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(100)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        self.selected_tags_container = QWidget()
        self.selected_tags_container.setObjectName("AddRecipeSelectedTagsContainer")
        self.selected_tags_layout = FlowLayout(self.selected_tags_container)
        
        scroll_area.setWidget(self.selected_tags_container)
        
        selected_layout.addWidget(selected_label)
        selected_layout.addWidget(scroll_area)
        
        layout.addWidget(header_label)
        layout.addWidget(input_frame)
        layout.addWidget(common_frame)
        layout.addWidget(selected_frame)
    
    def set_available_tags(self, tags: List[str]):
        """Set available tags for autocomplete"""
        self.available_tags = tags
        model = QStringListModel(tags)
        self.completer.setModel(model)
        
        # Update common tags (show first 8)
        self.update_common_tags(tags[:8])
    
    def update_common_tags(self, common_tags: List[str]):
        """Update common tags display"""
        # Clear existing common tags
        for i in reversed(range(self.common_tags_layout.count())):
            child = self.common_tags_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
        
        # Add new common tags
        for tag in common_tags:
            if tag not in self.tags:
                btn = QPushButton(tag)
                btn.setObjectName("AddRecipeCommonTagButton")
                btn.clicked.connect(lambda checked, t=tag: self.add_tag_by_name(t))
                self.common_tags_layout.addWidget(btn)
        
        # Add stretch at the end
        self.common_tags_layout.addStretch()
    
    def add_tag(self):
        """Add tag from input field"""
        tag_text = self.tag_input.text().strip()
        if tag_text:
            self.add_tag_by_name(tag_text)
            self.tag_input.clear()
    
    def add_tag_by_name(self, tag_name: str):
        """Add a tag by name"""
        tag_name = tag_name.strip().lower()
        if tag_name and tag_name not in self.tags:
            self.tags.append(tag_name)
            self.add_tag_widget(tag_name)
            self.tags_changed.emit(self.tags)
            
            # Update common tags to hide added tag
            self.update_common_tags([t for t in self.available_tags[:8] if t not in self.tags])
    
    def add_tag_widget(self, tag_name: str):
        """Add a tag widget to the selected tags area"""
        tag_widget = TagWidget(tag_name)
        tag_widget.tag_removed.connect(self.remove_tag)
        
        # Create a container for the tag widget
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(2, 2, 2, 2)
        container_layout.addWidget(tag_widget)
        
        self.selected_tags_layout.addWidget(container)
    
    def remove_tag(self, tag_name: str):
        """Remove a tag"""
        if tag_name in self.tags:
            self.tags.remove(tag_name)
            
            # Remove tag widget
            for i in reversed(range(self.selected_tags_layout.count())):
                item = self.selected_tags_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget:
                        # Find the TagWidget inside the container
                        for child in widget.findChildren(TagWidget):
                            if child.tag_name == tag_name:
                                widget.deleteLater()
                                break
            
            self.tags_changed.emit(self.tags)
            
            # Update common tags to show removed tag
            self.update_common_tags([t for t in self.available_tags[:8] if t not in self.tags])
    
    def get_tags(self) -> List[str]:
        """Get current tags"""
        return self.tags.copy()
    
    def set_tags(self, tags: List[str]):
        """Set current tags"""
        # Clear existing tags
        for i in reversed(range(self.selected_tags_layout.count())):
            item = self.selected_tags_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        
        self.tags = []
        
        # Add new tags
        for tag in tags:
            self.add_tag_by_name(tag)

class AddRecipeView(QWidget):
    """Main view for adding a new recipe"""
    
    # Signals
    home_requested = Signal()
    logout_requested = Signal()
    recipe_creation_requested = Signal(dict)  # recipe_data
    tags_load_requested = Signal()
    photo_upload_requested = Signal(str)  # file_path
    
    def __init__(self, user_data: UserData, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.selected_image_path = None
        self.setObjectName("AddRecipeView")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup main UI"""
        self.setWindowTitle("Add New Recipe - ShareBite")
        self.setMinimumSize(1000, 700)
        
        # Create scroll area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Create scrollable content widget
        content_widget = QWidget()
        content_widget.setObjectName("AddRecipeContentWidget")
        
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
        
        # Main form section
        form_section = self.create_form_section()
        content_layout.addWidget(form_section)
        
        # Action buttons section
        actions_section = self.create_actions_section()
        content_layout.addWidget(actions_section)
        
        # Message label
        self.message_label = QLabel()
        self.message_label.setObjectName("AddRecipeMessageLabel")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.hide()
        content_layout.addWidget(self.message_label)
        
        # Set the content widget to scroll area
        scroll_area.setWidget(content_widget)
    
    def create_header_section(self):
        """Create header with navigation and branding"""
        header = QFrame()
        header.setObjectName("AddRecipeHeaderSection")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # Brand/Logo
        brand_container = QFrame()
        brand_container.setObjectName("AddRecipeBrandContainer")
        
        brand_layout = QHBoxLayout(brand_container)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(10)
        
        logo_label = QLabel("ShareBite")
        logo_label.setObjectName("AddRecipeBrandLogo")
        
        tagline_label = QLabel("Add New Recipe")
        tagline_label.setObjectName("AddRecipeBrandTagline")
        
        brand_layout.addWidget(logo_label)
        brand_layout.addWidget(tagline_label)
        brand_layout.addStretch()
        
        # Navigation buttons
        nav_container = QFrame()
        nav_container.setObjectName("AddRecipeNavContainer")
        
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(10)
        
        home_button = QPushButton("Home")
        home_button.setObjectName("AddRecipeNavButton")
        home_button.clicked.connect(self.home_requested.emit)
        
        logout_button = QPushButton("Logout")
        logout_button.setObjectName("AddRecipeLogoutButton")
        logout_button.clicked.connect(self.logout_requested.emit)
        
        nav_layout.addWidget(home_button)
        nav_layout.addWidget(logout_button)
        
        layout.addWidget(brand_container)
        layout.addWidget(nav_container)
        
        return header
    
    def create_form_section(self):
        """Create main form section"""
        form_container = QFrame()
        form_container.setObjectName("AddRecipeFormContainer")
        
        layout = QVBoxLayout(form_container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Form content in a card-like frame
        form_card = QFrame()
        form_card.setObjectName("AddRecipeFormCard")
        
        form_layout = QGridLayout(form_card)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(20)
        
        row = 0
        
        # Recipe Title (Required)
        title_label = QLabel("Recipe Title *")
        title_label.setObjectName("AddRecipeFieldLabel")
        
        self.title_input = QLineEdit()
        self.title_input.setObjectName("AddRecipeFieldInput")
        self.title_input.setPlaceholderText("Enter an appetizing recipe title...")
        
        form_layout.addWidget(title_label, row, 0)
        form_layout.addWidget(self.title_input, row, 1, 1, 2)
        row += 1
        
        # Recipe Description
        desc_label = QLabel("Description")
        desc_label.setObjectName("AddRecipeFieldLabel")
        
        self.description_input = QTextEdit()
        self.description_input.setObjectName("AddRecipeDescriptionInput")
        self.description_input.setPlaceholderText("Describe your recipe, its origin, or special notes...")
        self.description_input.setMaximumHeight(100)
        
        form_layout.addWidget(desc_label, row, 0)
        form_layout.addWidget(self.description_input, row, 1, 1, 2)
        row += 1
        
        # Servings
        servings_label = QLabel("Servings")
        servings_label.setObjectName("AddRecipeFieldLabel")
        
        self.servings_input = QSpinBox()
        self.servings_input.setObjectName("AddRecipeServingsInput")
        self.servings_input.setRange(1, 50)
        self.servings_input.setValue(4)
        self.servings_input.setSuffix(" people")
        
        form_layout.addWidget(servings_label, row, 0)
        form_layout.addWidget(self.servings_input, row, 1)
        row += 1
        
        # Ingredients (Required)
        ingredients_label = QLabel("Ingredients *")
        ingredients_label.setObjectName("AddRecipeFieldLabel")
        
        self.ingredients_input = QTextEdit()
        self.ingredients_input.setObjectName("AddRecipeIngredientsInput")
        self.ingredients_input.setPlaceholderText("List ingredients with quantities:\ne.g., 2 cups flour\n1 tsp salt\n3 eggs...")
        self.ingredients_input.setMinimumHeight(120)
        
        form_layout.addWidget(ingredients_label, row, 0)
        form_layout.addWidget(self.ingredients_input, row, 1, 1, 2)
        row += 1
        
        # Instructions (Required)
        instructions_label = QLabel("Instructions *")
        instructions_label.setObjectName("AddRecipeFieldLabel")
        
        self.instructions_input = QTextEdit()
        self.instructions_input.setObjectName("AddRecipeInstructionsInput")
        self.instructions_input.setPlaceholderText("Step-by-step cooking instructions:\n1. Preheat oven to 350°F\n2. Mix dry ingredients\n3. Add wet ingredients...")
        self.instructions_input.setMinimumHeight(150)
        
        form_layout.addWidget(instructions_label, row, 0)
        form_layout.addWidget(self.instructions_input, row, 1, 1, 2)
        row += 1
        
        # Photo Upload Section
        photo_label = QLabel("Recipe Photo URL")
        photo_label.setObjectName("AddRecipeFieldLabel")

        photo_container = QFrame()
        photo_container.setObjectName("AddRecipePhotoContainer")

        photo_layout = QVBoxLayout(photo_container)
        photo_layout.setContentsMargins(10, 10, 10, 10)
        photo_layout.setSpacing(10)

        # URL input field
        url_input_frame = QFrame()
        url_input_layout = QHBoxLayout(url_input_frame)
        url_input_layout.setContentsMargins(0, 0, 0, 0)
        url_input_layout.setSpacing(8)

        self.image_url_input = QLineEdit()
        self.image_url_input.setObjectName("AddRecipeImageUrlInput")
        self.image_url_input.setPlaceholderText("Enter image URL (e.g., https://example.com/recipe-image.jpg)")
        self.image_url_input.textChanged.connect(self.on_image_url_changed)

        preview_btn = QPushButton("Preview")
        preview_btn.setObjectName("AddRecipePreviewButton")
        preview_btn.clicked.connect(self.preview_image_url)

        url_input_layout.addWidget(self.image_url_input)
        url_input_layout.addWidget(preview_btn)

        # Photo preview
        self.photo_preview = QLabel("No image URL provided")
        self.photo_preview.setObjectName("AddRecipePhotoPreview")
        self.photo_preview.setAlignment(Qt.AlignCenter)
        self.photo_preview.setMinimumHeight(150)
        self.photo_preview.setMaximumHeight(200)
        self.photo_preview.setStyleSheet("border: 2px dashed #ccc; border-radius: 8px;")

        # Photo buttons
        photo_buttons = QFrame()
        photo_buttons_layout = QHBoxLayout(photo_buttons)
        photo_buttons_layout.setContentsMargins(0, 0, 0, 0)
        photo_buttons_layout.setSpacing(10)

        self.clear_image_btn = QPushButton("Clear Image")
        self.clear_image_btn.setObjectName("AddRecipeClearImageButton")
        self.clear_image_btn.clicked.connect(self.clear_image_url)
        self.clear_image_btn.hide()

        photo_buttons_layout.addWidget(self.clear_image_btn)
        photo_buttons_layout.addStretch()

        photo_layout.addWidget(url_input_frame)
        photo_layout.addWidget(self.photo_preview)
        photo_layout.addWidget(photo_buttons)

        form_layout.addWidget(photo_label, row, 0)
        form_layout.addWidget(photo_container, row, 1, 1, 2)
        row += 1
        
        # Tags Section
        self.tags_widget = TagsWidget()
        
        form_layout.addWidget(QLabel(""), row, 0)  # Spacer
        form_layout.addWidget(self.tags_widget, row, 0, 1, 3)
        
        layout.addWidget(form_card)
        
        return form_container
    
    def create_actions_section(self):
        """Create action buttons section"""
        actions_container = QFrame()
        actions_container.setObjectName("AddRecipeActionsContainer")
        
        layout = QHBoxLayout(actions_container)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(15)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("AddRecipeCancelButton")
        cancel_btn.clicked.connect(self.home_requested.emit)
        
        # Create Recipe button
        create_btn = QPushButton("Create Recipe")
        create_btn.setObjectName("AddRecipeCreateButton")
        create_btn.clicked.connect(self.create_recipe)
        
        layout.addStretch()
        layout.addWidget(cancel_btn)
        layout.addWidget(create_btn)
        
        return actions_container
    
    def on_image_url_changed(self):
        """Handle image URL input changes"""
        url = self.image_url_input.text().strip()
        if not url:
            self.clear_image_url()

    def preview_image_url(self):
        """Preview image from URL"""
        url = self.image_url_input.text().strip()
        
        if not url:
            self.show_message("Please enter an image URL", is_error=True)
            return
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            self.show_message("Please enter a valid URL starting with http:// or https://", is_error=True)
            return
        
        # Show loading state
        self.photo_preview.setText("Loading image...")
        self.photo_preview.setStyleSheet("border: 2px dashed #007acc; border-radius: 8px; color: #007acc;")
        
        # Load image using the shared ImageLoader (reuse from recipe details)
        self.load_image_from_url(url)

    def load_image_from_url(self, image_url: str):
        """Load image from URL for preview"""
        try:
            # Import and use the shared ImageLoader
            from views.components.recipe_card import ImageLoader
            from PySide6.QtCore import QThread
            
            # Clean up any existing loader
            self.cleanup_image_loader()
            
            # Create thread and worker for image loading
            self.image_loader_thread = QThread()
            self.image_loader = ImageLoader(image_url, (200, 150))
            
            # Move worker to thread
            self.image_loader.moveToThread(self.image_loader_thread)
            
            # Connect signals
            self.image_loader_thread.started.connect(self.image_loader.load_image)
            self.image_loader.image_loaded.connect(self.on_preview_image_loaded)
            self.image_loader.image_failed.connect(self.on_preview_image_failed)
            
            # Clean up thread when done
            self.image_loader.image_loaded.connect(self.image_loader_thread.quit)
            self.image_loader.image_failed.connect(self.image_loader_thread.quit)
            self.image_loader_thread.finished.connect(self.image_loader.deleteLater)
            self.image_loader_thread.finished.connect(self.image_loader_thread.deleteLater)
            
            # Start loading
            self.image_loader_thread.start()
            
        except Exception as e:
            print(f"Error setting up image preview loading: {e}")
            self.on_preview_image_failed()

    def on_preview_image_loaded(self, pixmap):
        """Handle successful image preview loading"""
        try:
            self.photo_preview.clear()
            self.photo_preview.setStyleSheet("border: 2px solid #28a745; border-radius: 8px;")
            self.photo_preview.setPixmap(pixmap)
            self.photo_preview.setScaledContents(False)
            
            # Show clear button
            self.clear_image_btn.show()
            
            print("Image preview loaded successfully")
        except Exception as e:
            print(f"Error displaying preview image: {e}")
            self.on_preview_image_failed()

    def on_preview_image_failed(self):
        """Handle failed image preview loading"""
        print("Failed to load image preview")
        self.photo_preview.clear()
        self.photo_preview.setText("Failed to load image\nPlease check the URL")
        self.photo_preview.setStyleSheet("border: 2px dashed #dc3545; border-radius: 8px; color: #dc3545;")

    def cleanup_image_loader(self):
        """Clean up image loading thread"""
        try:
            if hasattr(self, 'image_loader_thread') and self.image_loader_thread and self.image_loader_thread.isRunning():
                if hasattr(self, 'image_loader') and self.image_loader:
                    self.image_loader.stop()
                
                self.image_loader_thread.quit()
                
                if not self.image_loader_thread.wait(1000):
                    self.image_loader_thread.terminate()
                    self.image_loader_thread.wait(500)
                
                self.image_loader_thread = None
                self.image_loader = None
        except RuntimeError:
            pass
        except Exception as e:
            print(f"Error during image loader cleanup: {e}")

    def clear_image_url(self):
        """Clear image URL and preview"""
        self.image_url_input.clear()
        self.photo_preview.clear()
        self.photo_preview.setText("No image URL provided")
        self.photo_preview.setStyleSheet("border: 2px dashed #ccc; border-radius: 8px; color: #666;")
        self.clear_image_btn.hide()
        
        # Clean up any loading threads
        self.cleanup_image_loader()
    
    def create_recipe(self):
        """Validate and create recipe"""
        # Validate required fields
        if not self.validate_form():
            return
        
        # Collect recipe data
        recipe_data = {
            'title': self.title_input.text().strip(),
            'description': self.description_input.toPlainText().strip(),
            'servings': self.servings_input.value(),
            'ingredients': self.ingredients_input.toPlainText().strip(),
            'instructions': self.instructions_input.toPlainText().strip(),
            'tags': self.tags_widget.get_tags(),
            'image_url': self.image_url_input.text().strip() or None  # Use URL directly
        }
        
        print(f"Creating recipe: {recipe_data['title']}")
        self.recipe_creation_requested.emit(recipe_data)
    
    def validate_form(self) -> bool:
        """Validate form fields"""
        errors = []
        
        # Required fields
        if not self.title_input.text().strip():
            errors.append("Recipe title is required")
        
        if not self.ingredients_input.toPlainText().strip():
            errors.append("Ingredients are required")
        
        if not self.instructions_input.toPlainText().strip():
            errors.append("Instructions are required")
        
        # Validation rules
        if len(self.title_input.text().strip()) > 100:
            errors.append("Recipe title cannot exceed 100 characters")
        
        if len(self.tags_widget.get_tags()) > 10:
            errors.append("Recipe cannot have more than 10 tags")
        
        if errors:
            error_message = "Please fix the following errors:\n" + "\n".join(f"• {error}" for error in errors)
            self.show_message(error_message, is_error=True)
            return False
        
        return True
    
    def set_available_tags(self, tags: List[str]):
        """Set available tags for the tags widget"""
        self.tags_widget.set_available_tags(tags)
    
    def clear_form(self):
        """Clear all form fields"""
        self.title_input.clear()
        self.description_input.clear()
        self.servings_input.setValue(4)
        self.ingredients_input.clear()
        self.instructions_input.clear()
        self.tags_widget.set_tags([])
        self.clear_image_url()  # Updated method name
    
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
    
    def cleanup(self):
        """Clean up resources"""
        self.cleanup_image_loader()
        print("Add recipe view cleaned up")