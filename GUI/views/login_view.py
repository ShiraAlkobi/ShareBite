
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QStackedWidget, QTextEdit, QCheckBox,
    QGraphicsDropShadowEffect, QSpacerItem, QSizePolicy, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QColor, QPainter, QPainterPath

class RecipeCard(QFrame):
    """Recipe-styled card that looks like a recipe card"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #FFFEF7,
                    stop: 0.05 #FFF8E1,
                    stop: 1 #F5F5DC);
                border: 2px solid #D4AF37;
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(212, 175, 55, 0.3);
            }
        """)
        
        # Add vintage paper effect shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(139, 69, 19, 80))
        shadow.setOffset(5, 8)
        self.setGraphicsEffect(shadow)

class VintageLineEdit(QLineEdit):
    """Vintage recipe book style input"""
    
    def __init__(self, placeholder_text: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder_text)
        self.setFixedHeight(45)
        self.setStyleSheet("""
            QLineEdit {
                background: #FFFFFF;
                border: 2px solid #CD853F;
                border-radius: 10px;
                padding: 0 15px;
                font-size: 15px;
                color: #8B4513;
                font-family: 'Georgia', 'Times New Roman', serif;
                font-weight: 500;
            }
            QLineEdit:focus {
                border: 3px solid #D2691E;
                background: #FFF8DC;
                box-shadow: inset 0 2px 4px rgba(210, 105, 30, 0.2);
            }
            QLineEdit:hover {
                border: 2px solid #D2691E;
                background: #FFFAF0;
            }
            QLineEdit::placeholder {
                color: rgba(139, 69, 19, 0.6);
                font-style: italic;
            }
        """)

