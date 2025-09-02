from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QStackedWidget, QTextEdit, QCheckBox,
    QScrollArea, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor

class LoginCard(QFrame):
    """Login card with modern structure matching home page design"""
    
    login_requested = Signal(str, str)
    switch_to_register = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LoginCard")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup modern login card structure"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header section with modern styling
        header_section = self.create_header_section()
        main_layout.addWidget(header_section)
        
        # Form content section
        content_section = self.create_content_section()
        main_layout.addWidget(content_section)
        
        # Footer section
        footer_section = self.create_footer_section()
        main_layout.addWidget(footer_section)
    
    def create_header_section(self):
        """Create bold modern header section"""
        header = QFrame()
        header.setObjectName("LoginCardHeader")
        header.setFixedHeight(65)
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("Welcome Back!")
        title.setObjectName("LoginCardTitle")
        title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("Ready to cook up something amazing?")
        subtitle.setObjectName("LoginCardSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        return header
    
    def create_content_section(self):
        """Create modern content section"""
        content = QFrame()
        content.setObjectName("LoginCardContent")
        
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # Input fields container
        inputs_container = QFrame()
        inputs_container.setObjectName("LoginInputsContainer")
        
        inputs_layout = QVBoxLayout(inputs_container)
        inputs_layout.setContentsMargins(0, 0, 0, 0)
        inputs_layout.setSpacing(10)
        
        # Username field
        username_container = self.create_input_field(
            "Username", "Enter your username", False
        )
        self.username_input = username_container.findChild(QLineEdit)
        
        # Password field  
        password_container = self.create_input_field(
            "Password", "Enter your password", True
        )
        self.password_input = password_container.findChild(QLineEdit)
        
        inputs_layout.addWidget(username_container)
        inputs_layout.addWidget(password_container)
        
        # Options container
        options_container = QFrame()
        options_container.setObjectName("LoginOptionsContainer")
        
        options_layout = QHBoxLayout(options_container)
        options_layout.setContentsMargins(0, 0, 0, 0)
        
        self.remember_checkbox = QCheckBox("Remember me")
        self.remember_checkbox.setObjectName("LoginRememberCheckbox")
        
        forgot_link = QLabel("Forgot password?")
        forgot_link.setObjectName("LoginForgotLink")
        forgot_link.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        options_layout.addWidget(self.remember_checkbox)
        options_layout.addStretch()
        options_layout.addWidget(forgot_link)
        
        # Login button
        self.login_button = QPushButton("Sign In")
        self.login_button.setObjectName("LoginSubmitButton")
        self.login_button.clicked.connect(self.handle_login)
        
        layout.addWidget(inputs_container)
        layout.addWidget(options_container)
        layout.addWidget(self.login_button)
        
        return content
    
    def create_footer_section(self):
        """Create modern footer section"""
        footer = QFrame()
        footer.setObjectName("LoginCardFooter")
        footer.setFixedHeight(65)
        
        layout = QVBoxLayout(footer)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)
        
        # Divider
        divider = QFrame()
        divider.setObjectName("LoginDivider")
        divider.setFixedHeight(1)
        
        # Switch to register
        switch_container = QHBoxLayout()
        switch_container.setAlignment(Qt.AlignCenter)
        switch_container.setSpacing(8)
        
        switch_text = QLabel("Don't have an account?")
        switch_text.setObjectName("LoginSwitchText")
        
        self.register_link = QPushButton("Sign Up")
        self.register_link.setObjectName("LoginSwitchButton")
        self.register_link.clicked.connect(self.switch_to_register.emit)
        
        switch_container.addWidget(switch_text)
        switch_container.addWidget(self.register_link)
        
        layout.addWidget(divider)
        layout.addLayout(switch_container)
        
        return footer
    
    def create_input_field(self, label_text, placeholder, is_password=False):
        """Create modern input field with label"""
        container = QFrame()
        container.setObjectName("InputFieldContainer")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        label = QLabel(label_text)
        label.setObjectName("InputFieldLabel")
        
        input_field = QLineEdit()
        input_field.setObjectName("LoginFormInput")
        input_field.setPlaceholderText(placeholder)
        
        if is_password:
            input_field.setEchoMode(QLineEdit.EchoMode.Password)
        
        layout.addWidget(label)
        layout.addWidget(input_field)
        
        return container
    
    def handle_login(self):
        """Handle login button click"""
        username = self.username_input.text()
        password = self.password_input.text()
        self.login_requested.emit(username, password)
    
    def clear_form(self):
        """Clear all form fields"""
        self.username_input.clear()
        self.password_input.clear()
        self.remember_checkbox.setChecked(False)
    
    def set_loading(self, loading: bool):
        """Set loading state"""
        self.login_button.setEnabled(not loading)
        self.login_button.setText("Signing in..." if loading else "Sign In")

