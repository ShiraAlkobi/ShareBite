from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, 
    QScrollArea, QGridLayout, QSpacerItem, QSizePolicy, QButtonGroup
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap
from models.login_model import UserData
from models.graphs_model import AnalyticsData, TagAnalyticsData, RecipePopularityData
from typing import List, Optional

# Matplotlib imports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as mpatches

class GraphsView(QWidget):
    """
    Analytics view displaying charts and statistics using matplotlib
    """
    
    # Signals for communication with Presenter
    home_requested = Signal()
    logout_requested = Signal()
    refresh_requested = Signal()
    view_mode_changed = Signal(str)  # "user" or "global"
    recipe_selected = Signal(int)  # recipe_id
    
    def __init__(self, user_data: UserData, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.current_analytics: Optional[AnalyticsData] = None
        self.current_mode = "user"  # "user" or "global"
        
        self.setObjectName("GraphsView")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup main analytics UI"""
        self.setWindowTitle(f"Analytics - {self.user_data.username}")
        self.setMinimumSize(1000, 700)
        
        # Create scroll area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create scrollable content widget
        content_widget = QWidget()
        content_widget.setObjectName("GraphsContentWidget")
        
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
        
        # View mode selection
        mode_section = self.create_mode_selection_section()
        content_layout.addWidget(mode_section)
        
        # Statistics overview
        self.stats_section = self.create_stats_section()
        content_layout.addWidget(self.stats_section)
        
        # Charts container
        self.charts_container = self.create_charts_container()
        content_layout.addWidget(self.charts_container)
        
        # Message label for status updates
        self.message_label = QLabel()
        self.message_label.setObjectName("GraphsMessageLabel")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        header.setObjectName("GraphsHeaderSection")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # Brand/Logo
        brand_container = QFrame()
        brand_container.setObjectName("GraphsBrandContainer")
        
        brand_layout = QHBoxLayout(brand_container)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(10)
        
        logo_label = QLabel("ShareBite")
        logo_label.setObjectName("GraphsBrandLogo")
        
        tagline_label = QLabel("Recipe Analytics")
        tagline_label.setObjectName("GraphsBrandTagline")
        
        brand_layout.addWidget(logo_label)
        brand_layout.addWidget(tagline_label)
        brand_layout.addStretch()
        
        # Navigation buttons
        nav_container = QFrame()
        nav_container.setObjectName("GraphsNavContainer")
        
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(10)
        
        home_button = QPushButton("Home")
        home_button.setObjectName("GraphsNavButton")
        home_button.clicked.connect(self.home_requested.emit)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("GraphsNavButton")
        refresh_button.clicked.connect(self.refresh_requested.emit)
        
        logout_button = QPushButton("Logout")
        logout_button.setObjectName("GraphsLogoutButton")
        logout_button.clicked.connect(self.logout_requested.emit)
        
        nav_layout.addWidget(home_button)
        nav_layout.addWidget(refresh_button)
        nav_layout.addWidget(logout_button)
        
        layout.addWidget(brand_container)
        layout.addWidget(nav_container)
        
        return header
    
    def create_mode_selection_section(self):
        """Create view mode selection section"""
        mode_section = QFrame()
        mode_section.setObjectName("GraphsModeSection")
        
        layout = QHBoxLayout(mode_section)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)
        
        # Mode selection label
        mode_label = QLabel("View Mode:")
        mode_label.setObjectName("GraphsModeLabel")
        
        # Button group for exclusive selection
        self.mode_button_group = QButtonGroup(self)
        

        
        # Global mode button
        self.global_mode_button = QPushButton("Global Analytics")
        self.global_mode_button.setObjectName("GraphsModeButton")
        self.global_mode_button.setCheckable(True)
        self.global_mode_button.clicked.connect(lambda: self.view_mode_changed.emit("global"))
        self.mode_button_group.addButton(self.global_mode_button)
        
        layout.addWidget(mode_label)
        layout.addWidget(self.global_mode_button)
        layout.addStretch()
        
        return mode_section
    
    def create_stats_section(self):
        """Create statistics overview section"""
        stats_section = QFrame()
        stats_section.setObjectName("GraphsStatsSection")
        
        layout = QHBoxLayout(stats_section)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(20)
        
        # Total recipes stat
        self.total_recipes_container = self.create_stat_container("📊", "0", "Total Recipes")
        layout.addWidget(self.total_recipes_container)
        
        # Total tags stat
        self.total_tags_container = self.create_stat_container("🏷️", "0", "Different Tags")
        layout.addWidget(self.total_tags_container)
        
        # Top tag stat
        self.top_tag_container = self.create_stat_container("⭐", "N/A", "Most Popular Tag")
        layout.addWidget(self.top_tag_container)
        
        # Most liked recipe stat
        self.most_liked_container = self.create_stat_container("❤️", "N/A", "Most Liked Recipe")
        layout.addWidget(self.most_liked_container)
        
        return stats_section
    
    def create_stat_container(self, icon: str, value: str, label: str):
        """Create individual stat container"""
        container = QFrame()
        container.setObjectName("GraphsStatContainer")
        
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setObjectName("GraphsStatIcon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Value
        value_label = QLabel(value)
        value_label.setObjectName("GraphsStatValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Label
        text_label = QLabel(label)
        text_label.setObjectName("GraphsStatLabel")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setWordWrap(True)
        
        layout.addWidget(icon_label)
        layout.addWidget(value_label)
        layout.addWidget(text_label)
        
        # Store references for updating
        container.value_label = value_label
        container.text_label = text_label
        
        return container
    
    def create_charts_container(self):
        """Create container for matplotlib charts"""
        charts_container = QFrame()
        charts_container.setObjectName("GraphsChartsContainer")
        
        layout = QVBoxLayout(charts_container)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(20)
        
        # Charts grid
        charts_grid = QGridLayout()
        charts_grid.setSpacing(20)
        
        # Tag distribution pie chart
        self.pie_chart_container = self.create_chart_container("Recipe Distribution by Tags")
        charts_grid.addWidget(self.pie_chart_container, 0, 0)
        
        # Recipe popularity bar chart
        self.bar_chart_container = self.create_chart_container("Most Popular Recipes by Likes")
        charts_grid.addWidget(self.bar_chart_container, 0, 1)
        
        layout.addLayout(charts_grid)
        
        return charts_container
    
    def create_chart_container(self, title: str):
        """Create individual chart container with matplotlib canvas"""
        container = QFrame()
        container.setObjectName("GraphsChartContainer")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Chart title
        title_label = QLabel(title)
        title_label.setObjectName("GraphsChartTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create matplotlib figure and canvas
        figure = Figure(figsize=(6, 4), dpi=100, facecolor='none')
        canvas = FigureCanvas(figure)
        canvas.setMinimumSize(400, 300)
        
        # Create placeholder plot
        ax = figure.add_subplot(111)
        ax.text(0.5, 0.5, 'Loading chart...', ha='center', va='center', transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        layout.addWidget(title_label)
        layout.addWidget(canvas)
        
        # Store references
        container.title_label = title_label
        container.figure = figure
        container.canvas = canvas
        
        return container
    
    def update_analytics_display(self, analytics: AnalyticsData, mode: str):
        """Update the display with new analytics data"""
        self.current_analytics = analytics
        self.current_mode = mode
        
        print(f"Updating analytics display for {mode} mode")
        
        # Update statistics
        self.update_statistics(analytics, mode)
        
        # Update charts
        self.update_pie_chart(analytics.tag_distribution)
        self.update_bar_chart(analytics.popular_recipes)
    
    def update_statistics(self, analytics: AnalyticsData, mode: str):
        """Update statistics display"""
        # Update total recipes
        if hasattr(self.total_recipes_container, 'value_label'):
            self.total_recipes_container.value_label.setText(str(analytics.total_recipes))
        
        # Update total tags
        if hasattr(self.total_tags_container, 'value_label'):
            self.total_tags_container.value_label.setText(str(analytics.total_tags))
        
        # Update most popular tag
        if hasattr(self.top_tag_container, 'value_label'):
            if analytics.tag_distribution:
                top_tag = analytics.tag_distribution[0]
                self.top_tag_container.value_label.setText(f"{top_tag.tag_name} ({top_tag.percentage}%)")
            else:
                self.top_tag_container.value_label.setText("N/A")
        
        # Update most liked recipe
        if hasattr(self.most_liked_container, 'value_label'):
            if analytics.popular_recipes:
                most_liked = analytics.popular_recipes[0]
                recipe_text = f"{most_liked.title} ({most_liked.likes_count} likes)"
                # Truncate if too long
                if len(recipe_text) > 20:
                    recipe_text = recipe_text[:17] + "..."
                self.most_liked_container.value_label.setText(recipe_text)
            else:
                self.most_liked_container.value_label.setText("N/A")
        
        # Update mode-specific labels
        if mode == "user":
            if hasattr(self.total_recipes_container, 'text_label'):
                self.total_recipes_container.text_label.setText("My Recipes")
            if hasattr(self.total_tags_container, 'text_label'):
                self.total_tags_container.text_label.setText("My Tags Used")
            if hasattr(self.top_tag_container, 'text_label'):
                self.top_tag_container.text_label.setText("My Top Tag")
            if hasattr(self.most_liked_container, 'text_label'):
                self.most_liked_container.text_label.setText("My Most Liked")
        else:
            if hasattr(self.total_recipes_container, 'text_label'):
                self.total_recipes_container.text_label.setText("Total Recipes")
            if hasattr(self.total_tags_container, 'text_label'):
                self.total_tags_container.text_label.setText("Total Tags")
            if hasattr(self.top_tag_container, 'text_label'):
                self.top_tag_container.text_label.setText("Top Tag Platform")
            if hasattr(self.most_liked_container, 'text_label'):
                self.most_liked_container.text_label.setText("Most Liked Recipe")
    
    def update_pie_chart(self, tag_data: List[TagAnalyticsData]):
        """Update pie chart with tag distribution data using matplotlib"""
        if not tag_data:
            # Show empty state
            figure = self.pie_chart_container.figure
            figure.clear()
            ax = figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No tag data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)
            self.pie_chart_container.canvas.draw()
            return
        
        # Prepare data
        labels = [tag.tag_name for tag in tag_data]
        sizes = [tag.percentage for tag in tag_data]
        
        # Color palette
        colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe', 
                  '#43e97b', '#38f9d7', '#ffecd2', '#fcb69f', '#a8edea', '#fed6e3']
        
        # Create pie chart
        figure = self.pie_chart_container.figure
        figure.clear()
        ax = figure.add_subplot(111)
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors[:len(labels)], 
                                          autopct='%1.1f%%', startangle=90)
        
        # Style the text
        for text in texts:
            text.set_fontsize(8)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(8)
        
        ax.set_title('Recipe Distribution by Tags', fontsize=12, fontweight='bold', pad=20)
        figure.tight_layout()
        self.pie_chart_container.canvas.draw()
        
        print(f"Updated pie chart with {len(tag_data)} tag categories")
    
    def update_bar_chart(self, recipe_data: List[RecipePopularityData]):
        """Update bar chart with recipe popularity data using matplotlib"""
        if not recipe_data:
            # Show empty state
            figure = self.bar_chart_container.figure
            figure.clear()
            ax = figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No recipe data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)
            self.bar_chart_container.canvas.draw()
            return
        
        # Prepare data
        recipe_titles = [recipe.title[:15] + '...' if len(recipe.title) > 15 else recipe.title 
                        for recipe in recipe_data]
        likes_counts = [recipe.likes_count for recipe in recipe_data]
        
        # Create bar chart
        figure = self.bar_chart_container.figure
        figure.clear()
        ax = figure.add_subplot(111)
        
        # Create gradient colors
        bars = ax.bar(range(len(recipe_titles)), likes_counts, 
                     color=['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe'] * 2)
        
        # Customize chart
        ax.set_xlabel('Recipes', fontweight='bold')
        ax.set_ylabel('Likes Count', fontweight='bold')
        ax.set_title('Most Popular Recipes by Likes', fontsize=12, fontweight='bold', pad=20)
        ax.set_xticks(range(len(recipe_titles)))
        ax.set_xticklabels(recipe_titles, rotation=45, ha='right', fontsize=8)
        
        # Add value labels on bars
        for bar, count in zip(bars, likes_counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(count)}', ha='center', va='bottom', fontweight='bold')
        
        # Style the plot
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.3, axis='y')
        
        figure.tight_layout()
        self.bar_chart_container.canvas.draw()
        
        print(f"Updated bar chart with {len(recipe_data)} recipes")
    
    def setup_loading_indicator(self):
        """Setup loading indicator"""
        self.loading_indicator = QFrame(self)
        self.loading_indicator.setObjectName("GraphsLoadingIndicator")
        
        layout = QVBoxLayout(self.loading_indicator)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        
        loading_label = QLabel("Loading analytics...")
        loading_label.setObjectName("GraphsLoadingLabel")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(loading_label)
        self.loading_indicator.hide()
    
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
            
            # Center loading indicator
            parent_rect = self.rect()
            indicator_rect = self.loading_indicator.rect()
            x = (parent_rect.width() - indicator_rect.width()) // 2
            y = (parent_rect.height() - indicator_rect.height()) // 2
            self.loading_indicator.move(x, y)
        else:
            self.loading_indicator.hide()
    
    def cleanup(self):
        """Clean up resources"""
        print("Graphs view cleaned up")
    
    def resizeEvent(self, event):
        """Handle window resize to position loading overlay"""
        super().resizeEvent(event)
        if hasattr(self, 'loading_indicator') and self.loading_indicator.isVisible():
            # Center loading indicator
            parent_rect = self.rect()
            indicator_rect = self.loading_indicator.rect()
            x = (parent_rect.width() - indicator_rect.width()) // 2
            y = (parent_rect.height() - indicator_rect.height()) // 2
            self.loading_indicator.move(x, y)