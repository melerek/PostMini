"""
Design System Module

This module defines the complete design system for the API Client application,
including colors, typography, spacing, and other design tokens.
Based on modern design principles and Material Design guidelines.
"""


class DesignSystem:
    """
    Centralized design system with all design tokens.
    All visual styling should reference these values.
    """
    
    # ==================== COLOR PALETTE ====================
    
    # Primary Colors (Blue - for main actions)
    PRIMARY = '#2196F3'
    PRIMARY_DARK = '#1976D2'
    PRIMARY_LIGHT = '#BBDEFB'
    PRIMARY_HOVER = '#1E88E5'
    PRIMARY_PRESSED = '#1565C0'
    
    # Secondary Colors (Green - for success/send actions)
    SECONDARY = '#4CAF50'
    SECONDARY_DARK = '#388E3C'
    SECONDARY_LIGHT = '#C8E6C9'
    SECONDARY_HOVER = '#43A047'
    SECONDARY_PRESSED = '#2E7D32'
    
    # Accent Colors (Orange - for warnings/loading)
    ACCENT = '#FF9800'
    ACCENT_DARK = '#F57C00'
    ACCENT_LIGHT = '#FFE0B2'
    ACCENT_HOVER = '#FB8C00'
    ACCENT_PRESSED = '#EF6C00'
    
    # Semantic Colors
    SUCCESS = '#4CAF50'
    SUCCESS_BG = '#E8F5E9'
    WARNING = '#FF9800'
    WARNING_BG = '#FFF3E0'
    ERROR = '#F44336'
    ERROR_BG = '#FFEBEE'
    INFO = '#2196F3'
    INFO_BG = '#E3F2FD'
    
    # HTTP Status Colors
    STATUS_2XX = '#4CAF50'  # Success (green)
    STATUS_3XX = '#2196F3'  # Redirect (blue)
    STATUS_4XX = '#FF9800'  # Client Error (orange)
    STATUS_5XX = '#F44336'  # Server Error (red)
    
    # Neutral Colors (Grays)
    BACKGROUND = '#FAFAFA'        # Main app background
    SURFACE = '#FFFFFF'           # Cards, panels
    SURFACE_HOVER = '#F5F5F5'     # Hover state for surfaces
    SURFACE_SELECTED = '#E3F2FD'  # Selected items
    
    BORDER = '#E0E0E0'            # Default borders
    BORDER_DARK = '#BDBDBD'       # Emphasized borders
    BORDER_LIGHT = '#F5F5F5'      # Subtle borders
    
    DIVIDER = '#EEEEEE'           # Divider lines
    
    # Text Colors
    TEXT_PRIMARY = '#212121'      # Main text
    TEXT_SECONDARY = '#757575'    # Secondary text
    TEXT_TERTIARY = '#9E9E9E'     # Tertiary text, hints
    TEXT_DISABLED = '#BDBDBD'     # Disabled text
    TEXT_ON_PRIMARY = '#FFFFFF'   # Text on primary color
    TEXT_ON_SECONDARY = '#FFFFFF' # Text on secondary color
    
    # ==================== SPACING SYSTEM ====================
    # 8px base grid system
    
    SPACING_XS = 4    # Extra small spacing
    SPACING_SM = 8    # Small spacing (default)
    SPACING_MD = 16   # Medium spacing (section separation)
    SPACING_LG = 24   # Large spacing (panel spacing)
    SPACING_XL = 32   # Extra large spacing
    SPACING_XXL = 48  # Major divisions
    
    # Common padding values
    PADDING_TIGHT = 8
    PADDING_NORMAL = 16
    PADDING_COMFORTABLE = 24
    
    # ==================== TYPOGRAPHY ====================
    
    # Font Family
    FONT_FAMILY = 'Segoe UI, -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif'
    FONT_FAMILY_MONO = 'Consolas, Monaco, "Courier New", monospace'
    
    # Font Sizes
    FONT_SIZE_H1 = 24
    FONT_SIZE_H2 = 18
    FONT_SIZE_H3 = 16
    FONT_SIZE_BODY = 14
    FONT_SIZE_SMALL = 12
    FONT_SIZE_TINY = 11
    
    # Font Weights
    FONT_WEIGHT_NORMAL = 'normal'
    FONT_WEIGHT_MEDIUM = '500'
    FONT_WEIGHT_BOLD = 'bold'
    
    # Line Heights
    LINE_HEIGHT_TIGHT = 1.2
    LINE_HEIGHT_NORMAL = 1.5
    LINE_HEIGHT_RELAXED = 1.7
    
    # ==================== BORDER RADIUS ====================
    
    RADIUS_SM = 4     # Small radius (buttons, inputs)
    RADIUS_MD = 6     # Medium radius (cards)
    RADIUS_LG = 8     # Large radius (panels)
    RADIUS_XL = 12    # Extra large radius
    RADIUS_ROUND = 999  # Fully rounded (pills)
    
    # ==================== SHADOWS ====================
    
    SHADOW_SM = '0 1px 3px rgba(0, 0, 0, 0.12)'
    SHADOW_MD = '0 2px 6px rgba(0, 0, 0, 0.15)'
    SHADOW_LG = '0 4px 12px rgba(0, 0, 0, 0.18)'
    SHADOW_FOCUS = f'0 0 0 3px {PRIMARY_LIGHT}'
    
    # ==================== TRANSITIONS ====================
    
    TRANSITION_FAST = '150ms'
    TRANSITION_NORMAL = '250ms'
    TRANSITION_SLOW = '350ms'
    
    # ==================== Z-INDEX ====================
    
    Z_DROPDOWN = 1000
    Z_MODAL = 2000
    Z_TOOLTIP = 3000
    Z_NOTIFICATION = 4000
    
    # ==================== WIDGET SPECIFIC ====================
    
    # Input fields
    INPUT_HEIGHT = 38
    INPUT_PADDING = '10px 12px'
    INPUT_BORDER_WIDTH = 2
    
    # Buttons
    BUTTON_HEIGHT = 36
    BUTTON_PADDING = '8px 16px'
    BUTTON_BORDER_RADIUS = RADIUS_SM
    
    # Table
    TABLE_ROW_HEIGHT = 36
    TABLE_CELL_PADDING = '8px 12px'
    TABLE_HEADER_HEIGHT = 40
    
    # Tree
    TREE_ITEM_HEIGHT = 32
    TREE_ITEM_PADDING = 8
    TREE_INDENT = 20
    
    # Tabs
    TAB_HEIGHT = 40
    TAB_PADDING = '10px 20px'
    
    # ==================== HELPER METHODS ====================
    
    @classmethod
    def spacing(cls, multiplier: int = 1) -> int:
        """Get spacing value based on 8px grid."""
        return cls.SPACING_SM * multiplier
    
    @classmethod
    def get_button_style(cls, variant: str = 'primary') -> dict:
        """Get button style configuration."""
        styles = {
            'primary': {
                'bg': cls.SECONDARY,
                'bg_hover': cls.SECONDARY_HOVER,
                'bg_pressed': cls.SECONDARY_PRESSED,
                'text': cls.TEXT_ON_SECONDARY,
            },
            'secondary': {
                'bg': cls.PRIMARY,
                'bg_hover': cls.PRIMARY_HOVER,
                'bg_pressed': cls.PRIMARY_PRESSED,
                'text': cls.TEXT_ON_PRIMARY,
            },
            'danger': {
                'bg': cls.ERROR,
                'bg_hover': '#E53935',
                'bg_pressed': '#C62828',
                'text': '#FFFFFF',
            },
            'ghost': {
                'bg': 'transparent',
                'bg_hover': cls.SURFACE_HOVER,
                'bg_pressed': cls.BORDER_LIGHT,
                'text': cls.TEXT_PRIMARY,
            },
        }
        return styles.get(variant, styles['primary'])
    
    @classmethod
    def get_status_color(cls, status_code: int) -> str:
        """Get color for HTTP status code."""
        if 200 <= status_code < 300:
            return cls.STATUS_2XX
        elif 300 <= status_code < 400:
            return cls.STATUS_3XX
        elif 400 <= status_code < 500:
            return cls.STATUS_4XX
        elif 500 <= status_code < 600:
            return cls.STATUS_5XX
        return cls.TEXT_TERTIARY


# Create a singleton instance for easy access
ds = DesignSystem()

