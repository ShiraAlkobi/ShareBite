# Create a new file: components/recipe_card.py

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtGui import QPixmap
import requests
from io import BytesIO

class ImageLoader(QObject):
    """Worker class for loading images asynchronously"""
    image_loaded = Signal(QPixmap)
    image_failed = Signal()
    
    def __init__(self, image_url: str, size: tuple = (140, 140)):
        super().__init__()
        self.image_url = image_url
        self.target_size = size
        self.should_stop = False
    
    def stop(self):
        """Stop the image loading operation"""
        self.should_stop = True
    
    def load_image(self):
        """Load image from URL with stop checks"""
        if self.should_stop:
            return
            
        try:
            response = requests.get(self.image_url, timeout=10, stream=True)
            if response.status_code == 200:
                if self.should_stop:
                    return
                    
                image_data = BytesIO()
                for chunk in response.iter_content(chunk_size=8192):
                    if self.should_stop:
                        return
                    image_data.write(chunk)
                image_data.seek(0)
                
                pixmap = QPixmap()
                if pixmap.loadFromData(image_data.getvalue()):
                    if not self.should_stop:
                        scaled_pixmap = pixmap.scaled(
                            self.target_size[0], 
                            self.target_size[1], 
                            Qt.KeepAspectRatio, 
                            Qt.SmoothTransformation
                        )
                        self.image_loaded.emit(scaled_pixmap)
                        return
            
            if not self.should_stop:
                self.image_failed.emit()
                
        except Exception as e:
            if not self.should_stop:
                print(f"Error loading image from {self.image_url}: {e}")
                self.image_failed.emit()

