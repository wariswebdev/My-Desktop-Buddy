from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QScreen
from PyQt6.QtGui import QGuiApplication

class LiveCorrectionAlert(QWidget):
    """
    Frameless, always-on-top window positioned in the bottom right corner.
    Displays live webcam feedback to help the user correct their posture.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Frameless and Always on Top
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        # UI Setup
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        self.setStyleSheet("background-color: #1e1e2e; border: 2px solid #f38ba8; border-radius: 8px;")
        
        self.title_label = QLabel("Fix Your Posture")
        self.title_label.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 14px; border: none;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title_label)
        
        self.image_label = QLabel()
        self.image_label.setStyleSheet("border: none;")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.image_label)
        
        # Dimensions
        self.resize(320, 260)
        self._position_bottom_right()

    def _position_bottom_right(self):
        """Position window cleanly in the bottom right corner of the primary screen."""
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        # Calculate x and y for bottom-right corner with a small margin
        margin = 20
        x = screen_geometry.width() - self.width() - margin
        y = screen_geometry.height() - self.height() - margin
        
        self.move(x, y)

    def update_frame(self, q_image):
        """Update the label with the latest QImage."""
        pixmap = QPixmap.fromImage(q_image)
        # Scale to fit nicely
        pixmap = pixmap.scaled(300, 225, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(pixmap)
