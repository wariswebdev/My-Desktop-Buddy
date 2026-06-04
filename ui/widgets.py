from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtCore import Qt, QRect, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui import QPainter, QColor

class ToggleSwitch(QCheckBox):
    """A custom QCheckBox styled as a mobile-like toggle switch."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._position = 18
        self.animation = QPropertyAnimation(self, b"position")
        self.animation.setDuration(150)
        self.stateChanged.connect(self.setup_animation)
        self.setChecked(True) # ON by default as requested

    @pyqtProperty(int)
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos
        self.update()

    def setup_animation(self, value):
        self.animation.stop()
        if value:
            self.animation.setEndValue(18)
        else:
            self.animation.setEndValue(0)
        self.animation.start()

    def hitButton(self, pos):
        return self.contentsRect().contains(pos)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background pill
        p.setPen(Qt.PenStyle.NoPen)
        if self.isChecked():
            p.setBrush(QColor("#89b4fa")) # Muted blue accent
        else:
            p.setBrush(QColor("#45475a")) # Deep gray off state
            
        rect = QRect(0, 0, self.width(), self.height())
        p.drawRoundedRect(rect, 11, 11)
        
        # Draw thumb
        p.setBrush(QColor("#ffffff"))
        thumb_rect = QRect(self._position + 2, 2, 18, 18)
        p.drawEllipse(thumb_rect)
