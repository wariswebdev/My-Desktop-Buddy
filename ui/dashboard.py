from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGridLayout, QFrame, QPushButton)
from PyQt6.QtCore import Qt
from ui.widgets import ToggleSwitch

class FeatureToggleWidget(QWidget):
    def __init__(self, feature_name, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.label = QLabel(feature_name)
        self.toggle = ToggleSwitch()
        
        # Expose toggled signal
        self.toggled = self.toggle.toggled
        
        # Print debug statement when toggled
        self.toggle.toggled.connect(lambda checked: print(f"{feature_name}: {'Enabled' if checked else 'Disabled'}"))
        
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.toggle)

class Dashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # Header
        header = QLabel("Welcome back, Buddy.")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #cdd6f4;")
        layout.addWidget(header)
        
        # Status Overview
        status_label = QLabel("Status Overview")
        status_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #a6adc8;")
        layout.addWidget(status_label)
        
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # Card 1: Today's Screen Time
        card1 = QFrame()
        card1.setStyleSheet("background-color: #313244; border-radius: 10px; padding: 20px;")
        card1_layout = QVBoxLayout(card1)
        c1_title = QLabel("Today's Screen Time")
        c1_title.setStyleSheet("color: #bac2de; font-size: 14px;")
        c1_val = QLabel("4h 12m")
        c1_val.setStyleSheet("color: #89b4fa; font-size: 24px; font-weight: bold;")
        card1_layout.addWidget(c1_title)
        card1_layout.addWidget(c1_val)
        grid.addWidget(card1, 0, 0)
        
        # Card 2: Recent Alerts
        card2 = QFrame()
        card2.setStyleSheet("background-color: #313244; border-radius: 10px; padding: 20px;")
        card2_layout = QVBoxLayout(card2)
        c2_title = QLabel("Recent Alerts")
        c2_title.setStyleSheet("color: #bac2de; font-size: 14px;")
        self.recent_alerts_label = QLabel("0 alerts today")
        self.recent_alerts_label.setStyleSheet("color: #f38ba8; font-size: 24px; font-weight: bold;")
        card2_layout.addWidget(c2_title)
        card2_layout.addWidget(self.recent_alerts_label)
        grid.addWidget(card2, 0, 1)
        
        layout.addLayout(grid)
        
        # Feature Controls
        feature_label = QLabel("Feature Controls")
        feature_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #a6adc8; margin-top: 15px;")
        layout.addWidget(feature_label)
        
        features = [
            "Posture Detection",
            "Fatigue & Sleepiness Detection",
            "Phone Distraction Detection",
            "Smart Break Assistant",
            "Resource Optimization",
            "Deadline & Reminder System",
            "Focus Music Integration"
        ]
        
        features_frame = QFrame()
        features_frame.setStyleSheet("background-color: #181825; border-radius: 10px; padding: 10px;")
        features_layout = QVBoxLayout(features_frame)
        features_layout.setSpacing(10)
        
        self.feature_widgets = {}
        for f in features:
            widget = FeatureToggleWidget(f)
            self.feature_widgets[f] = widget
            features_layout.addWidget(widget)
            
        layout.addWidget(features_frame)
        
        # Recalibrate Button
        self.recalibrate_btn = QPushButton("Recalibrate Baseline")
        self.recalibrate_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)
        layout.addWidget(self.recalibrate_btn)
        
        layout.addStretch()
