import sys
import logging
from PyQt6.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QSizePolicy,
    QComboBox,
)
from PyQt6.QtCore import (
    Qt,
    QTimer,
    QSize,
    QPropertyAnimation,
    QEasingCurve,
    QRect,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QBrush, QIcon
# from pynput import keyboard # Removed, no longer needed
from rivavoice import constants  # Import constants

logger = logging.getLogger(constants.APP_NAME)  # Use constant


class PulsingOrb(QWidget):
    def __init__(self, parent=None, size=100):
        super().__init__(parent)

        # Set minimum size
        self.setMinimumSize(size, size)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Initialize properties
        self.recording = False
        self.pulse_size = 0
        self.pulse_opacity = 0.5

        # Setup animation
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.update_pulse)
        self.pulse_timer.start(30)  # Update every 30ms

        # Animation parameters
        self.pulse_direction = 1
        self.pulse_speed = 0.03

    def update_pulse(self):
        # Update pulse size
        self.pulse_size += self.pulse_direction * self.pulse_speed

        # Reverse direction at limits
        if self.pulse_size > 1:
            self.pulse_direction = -1
        elif self.pulse_size < 0:
            self.pulse_direction = 1

        # Keep pulse_size in valid range
        self.pulse_size = max(0, min(1, self.pulse_size))

        # Force repaint
        self.update()

    def set_recording(self, recording):
        self.recording = recording
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate center and radius
        center_x = self.width() / 2
        center_y = self.height() / 2
        base_radius = min(center_x, center_y) * 0.7

        # Pulse effect - outer circle
        pulse_radius = base_radius * (1 + self.pulse_size * 0.3)

        # Draw pulse effect
        pulse_color = (
            QColor(239, 68, 68, int(120 * (1 - self.pulse_size)))
            if self.recording
            else QColor(59, 130, 246, int(80 * (1 - self.pulse_size)))
        )
        painter.setBrush(QBrush(pulse_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            int(center_x - pulse_radius),
            int(center_y - pulse_radius),
            int(pulse_radius * 2),
            int(pulse_radius * 2),
        )

        # Draw main orb
        main_color = QColor(239, 68, 68) if self.recording else QColor(59, 130, 246)
        painter.setBrush(QBrush(main_color))
        painter.drawEllipse(
            int(center_x - base_radius),
            int(center_y - base_radius),
            int(base_radius * 2),
            int(base_radius * 2),
        )

        # Draw highlight (to make it look more 3D)
        highlight_path = QPainterPath()
        highlight_radius = base_radius * 0.8
        highlight_offset = -base_radius * 0.2

        highlight_path.addEllipse(
            center_x - highlight_radius + highlight_offset,
            center_y - highlight_radius + highlight_offset,
            highlight_radius * 2,
            highlight_radius * 2,
        )

        highlight_color = QColor(255, 255, 255, 40)
        painter.setBrush(QBrush(highlight_color))
        painter.drawPath(highlight_path)


class CardContainer(QWidget):
    """A rounded rectangle container with shadow for a card-like appearance"""

    def __init__(self, parent=None, width=458, height=572, corner_radius=16):
        super().__init__(parent)

        self.setFixedSize(width, height)
        self.corner_radius = corner_radius
        self.accent_color = QColor("#4E3FCA")  # Purple accent color
        self.drag_position = None

        # Set solid background (remove translucency)
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(
            """
            background-color: white;
            border-radius: 16px;
        """
        )

        # Set shadow effect
        self.setGraphicsEffect(self._create_shadow_effect())

    def _create_shadow_effect(self):
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        return shadow

    def mousePressEvent(self, event):
        """Make window draggable"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Get main window (go up two levels: layout -> central widget -> main window)
            main_window = self.window()
            self.drag_position = (
                event.globalPosition().toPoint() - main_window.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse drag"""
        if (
            event.buttons() == Qt.MouseButton.LeftButton
            and self.drag_position is not None
        ):
            main_window = self.window()
            main_window.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Reset drag state"""
        self.drag_position = None
        event.accept()

    def paintEvent(self, event):
        # Create a custom paint event to ensure the widget has rounded corners
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Create rounded rectangle path
        path = QPainterPath()
        path.addRoundedRect(
            0, 0, self.width(), self.height(), self.corner_radius, self.corner_radius
        )

        # Clip painting to the rounded rectangle
        painter.setClipPath(path)

        # Call the parent class's paint event with the clipped painter
        super().paintEvent(event)


class StyledButton(QPushButton):
    """Custom styled button with hover effects"""

    def __init__(self, text="", parent=None, accent_color=None, is_text_button=False):
        super().__init__(text, parent)

        self.accent_color = accent_color or QColor("#4E3FCA")
        self.is_text_button = is_text_button

        if is_text_button:
            # Text-only button style
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.accent_color.name()};
                    border: none;
                    padding: 8px 16px;
                    font-weight: bold;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: rgba(78, 63, 202, 0.1);
                }}
                QPushButton:pressed {{
                    background-color: rgba(78, 63, 202, 0.2);
                }}
            """
            )
        else:
            # Filled button style
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {self.accent_color.name()};
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #3E32A3;
                }}
                QPushButton:pressed {{
                    background-color: #352C8C;
                }}
            """
            )


class IconButton(QPushButton):
    """Button with just an icon and hover effect"""

    def __init__(self, icon_name, parent=None, color=None, size=24):
        super().__init__(parent)

        self.color = color or QColor("#4E3FCA")

        # Create icon
        # Note: You would need to have the actual icons available
        # This is simplified for demonstration
        self.setIcon(QIcon(icon_name))
        self.setIconSize(QSize(size, size))

        # Set fixed size to make it square
        self.setFixedSize(size + 12, size + 12)

        # Set style
        self.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 16px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """
        )