class ChefButton(QPushButton):
    """Chef-inspired cooking button"""
    
    def __init__(self, text: str = "", style: str = "primary", parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(50)
        
        if style == "primary":
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #FF6347,
                        stop: 0.5 #FF4500,
                        stop: 1 #DC143C);
                    color: #FFFFFF;
                    border: 3px solid #B22222;
                    border-radius: 12px;
                    font-size: 15px;
                    font-weight: 700;
                    font-family: 'Georgia', serif;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                }
                QPushButton:hover {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #FF7F50,
                        stop: 0.5 #FF6347,
                        stop: 1 #FF4500);
                    border: 3px solid #CD5C5C;
                }
                QPushButton:pressed {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #DC143C,
                        stop: 1 #B22222);
                }
                QPushButton:disabled {
                    background: #D3D3D3;
                    color: #A9A9A9;
                    border: 3px solid #C0C0C0;
                }
            """)
        elif style == "secondary":
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #32CD32,
                        stop: 0.5 #228B22,
                        stop: 1 #006400);
                    color: #FFFFFF;
                    border: 3px solid #006400;
                    border-radius: 12px;
                    font-size: 15px;
                    font-weight: 700;
                    font-family: 'Georgia', serif;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                }
                QPushButton:hover {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #7FFF00,
                        stop: 0.5 #32CD32,
                        stop: 1 #228B22);
                }
            """)
        elif style == "ghost":
            self.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #D2691E;
                    border: 2px solid #D2691E;
                    border-radius: 10px;
                    font-size: 13px;
                    font-weight: 600;
                    font-family: 'Georgia', serif;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background: rgba(210, 105, 30, 0.1);
                    color: #8B4513;
                    border-color: #8B4513;
                }
            """)

class CookingLoginCard(RecipeCard):
    """Recipe-themed login card with fixed structure"""
    
    login_requested = Signal(str, str)
    switch_to_register = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 480)  # Fixed size prevents resizing
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the recipe login card with fixed layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(0)  # Control spacing manually
        
        # Header section - fixed height
        header_container = QWidget()
        header_container.setFixedHeight(70)
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(15, 10, 15, 10)
        header_layout.setSpacing(2)
        
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(255, 165, 0, 0.3),
                    stop: 0.5 rgba(255, 140, 0, 0.2),
                    stop: 1 rgba(255, 165, 0, 0.3));
                border: 2px dashed #D2691E;
                border-radius: 10px;
            }
        """)
        
        title = QLabel("Welcome Back, Chef!")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #8B4513;
                font-size: 18px;
                font-weight: 700;
                font-family: 'Georgia', serif;
                text-shadow: 2px 2px 4px rgba(139, 69, 19, 0.3);
            }
        """)
        
        subtitle = QLabel("Let's cook up something amazing")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                color: #D2691E;
                font-size: 11px;
                font-weight: 500;
                font-family: 'Georgia', serif;
                font-style: italic;
            }
        """)
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_frame.setLayout(header_layout)
        
        header_container_layout = QVBoxLayout(header_container)
        header_container_layout.setContentsMargins(0, 0, 0, 0)
        header_container_layout.addWidget(header_frame)
        
        # Form section - fixed height
        form_container = QWidget()
        form_container.setFixedHeight(300)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 15, 0, 0)
        form_layout.setSpacing(12)
        
        # Section label
        credentials_label = QLabel("Your Kitchen Access:")
        credentials_label.setStyleSheet("""
            QLabel {
                color: #8B4513;
                font-size: 15px;
                font-weight: 600;
                font-family: 'Georgia', serif;
            }
        """)
        
        # Input fields
        self.username_input = VintageLineEdit("Your chef name")
        self.password_input = VintageLineEdit("Secret recipe code")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Remember me
        self.remember_checkbox = QCheckBox("Keep my apron on")
        self.remember_checkbox.setStyleSheet("""
            QCheckBox {
                color: #8B4513;
                font-size: 13px;
                font-family: 'Georgia', serif;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 2px solid #D2691E;
                background: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #FF6347, stop: 1 #D2691E);
                border-color: #8B4513;
            }
            QCheckBox::indicator:hover {
                border-color: #8B4513;
            }
        """)
        
        # Login button
        self.login_button = ChefButton("Start Cooking!", "primary")
        self.login_button.clicked.connect(self.handle_login)
        
        form_layout.addWidget(credentials_label)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.remember_checkbox)
        form_layout.addSpacing(10)
        form_layout.addWidget(self.login_button)
        form_layout.addStretch()
        
        # Bottom section - fixed height
        bottom_container = QWidget()
        bottom_container.setFixedHeight(60)
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setAlignment(Qt.AlignCenter)
        bottom_layout.setSpacing(8)
        
        no_account = QLabel("New to our kitchen?")
        no_account.setStyleSheet("""
            QLabel {
                color: #8B4513;
                font-size: 12px;
                font-family: 'Georgia', serif;
            }
        """)
        
        self.register_link = ChefButton("Get Your Apron", "ghost")
        self.register_link.clicked.connect(self.switch_to_register.emit)
        
        bottom_layout.addWidget(no_account)
        bottom_layout.addWidget(self.register_link)
        
        # Add all containers to main layout
        main_layout.addWidget(header_container)
        main_layout.addWidget(form_container)
        main_layout.addWidget(bottom_container)
    
    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        self.login_requested.emit(username, password)
    
    def clear_form(self):
        self.username_input.clear()
        self.password_input.clear()
        self.remember_checkbox.setChecked(False)
    
    def set_loading(self, loading: bool):
        self.login_button.setEnabled(not loading)
        self.login_button.setText("Cooking..." if loading else "Start Cooking!")

