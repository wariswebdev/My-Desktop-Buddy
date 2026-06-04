from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal

class SettingsView(QWidget):
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        title = QLabel("Detection Settings")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #cdd6f4;")
        layout.addWidget(title)

        self.slouch_container, self.slouch_slider = self._create_slider("Slouching Limit", 5, 30, 15, "%")
        layout.addWidget(self.slouch_container)
        
        self.prox_container, self.prox_slider = self._create_slider("Proximity Limit", 5, 30, 15, "%")
        layout.addWidget(self.prox_container)

        self.yawn_container, self.yawn_slider = self._create_slider("Yawn Confirmation", 5, 30, 10, " frames")
        layout.addWidget(self.yawn_container)

        layout.addStretch()

    def _create_slider(self, name, min_val, max_val, default_val, suffix):
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        label = QLabel(name)
        label.setStyleSheet("color: #a6adc8; font-size: 16px;")
        
        val_label = QLabel(f"{default_val}{suffix}")
        val_label.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 16px;")
        
        header.addWidget(label)
        header.addStretch()
        header.addWidget(val_label)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default_val)
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #313244;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #89b4fa;
                width: 16px;
                height: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
        """)
        
        slider.valueChanged.connect(lambda v: val_label.setText(f"{v}{suffix}"))
        slider.valueChanged.connect(self._on_changed)

        vbox.addLayout(header)
        vbox.addWidget(slider)
        
        return container, slider

    def _on_changed(self):
        settings = {
            'slouch_limit': self.slouch_slider.value() / 100.0,
            'proximity_limit': 1.0 + (self.prox_slider.value() / 100.0),
            'yawn_frames': self.yawn_slider.value()
        }
        self.settings_changed.emit(settings)

    def load_settings(self, settings):
        """Update sliders if settings are loaded from config.json"""
        if 'slouch_limit' in settings:
            self.slouch_slider.setValue(int(settings['slouch_limit'] * 100))
        if 'proximity_limit' in settings:
            self.prox_slider.setValue(int((settings['proximity_limit'] - 1.0) * 100))
        if 'yawn_frames' in settings:
            self.yawn_slider.setValue(settings['yawn_frames'])