class RegisterCard(QFrame):
    """Registration card with modern structure matching home page design"""
    
    register_requested = Signal(str, str, str, str, str)
    switch_to_login = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RegisterCard")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup modern register card structure"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(3)
        
        # Header section
        header_section = self.create_header_section()
        main_layout.addWidget(header_section)
        
        # Form content section
        content_section = self.create_content_section()
        main_layout.addWidget(content_section)
        
        # Footer section
        footer_section = self.create_footer_section()
        main_layout.addWidget(footer_section)
    
    def create_header_section(self):
        """Create bold modern header section"""
        header = QFrame()
        header.setObjectName("RegisterCardHeader")
        header.setFixedHeight(65)
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("Join ShareBite")
        title.setObjectName("RegisterCardTitle")
        title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("Start your culinary adventure today!")
        subtitle.setObjectName("RegisterCardSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        return header
    
    def create_content_section(self):
        """Create modern content section with compact spacing"""
        content = QFrame()
        content.setObjectName("RegisterCardContent")
        
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)  # Reduced spacing
        
        # Input fields container
        inputs_container = QFrame()
        inputs_container.setObjectName("RegisterInputsContainer")
        
        inputs_layout = QVBoxLayout(inputs_container)
        inputs_layout.setContentsMargins(0, 0, 0, 0)
        inputs_layout.setSpacing(6)  # Reduced spacing between fields
        
        # Username field
        username_container = self.create_input_field(
            "Username", "Choose a username"
        )
        self.username_input = username_container.findChild(QLineEdit)
        
        # Email field
        email_container = self.create_input_field(
            "Email", "Enter your email address"
        )
        self.email_input = email_container.findChild(QLineEdit)
        
        # Password field
        password_container = self.create_input_field(
            "Password", "Create password", True
        )
        self.password_input = password_container.findChild(QLineEdit)
        
        # Confirm Password field
        confirm_container = self.create_input_field(
            "Confirm Password", "Confirm password", True
        )
        self.confirm_password_input = confirm_container.findChild(QLineEdit)
        
        # Bio field - more compact
        bio_container = QFrame()
        bio_container.setObjectName("InputFieldContainer")
        
        bio_layout = QVBoxLayout(bio_container)
        bio_layout.setContentsMargins(0, 0, 0, 0)
        bio_layout.setSpacing(3)  # Reduced spacing
        
        bio_label = QLabel("About You (Optional)")
        bio_label.setObjectName("InputFieldLabel")
        
        self.bio_input = QTextEdit()
        self.bio_input.setObjectName("RegisterBioInput")
        self.bio_input.setPlaceholderText("Tell us about your cooking journey...")
        
        bio_layout.addWidget(bio_label)
        bio_layout.addWidget(self.bio_input)
        
        # Register button
        self.register_button = QPushButton("Create Account")
        self.register_button.setObjectName("RegisterSubmitButton")
        self.register_button.clicked.connect(self.handle_register)
        
        inputs_layout.addWidget(username_container)
        inputs_layout.addWidget(email_container)
        inputs_layout.addWidget(password_container)
        inputs_layout.addWidget(confirm_container)
        inputs_layout.addWidget(bio_container)
        
        layout.addWidget(inputs_container)
        layout.addWidget(self.register_button)
        
        return content
    
    def create_footer_section(self):
        """Create modern footer section"""
        footer = QFrame()
        footer.setObjectName("RegisterCardFooter")
        footer.setFixedHeight(65)
        
        layout = QVBoxLayout(footer)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)
        
        # Divider
        divider = QFrame()
        divider.setObjectName("RegisterDivider")
        divider.setFixedHeight(1)
        
        # Switch to login
        switch_container = QHBoxLayout()
        switch_container.setAlignment(Qt.AlignCenter)
        switch_container.setSpacing(8)
        
        switch_text = QLabel("Already have an account?")
        switch_text.setObjectName("RegisterSwitchText")
        
        self.login_link = QPushButton("Sign In")
        self.login_link.setObjectName("RegisterSwitchButton")
        self.login_link.clicked.connect(self.switch_to_login.emit)
        
        switch_container.addWidget(switch_text)
        switch_container.addWidget(self.login_link)
        
        layout.addWidget(divider)
        layout.addLayout(switch_container)
        
        return footer
    
    def create_input_field(self, label_text, placeholder, is_password=False):
        """Create modern input field with label and compact spacing"""
        container = QFrame()
        container.setObjectName("InputFieldContainer")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)  # Reduced spacing between label and input
        
        label = QLabel(label_text)
        label.setObjectName("InputFieldLabel")
        
        input_field = QLineEdit()
        input_field.setObjectName("RegisterFormInput")
        input_field.setPlaceholderText(placeholder)
        
        if is_password:
            input_field.setEchoMode(QLineEdit.EchoMode.Password)
        
        layout.addWidget(label)
        layout.addWidget(input_field)
        
        return container
    
    def handle_register(self):
        """Handle registration button click"""
        username = self.username_input.text()
        email = self.email_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        bio = self.bio_input.toPlainText()
        self.register_requested.emit(username, email, password, confirm_password, bio)
    
    def clear_form(self):
        """Clear all form fields"""
        self.username_input.clear()
        self.email_input.clear()
        self.password_input.clear()
        self.confirm_password_input.clear()
        self.bio_input.clear()
    
    def set_loading(self, loading: bool):
        """Set loading state"""
        self.register_button.setEnabled(not loading)
        self.register_button.setText("Creating account..." if loading else "Create Account")