class CookingRegisterCard(RecipeCard):
    """Recipe-themed registration card with fixed structure"""
    
    register_requested = Signal(str, str, str, str, str)
    switch_to_login = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 580)  # Fixed size prevents resizing
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the recipe registration card with fixed layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(0)  # Control spacing manually
        
        # Header section - fixed height
        header_container = QWidget()
        header_container.setFixedHeight(70)
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(15, 10, 15, 10)
        header_layout.setSpacing(2)
        
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(50, 205, 50, 0.3),
                    stop: 0.5 rgba(34, 139, 34, 0.2),
                    stop: 1 rgba(50, 205, 50, 0.3));
                border: 2px dashed #228B22;
                border-radius: 10px;
            }
        """)
        
        title = QLabel("Join Our Kitchen!")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #006400;
                font-size: 18px;
                font-weight: 700;
                font-family: 'Georgia', serif;
                text-shadow: 2px 2px 4px rgba(0, 100, 0, 0.3);
            }
        """)
        
        subtitle = QLabel("Let's create your chef profile")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                color: #228B22;
                font-size: 11px;
                font-weight: 500;
                font-family: 'Georgia', serif;
                font-style: italic;
            }
        """)
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_frame.setLayout(header_layout)
        
        header_container_layout = QVBoxLayout(header_container)
        header_container_layout.setContentsMargins(0, 0, 0, 0)
        header_container_layout.addWidget(header_frame)
        
        # Form section - fixed height
        form_container = QWidget()
        form_container.setFixedHeight(400)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 15, 0, 0)
        form_layout.setSpacing(10)
        
        # Section label
        profile_label = QLabel("Chef Profile Setup:")
        profile_label.setStyleSheet("""
            QLabel {
                color: #006400;
                font-size: 15px;
                font-weight: 600;
                font-family: 'Georgia', serif;
            }
        """)
        
        # Input fields
        self.username_input = VintageLineEdit("Your chef nickname")
        self.email_input = VintageLineEdit("Kitchen contact email")
        self.password_input = VintageLineEdit("Secret pantry code")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input = VintageLineEdit("Confirm pantry code")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Bio area
        self.bio_input = QTextEdit()
        self.bio_input.setPlaceholderText("Tell us about your cooking journey and favorite dishes...")
        self.bio_input.setFixedHeight(60)
        self.bio_input.setStyleSheet("""
            QTextEdit {
                background: #FFFFFF;
                border: 2px solid #CD853F;
                border-radius: 10px;
                padding: 10px;
                font-size: 13px;
                color: #8B4513;
                font-family: 'Georgia', serif;
            }
            QTextEdit:focus {
                border: 3px solid #228B22;
                background: #F0FFF0;
            }
        """)
        
        # Register button
        self.register_button = ChefButton("Join the Kitchen!", "secondary")
        self.register_button.clicked.connect(self.handle_register)
        
        form_layout.addWidget(profile_label)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.confirm_password_input)
        form_layout.addWidget(self.bio_input)
        form_layout.addSpacing(8)
        form_layout.addWidget(self.register_button)
        form_layout.addStretch()
        
        # Bottom section - fixed height
        bottom_container = QWidget()
        bottom_container.setFixedHeight(60)
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setAlignment(Qt.AlignCenter)
        bottom_layout.setSpacing(8)
        
        have_account = QLabel("Already have an apron?")
        have_account.setStyleSheet("""
            QLabel {
                color: #8B4513;
                font-size: 12px;
                font-family: 'Georgia', serif;
            }
        """)
        
        self.login_link = ChefButton("Back to Kitchen", "ghost")
        self.login_link.clicked.connect(self.switch_to_login.emit)
        
        bottom_layout.addWidget(have_account)
        bottom_layout.addWidget(self.login_link)
        
        # Add all containers to main layout
        main_layout.addWidget(header_container)
        main_layout.addWidget(form_container)
        main_layout.addWidget(bottom_container)
    
    def handle_register(self):
        username = self.username_input.text()
        email = self.email_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        bio = self.bio_input.toPlainText()
        self.register_requested.emit(username, email, password, confirm_password, bio)
    
    def clear_form(self):
        self.username_input.clear()
        self.email_input.clear()
        self.password_input.clear()
        self.confirm_password_input.clear()
        self.bio_input.clear()
    
    def set_loading(self, loading: bool):
        self.register_button.setEnabled(not loading)
        self.register_button.setText("Joining Kitchen..." if loading else "Join the Kitchen!")

class KitchenSidebar(QFrame):
    """Kitchen-themed sidebar with fixed structure"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 600)  # Fixed size
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #8B4513,
                    stop: 0.3 #A0522D,
                    stop: 0.7 #CD853F,
                    stop: 1 #D2691E);
                border-right: 4px solid #8B4513;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 30, 25, 30)
        main_layout.setSpacing(0)
        
        # Brand section - fixed height
        brand_container = QWidget()
        brand_container.setFixedHeight(180)
        brand_layout = QVBoxLayout(brand_container)
        brand_layout.setSpacing(8)
        
        # Logo frame
        logo_frame = QFrame()
        logo_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(255, 255, 255, 0.9),
                    stop: 1 rgba(255, 248, 220, 0.9));
                border: 3px solid #8B4513;
                border-radius: 15px;
            }
        """)
        
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(15, 15, 15, 15)
        logo_layout.setSpacing(2)
        
        logo1 = QLabel("Recipe")
        logo1.setAlignment(Qt.AlignCenter)
        logo1.setStyleSheet("""
            QLabel {
                color: #8B4513;
                font-size: 32px;
                font-weight: 800;
                font-family: 'Georgia', serif;
                text-shadow: 3px 3px 6px rgba(139, 69, 19, 0.4);
            }
        """)
        
        logo2 = QLabel("Share")
        logo2.setAlignment(Qt.AlignCenter)
        logo2.setStyleSheet("""
            QLabel {
                color: #D2691E;
                font-size: 32px;
                font-weight: 800;
                font-family: 'Georgia', serif;
                text-shadow: 3px 3px 6px rgba(210, 105, 30, 0.4);
                margin-top: -8px;
            }
        """)
        
        tagline = QLabel("Where Flavors Meet Friends")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setWordWrap(True)
        tagline.setStyleSheet("""
            QLabel {
                color: #654321;
                font-size: 13px;
                font-weight: 500;
                font-family: 'Georgia', serif;
                font-style: italic;
            }
        """)
        
        logo_layout.addWidget(logo1)
        logo_layout.addWidget(logo2)
        logo_layout.addWidget(tagline)
        
        brand_layout.addWidget(logo_frame)
        
        # Features section - fixed height
        features_container = QWidget()
        features_container.setFixedHeight(320)
        features_layout = QVBoxLayout(features_container)
        features_layout.setContentsMargins(0, 20, 0, 0)
        features_layout.setSpacing(12)
        
        features_frame = QFrame()
        features_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.15);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
            }
        """)
        
        features_inner_layout = QVBoxLayout(features_frame)
        features_inner_layout.setContentsMargins(20, 20, 20, 20)
        features_inner_layout.setSpacing(15)
        
        features_title = QLabel("Kitchen Features")
        features_title.setAlignment(Qt.AlignCenter)
        features_title.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 16px;
                font-weight: 700;
                font-family: 'Georgia', serif;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            }
        """)
        
        features = [
            ("Share Recipes", "Upload your family secrets"),
            ("Discover Flavors", "Explore world cuisines"),
            ("Save Favorites", "Build your collection"),
            ("Chef Assistant", "Get AI cooking tips"),
            ("Track Progress", "Monitor your journey")
        ]
        
        features_inner_layout.addWidget(features_title)
        
        for title, desc in features:
            feature_frame = QFrame()
            feature_frame.setFixedHeight(40)
            feature_frame.setStyleSheet("""
                QFrame {
                    background: rgba(255, 99, 71, 0.2);
                    border-left: 4px solid #FF6347;
                    border-radius: 6px;
                }
                QFrame:hover {
                    background: rgba(255, 99, 71, 0.3);
                    border-left: 4px solid #FF4500;
                }
            """)
            
            feature_layout = QVBoxLayout(feature_frame)
            feature_layout.setContentsMargins(10, 6, 10, 6)
            feature_layout.setSpacing(2)
            
            feature_title = QLabel(title)
            feature_title.setStyleSheet("""
                QLabel {
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: 700;
                    font-family: 'Georgia', serif;
                }
            """)
            
            feature_desc = QLabel(desc)
            feature_desc.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 0.9);
                    font-size: 10px;
                    font-weight: 400;
                    font-family: 'Georgia', serif;
                }
            """)
            
            feature_layout.addWidget(feature_title)
            feature_layout.addWidget(feature_desc)
            
            features_inner_layout.addWidget(feature_frame)
        
        features_layout.addWidget(features_frame)
        
        # Add containers to main layout
        main_layout.addWidget(brand_container)
        main_layout.addWidget(features_container)
        main_layout.addStretch()