class BaseRecipeCard(QFrame):
    """Base recipe card with shared image loading functionality"""
    
    # Signals - subclasses should connect these
    recipe_clicked = Signal(int)  # recipe_id
    recipe_liked = Signal(int)    # recipe_id
    recipe_favorited = Signal(int)  # recipe_id (optional)
    
    def __init__(self, recipe_data, card_size=(280, 320), image_size=(140, 140), parent=None):
        super().__init__(parent)
        self.recipe = recipe_data
        self.card_size = card_size
        self.image_size = image_size
        self.image_loader_thread = None
        self.image_loader = None
        
        # Set card size
        self.setFixedSize(*card_size)
        
        # Setup UI - call in subclass after setting specific object name
        
    def setup_image_container(self, image_height=None):
        """Setup image container with loading capability"""
        if image_height is None:
            image_height = self.image_size[1]
            
        # Image container
        image_container = QFrame()
        image_container.setObjectName("RecipeImageContainer")
        image_container.setFixedHeight(image_height)
        print(f"DEBUG: Created image container with object name: {image_container.objectName()}")
        self.apply_image_container_style()
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setAlignment(Qt.AlignCenter)


        
        # Image label
        self.image_label = QLabel()
        self.image_label.setObjectName("RecipeImage")  # Use original name for CSS compatibility
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(*self.image_size)
        self.image_label.setScaledContents(False)

        print(f"DEBUG: Created image label with object name: {self.image_label.objectName()}")
        
        # Load image if available
        if hasattr(self.recipe, 'image_url') and self.recipe.image_url and self.recipe.image_url.strip():
            self.load_recipe_image()
        else:
            self.show_placeholder_image()
        
        image_layout.addWidget(self.image_label)
        return image_container
    
    def load_recipe_image(self):
        """Load recipe image from URL asynchronously"""
        try:
            # Show loading placeholder
            self.image_label.setText("🔄")
            self.image_label.setStyleSheet("font-size: 24px; color: #666;")
            
            # Create thread and worker for image loading
            self.image_loader_thread = QThread()
            self.image_loader = ImageLoader(self.recipe.image_url, self.image_size)
            
            # Move worker to thread
            self.image_loader.moveToThread(self.image_loader_thread)
            
            # Connect signals
            self.image_loader_thread.started.connect(self.image_loader.load_image)
            self.image_loader.image_loaded.connect(self.on_image_loaded)
            self.image_loader.image_failed.connect(self.on_image_failed)
            
            # Clean up thread when done
            self.image_loader.image_loaded.connect(self.image_loader_thread.quit)
            self.image_loader.image_failed.connect(self.image_loader_thread.quit)
            self.image_loader_thread.finished.connect(self.image_loader.deleteLater)
            self.image_loader_thread.finished.connect(self.image_loader_thread.deleteLater)
            
            # Start loading
            self.image_loader_thread.start()
            
        except Exception as e:
            print(f"Error setting up image loading: {e}")
            self.show_placeholder_image()

    def apply_image_container_style(self):
        """Apply image container styling directly"""
        if hasattr(self, 'image_container'):
            self.image_container.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                    border-radius: 12px;
                }
            """)

    def on_image_loaded(self, pixmap: QPixmap):
        """Handle successful image loading"""
        try:
            self.image_label.clear()
            self.image_label.setStyleSheet("")
            self.image_label.setPixmap(pixmap)
            print(f"Successfully loaded image for recipe: {getattr(self.recipe, 'title', 'Unknown')}")
        except Exception as e:
            print(f"Error displaying loaded image: {e}")
            self.show_placeholder_image()
    
    def on_image_failed(self):
        """Handle failed image loading"""
        print(f"Failed to load image for recipe: {getattr(self.recipe, 'title', 'Unknown')}")
        self.show_placeholder_image()
    
    def show_placeholder_image(self):
        """Show placeholder when no image is available or loading failed"""
        self.image_label.clear()
        self.image_label.setText("🍽️")
        self.image_label.setStyleSheet("""
            font-size: 48px;
            color: #888;
            background-color: #f5f5f5;
            border: 1px solid #ddd;
            border-radius: 8px;
        """)
    
    def update_like_status(self, is_liked: bool, likes_count: int = None):
        """Update like button status - to be implemented by subclasses"""
        pass
    
    def update_favorite_status(self, is_favorited: bool):
        """Update favorite button status - to be implemented by subclasses"""
        pass
    
    def cleanup(self):
        """Clean up resources when card is destroyed"""
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
            print(f"Error during BaseRecipeCard cleanup: {e}")

class HomeRecipeCard(BaseRecipeCard):
    """Recipe card for home view - maintains existing functionality"""
    
    def __init__(self, recipe_data, parent=None):
        super().__init__(recipe_data, card_size=(280, 320), image_size=(140, 140), parent=parent)
        self.setObjectName("RecipeCard")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup home recipe card UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Image container
        image_container = self.setup_image_container(140)
        
        # Content container
        content_container = QFrame()
        content_container.setObjectName("RecipeContent")
        
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(16, 12, 16, 12)
        content_layout.setSpacing(8)
        
        # Recipe title
        self.title_label = QLabel(self.recipe.title)
        self.title_label.setObjectName("RecipeTitle")
        self.title_label.setWordWrap(True)
        
        # Recipe metadata
        meta_container = QFrame()
        meta_container.setObjectName("RecipeMetadata")
        meta_layout = QVBoxLayout(meta_container)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        meta_layout.setSpacing(2)
        
        author_label = QLabel(f"by Chef {self.recipe.author_name}")
        author_label.setObjectName("RecipeAuthor")
        
        date_label = QLabel(f"Created: {self.recipe.created_at or 'Date unknown'}")
        date_label.setObjectName("RecipeDate")
        
        meta_layout.addWidget(author_label)
        meta_layout.addWidget(date_label)
        
        # Actions container
        actions_container = QFrame()
        actions_container.setObjectName("RecipeActions")
        
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(6)
        
        # Buttons
        self.like_button = QPushButton(f"♥ {self.recipe.likes_count}")
        self.like_button.setObjectName("LikeButton")
        self.like_button.setProperty("liked", str(self.recipe.is_liked).lower())
        self.like_button.clicked.connect(lambda: self.recipe_liked.emit(self.recipe.recipe_id))
        
        self.favorite_button = QPushButton("★" if self.recipe.is_favorited else "☆")
        self.favorite_button.setObjectName("FavoriteButton")
        self.favorite_button.setProperty("favorited", str(self.recipe.is_favorited).lower())
        self.favorite_button.clicked.connect(lambda: self.recipe_favorited.emit(self.recipe.recipe_id))
        
        view_button = QPushButton("View")
        view_button.setObjectName("ViewRecipeButton")
        view_button.clicked.connect(lambda: self.recipe_clicked.emit(self.recipe.recipe_id))
        
        actions_layout.addWidget(self.like_button)
        actions_layout.addWidget(self.favorite_button)
        actions_layout.addStretch()
        actions_layout.addWidget(view_button)
        
        # Add to main layout
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

class ProfileRecipeCard(BaseRecipeCard):
    """Recipe card for profile view - adapted to existing profile design"""
    
    def __init__(self, recipe_data, parent=None):
        super().__init__(recipe_data, card_size=(280, 300), image_size=(120, 120), parent=parent)
        self.setObjectName("ProfileRecipeCard")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup profile recipe card UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Image container
        image_container = self.setup_image_container(120)
        
        # Content container
        content_container = QFrame()
        content_container.setObjectName("ProfileRecipeContent")
        
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(8)
        
        # Title
        title_label = QLabel(self.recipe.title)
        title_label.setObjectName("ProfileRecipeTitle")
        title_label.setWordWrap(True)
        
        # Description
        description = getattr(self.recipe, 'description', '')
        desc_text = description[:100] + "..." if len(description) > 100 else description
        desc_label = QLabel(desc_text)
        desc_label.setObjectName("ProfileRecipeDescription")
        desc_label.setWordWrap(True)
        
        # Stats and actions
        stats_container = QFrame()
        stats_container.setObjectName("ProfileRecipeStats")
        
        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(8)
        
        # Like button
        self.like_button = QPushButton(f"❤️ {getattr(self.recipe, 'likes_count', 0)}")
        self.like_button.setObjectName("ProfileRecipeLikeButton")
        self.like_button.clicked.connect(lambda: self.recipe_liked.emit(self.recipe.recipe_id))
        
        # Update like button style based on status
        self.update_like_status(getattr(self.recipe, 'is_liked', False))
        
        # View button
        view_button = QPushButton("View Recipe")
        view_button.setObjectName("ProfileRecipeViewButton")
        view_button.clicked.connect(lambda: self.recipe_clicked.emit(self.recipe.recipe_id))
        
        stats_layout.addWidget(self.like_button)
        stats_layout.addStretch()
        stats_layout.addWidget(view_button)
        
        content_layout.addWidget(title_label)
        content_layout.addWidget(desc_label)
        content_layout.addWidget(stats_container)
        
        layout.addWidget(image_container)
        layout.addWidget(content_container)
    
    def update_like_status(self, is_liked: bool, likes_count: int = None):
        """Update like button based on status"""
        self.recipe.is_liked = is_liked
        
        # Update likes count if provided
        if likes_count is not None:
            self.recipe.likes_count = likes_count
            self.like_button.setText(f"❤️ {likes_count}")
        
        # Update button properties
        self.like_button.setProperty("liked", str(is_liked).lower())
        
        # Force style refresh
        self.like_button.style().unpolish(self.like_button)
        self.like_button.style().polish(self.like_button)