class StyledLineEdit(QLineEdit):
    """Line edit with custom styling"""

    def __init__(self, parent=None, placeholder="", is_password=False):
        super().__init__(parent)

        self.setPlaceholderText(placeholder)
        if is_password:
            self.setEchoMode(QLineEdit.EchoMode.Password)

        # Set style
        self.setStyleSheet(
            """
            QLineEdit {
                padding: 8px; /* Reduced padding (approx 0.5rem) */
                border: 1px solid #d1d5db; /* Match target */
                border-radius: 4px; /* Match target */
                background-color: white; /* Match target */
                font-size: 14px; /* Approx 0.875rem */
            }
            QLineEdit:focus {
                border: 1px solid #6366f1; /* Match target focus */
                /* Native outline might be sufficient, removing custom one */
            }
        """
        )


class ToggleSwitch(QWidget):
    """Custom toggle switch widget"""

    # Define the signal properly
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None, initial_state=False):
        super().__init__(parent)

        # Set fixed size
        self.setFixedSize(50, 26)

        # Initialize state
        self.is_checked = initial_state

        # Always initialize position based on state
        self._toggle_position = 1.0 if initial_state else 0.0

        # Animation for smooth toggle
        self.animation = QPropertyAnimation(self, b"toggle_position")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def toggle_position(self):
        # Ensure a default is returned even if not set
        if not hasattr(self, "_toggle_position") or self._toggle_position is None:
            self._toggle_position = 1.0 if self.is_checked else 0.0
        return self._toggle_position

    def set_toggle_position(self, pos):
        self._toggle_position = pos
        self.update()

    # Define property for animation
    toggle_position = pyqtProperty(float, toggle_position, set_toggle_position)

    def toggle(self):
        self.is_checked = not self.is_checked
        target = 1.0 if self.is_checked else 0.0

        self.animation.setStartValue(self._toggle_position)
        self.animation.setEndValue(target)
        self.animation.start()

        # Emit signal when toggled
        # This is what was missing - we need proper signals
        self.toggled.emit(self.is_checked)

    def mousePressEvent(self, event):
        self.toggle()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Define colors
        if self.is_checked:
            track_color = QColor("#4E3FCA")
        else:
            track_color = QColor("#D1D5DB")

        thumb_color = QColor(255, 255, 255)

        # Draw track (background)
        track_height = 20
        track_rect = QRect(
            0, (self.height() - track_height) // 2, self.width(), track_height
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(track_rect, 10, 10)

        # Calculate thumb position
        thumb_size = 24
        thumb_x = int(self._toggle_position * (self.width() - thumb_size))
        thumb_y = (self.height() - thumb_size) // 2

        # Add shadow effect
        shadow = QColor(0, 0, 0, 30)
        shadow_rect = QRect(thumb_x + 1, thumb_y + 2, thumb_size, thumb_size)
        painter.setBrush(shadow)
        painter.drawEllipse(shadow_rect)

        # Draw thumb
        painter.setBrush(thumb_color)
        painter.drawEllipse(thumb_x, thumb_y, thumb_size, thumb_size)


# Predefined safe keybinds that won't interfere with typing or system shortcuts
SAFE_KEYBINDS = [
    {"name": "FN Key", "key": "fn", "code": "179", "display": "FN"},  # Keep FN as is
    {"name": "F1", "key": "f1", "display": "F1"},
    {"name": "F2", "key": "f2", "display": "F2"},
    {"name": "F3", "key": "f3", "display": "F3"},
    {"name": "F4", "key": "f4", "display": "F4"},
    # Update F5 to include scan code
    {"name": "F5", "key": "f5", "code": "59", "display": "F5"},
    {"name": "F6", "key": "f6", "display": "F6"},
    {"name": "F7", "key": "f7", "display": "F7"},
    {"name": "F8", "key": "f8", "display": "F8"},
    {"name": "F9", "key": "f9", "display": "F9"},
    {"name": "F10", "key": "f10", "display": "F10"},
    {"name": "F11", "key": "f11", "display": "F11"},
    {"name": "F12", "key": "f12", "display": "F12"},
    # Add Right Option (assuming 'alt_r' is the key string and 'code' is used for scan code)
    {"name": "Right Option", "key": "alt_r", "code": "61", "display": "Right Option"},
    {"name": "Home", "key": "home", "display": "Home"},
    {"name": "End", "key": "end", "display": "End"},
    {"name": "Page Up", "key": "page_up", "display": "Page Up"},
    {"name": "Page Down", "key": "page_down", "display": "Page Down"},
]


class KeybindSelector(QWidget):
    """Component for selecting keyboard shortcuts with info display"""

    keybind_changed = pyqtSignal(str)

    def __init__(self, parent=None, initial_keybind="fn"):
        super().__init__(parent)
        self.initial_keybind = initial_keybind
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Keybind dropdown
        self.keybind_dropdown = QComboBox()
        # Simplified style based on .form-select
        self.keybind_dropdown.setStyleSheet(
            """
            QComboBox {
                padding: 8px; /* Approx 0.5rem */
                border: 1px solid #d1d5db;
                border-radius: 4px;
                background-color: white;
                font-size: 14px; /* Approx 0.875rem */
                min-width: 120px;
            }
            QComboBox::drop-down {
                /* Use native arrow */
                border: none;
                width: 15px;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #d1d5db;
                background-color: white;
                selection-background-color: #e0e7ff;
                selection-color: #1f2937; /* Added for readable selected text */
            }
            QComboBox:focus {
                 border: 1px solid #6366f1; /* Match target focus */
            }
        """
        )

        # Add keybind options
        for keybind in SAFE_KEYBINDS:
            self.keybind_dropdown.addItem(keybind["name"], keybind["key"])

        # FN Key info (shown only when FN is selected)
        self.fn_key_info = QLabel(
            "Note: To use the FN key on macOS, you may need to disable its special function "
            "in System Settings > Keyboard > Keyboard Shortcuts > Function Keys."
        )
        self.fn_key_info.setWordWrap(True)
        self.fn_key_info.setStyleSheet(
            """
            font-size: 12px;
            color: #6B7280;
            background-color: transparent;
            padding: 10px;
            border-radius: 6px;
            border: 1px solid #E5E7EB;
            margin-top: 4px;
        """
        )
        self.fn_key_info.setVisible(
            False
        )  # Hidden by default, shown based on selection

        layout.addWidget(self.keybind_dropdown)
        layout.addWidget(self.fn_key_info)

        # Connect signals
        self.keybind_dropdown.currentIndexChanged.connect(self.update_keybind_info)
        self.keybind_dropdown.currentIndexChanged.connect(self.emit_keybind_changed)

        # Set initial value
        self.set_keybind(self.initial_keybind)

    def set_keybind(self, keybind):
        """Set the current keybind selection"""
        for i in range(self.keybind_dropdown.count()):
            if self.keybind_dropdown.itemData(i) == keybind:
                self.keybind_dropdown.setCurrentIndex(i)
                break

    def get_keybind(self):
        """Get the currently selected keybind"""
        return self.keybind_dropdown.currentData()

    def update_keybind_info(self):
        """Update keybind info based on selection"""
        current_key = self.keybind_dropdown.currentData()
        self.fn_key_info.setVisible(current_key == "fn" and sys.platform == "darwin")

    def emit_keybind_changed(self):
        """Emit the keybind_changed signal with the current keybind"""
        self.keybind_changed.emit(self.keybind_dropdown.currentData())


# For demonstration purposes - to be imported as needed
if __name__ == "__main__":
    # Simple test code for the components
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Create a test window
    container = CardContainer()
    layout = QVBoxLayout(container)

    # Add some components
    orb = PulsingOrb(container)
    layout.addWidget(orb, alignment=Qt.AlignmentFlag.AlignCenter)

    button = StyledButton("Test Button", container)
    layout.addWidget(button)

    container.show()

    sys.exit(app.exec())