class LoginView(QWidget):
    """
    Recipe-themed login interface with fixed component structure
    Prevents resizing issues by using fixed sizes throughout
    """
    
    login_requested = Signal(str, str)
    register_requested = Signal(str, str, str, str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the cooking-themed main UI with fixed structure"""
        self.setWindowTitle("Recipe Share - Your Culinary Journey Starts Here")
        self.setFixedSize(800, 600)  # Fixed window size
        
        # Warm kitchen gradient background
        self.setStyleSheet("""
            QWidget {
                background: qradialgradient(cx: 0.3, cy: 0.3, radius: 1.2,
                    stop: 0 #FFF8DC,
                    stop: 0.4 #FFFACD,
                    stop: 0.8 #F5DEB3,
                    stop: 1 #DEB887);
            }
        """)
        
        # Main horizontal layout with fixed structure
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Kitchen sidebar - fixed width
        self.sidebar = KitchenSidebar()
        main_layout.addWidget(self.sidebar)
        
        # Content area - fixed width
        content_container = QWidget()
        content_container.setFixedSize(500, 600)
        content_layout = QVBoxLayout(content_container)
        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.setContentsMargins(50, 50, 50, 50)
        content_layout.setSpacing(20)
        
        # Stacked widget for recipe cards
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setFixedSize(400, 580)  # Fixed size for cards
        
        # Login recipe card
        self.login_card = CookingLoginCard()
        self.stacked_widget.addWidget(self.login_card)
        
        # Register recipe card
        self.register_card = CookingRegisterCard()
        self.stacked_widget.addWidget(self.register_card)
        
        # Message display with fixed positioning
        self.message_label = QLabel()
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.setFixedHeight(30)
        self.message_label.hide()
        
        content_layout.addWidget(self.stacked_widget)
        content_layout.addWidget(self.message_label)
        
        main_layout.addWidget(content_container)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.login_card.switch_to_register.connect(self.show_register_form)
        self.register_card.switch_to_login.connect(self.show_login_form)
        
        self.login_card.login_requested.connect(self.login_requested.emit)
        self.register_card.register_requested.connect(self.register_requested.emit)
    
    def show_login_form(self):
        """Switch to login form"""
        self.stacked_widget.setCurrentWidget(self.login_card)
        self.register_card.clear_form()
        self.hide_message()
    
    def show_register_form(self):
        """Switch to register form"""
        self.stacked_widget.setCurrentWidget(self.register_card)
        self.login_card.clear_form()
        self.hide_message()
    
    def show_message(self, message: str, is_error: bool = True):
        """Show recipe note styled messages"""
        self.message_label.setText(message)
        
        if is_error:
            self.message_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #FFE4E1,
                        stop: 1 #FFC0CB);
                    color: #8B0000;
                    font-size: 12px;
                    font-weight: 600;
                    font-family: 'Georgia', serif;
                    padding: 8px 15px;
                    border: 2px solid #DC143C;
                    border-radius: 8px;
                    border-left: 4px solid #B22222;
                }
            """)
        else:
            self.message_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #F0FFF0,
                        stop: 1 #E6FFE6);
                    color: #006400;
                    font-size: 12px;
                    font-weight: 600;
                    font-family: 'Georgia', serif;
                    padding: 8px 15px;
                    border: 2px solid #32CD32;
                    border-radius: 8px;
                    border-left: 4px solid #228B22;
                }
            """)
        
        self.message_label.show()
    
    def hide_message(self):
        """Hide message label"""
        self.message_label.hide()
    
    def set_loading(self, loading: bool):
        """Set loading state for current form"""
        current_widget = self.stacked_widget.currentWidget()
        if current_widget:
            current_widget.set_loading(loading)