class LoginSidebar(QFrame):
    """Compact login sidebar with features only"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LoginLeftSection")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup compact sidebar UI with features only"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 20, 15, 20)
        main_layout.setSpacing(15)
        
        # Features section only
        features_container = QFrame()
        features_container.setObjectName("LoginFeaturesContainer")
        
        features_layout = QVBoxLayout(features_container)
        features_layout.setContentsMargins(15, 15, 15, 15)
        features_layout.setSpacing(8)
        
        features_title = QLabel("Why Join Us?")
        features_title.setObjectName("LoginFeaturesTitle")
        features_title.setAlignment(Qt.AlignCenter)
        
        features = [
            ("🚀", "Quick Share", "Upload recipes instantly"),
            ("🌍", "Global Community", "Connect with food lovers worldwide"),
            ("🔍", "Smart Discovery", "Find recipes you'll love"),
            ("❤️", "Save & Organize", "Build your digital cookbook")
        ]
        
        features_list = QFrame()
        features_list.setObjectName("LoginFeaturesList")
        
        features_list_layout = QVBoxLayout(features_list)
        features_list_layout.setSpacing(6)
        
        for icon, title, description in features:
            feature_item = self.create_compact_feature_item(icon, title, description)
            features_list_layout.addWidget(feature_item)
        
        features_layout.addWidget(features_title)
        features_layout.addWidget(features_list)
        
        main_layout.addWidget(features_container)
        main_layout.addStretch()
    
    def create_compact_feature_item(self, icon, title, description):
        """Create compact feature item with icon, title and description"""
        item = QFrame()
        item.setObjectName("LoginFeatureItem")
        
        layout = QHBoxLayout(item)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignLeft)
        
        # Icon container
        icon_container = QFrame()
        icon_container.setObjectName("LoginFeatureIconContainer")
        
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setAlignment(Qt.AlignCenter)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel(icon)
        icon_label.setObjectName("LoginFeatureIcon")
        icon_label.setAlignment(Qt.AlignCenter)
        
        icon_layout.addWidget(icon_label)
        
        # Content container
        content_container = QFrame()
        content_container.setObjectName("LoginFeatureContent")
        
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setObjectName("LoginFeatureTitle")
        
        desc_label = QLabel(description)
        desc_label.setObjectName("LoginFeatureDesc")
        desc_label.setWordWrap(True)
        
        content_layout.addWidget(title_label)
        content_layout.addWidget(desc_label)
        
        layout.addWidget(icon_container)
        layout.addWidget(content_container, 1)
        
        return item

class LoginView(QWidget):
    """Main login interface with scroll support"""
    
    login_requested = Signal(str, str)
    register_requested = Signal(str, str, str, str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LoginView")
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup main login UI with scroll support and welcome header"""
        self.setWindowTitle("ShareBite - Sign In")
        # Set reasonable window size
        self.setMinimumSize(700, 500)
        self.setMaximumSize(800, 650)
        self.resize(750, 580)
        
        # Main layout for the window
        window_layout = QVBoxLayout(self)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.setSpacing(0)
        
        # Welcome header section (moved from sidebar)
        self.setup_welcome_header(window_layout)
        
        # Create scroll area for content below header
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Create scrollable content widget
        content_widget = QWidget()
        content_widget.setObjectName("LoginContentWidget")
        
        # Content layout
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Left sidebar (now smaller)
        self.sidebar = LoginSidebar()
        content_layout.addWidget(self.sidebar)
        
        # Right section - auth forms
        right_section = self.create_right_section()
        content_layout.addWidget(right_section)
        
        # Set the content widget to scroll area
        scroll_area.setWidget(content_widget)
        window_layout.addWidget(scroll_area)
        
        # Loading indicator
        self.setup_loading_indicator()
    
    def setup_welcome_header(self, main_layout):
        """Setup welcome header section like in home view"""
        header = QFrame()
        header.setObjectName("LoginWelcomeHeader")
        header.setFixedHeight(80)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        header_layout.setSpacing(15)
        
        # Welcome container
        welcome_container = QFrame()
        welcome_container.setObjectName("LoginWelcomeContainer")
        
        welcome_layout = QHBoxLayout(welcome_container)
        welcome_layout.setSpacing(12)
        
        # App icon/emoji
        welcome_icon = QLabel("🍴")
        welcome_icon.setObjectName("LoginWelcomeIcon")
        
        # App brand
        brand_label = QLabel("ShareBite")
        brand_label.setObjectName("LoginWelcomeBrand")
        
        # Welcome tagline
        tagline_label = QLabel("Where culinary creativity meets community")
        tagline_label.setObjectName("LoginWelcomeTagline")
        
        welcome_layout.addWidget(welcome_icon)
        welcome_layout.addWidget(brand_label)
        welcome_layout.addWidget(tagline_label)
        welcome_layout.addStretch()
        
        header_layout.addWidget(welcome_container)
        
        main_layout.addWidget(header)
    
    def create_right_section(self):
        """Create right authentication section"""
        right = QFrame()
        right.setObjectName("LoginRightSection")
        
        layout = QVBoxLayout(right)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignCenter)
        
        # Auth cards container
        cards_container = QFrame()
        cards_container.setObjectName("LoginCardsContainer")
        
        cards_layout = QVBoxLayout(cards_container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(0)
        
        # Stacked widget for forms
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("LoginStackedWidget")
        
        # Create and add cards
        self.login_card = LoginCard()
        self.register_card = RegisterCard()
        
        self.stacked_widget.addWidget(self.login_card)
        self.stacked_widget.addWidget(self.register_card)
        
        cards_layout.addWidget(self.stacked_widget)
        
        # Message label
        self.message_label = QLabel()
        self.message_label.setObjectName("LoginMessageLabel")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.hide()
        
        layout.addWidget(cards_container)
        layout.addWidget(self.message_label)
        
        return right
    
    def setup_loading_indicator(self):
        """Setup loading indicator"""
        self.loading_indicator = QFrame(self)
        self.loading_indicator.setObjectName("LoginLoadingIndicator")
        
        layout = QVBoxLayout(self.loading_indicator)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        
        loading_icon = QLabel("Loading...")
        loading_icon.setObjectName("LoginLoadingIcon")
        loading_icon.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(loading_icon)
        self.loading_indicator.hide()
    
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
        
        current_widget = self.stacked_widget.currentWidget()
        if current_widget:
            current_widget.set_loading(loading)