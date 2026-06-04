from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QListWidget, 
                             QStackedWidget, QLabel, QSystemTrayIcon, QMenu, QApplication)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt
from ui.dashboard import Dashboard
from core.cv_worker import CVWorker
from ui.notification import LiveCorrectionAlert

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyDesktopBuddy")
        self.resize(900, 700)
        
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar Navigation
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220)
        tabs = ["Dashboard", "Deadlines & Goals", "Focus Music", "Settings"]
        self.sidebar.addItems(tabs)
        self.sidebar.setCurrentRow(0)
        
        # Stacked Widget for Pages
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: #1e1e2e;")
        
        # Initialize Pages
        self.dashboard_page = Dashboard()
        
        self.deadlines_page = QLabel("Deadlines & Goals (Coming Soon)")
        self.deadlines_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.deadlines_page.setStyleSheet("color: #a6adc8; font-size: 18px;")
        
        self.music_page = QLabel("Focus Music (Coming Soon)")
        self.music_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.music_page.setStyleSheet("color: #a6adc8; font-size: 18px;")
        
        self.settings_page = QLabel("Settings (Coming Soon)")
        self.settings_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.settings_page.setStyleSheet("color: #a6adc8; font-size: 18px;")
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.addWidget(self.deadlines_page)
        self.stacked_widget.addWidget(self.music_page)
        self.stacked_widget.addWidget(self.settings_page)
        
        # Connect sidebar to page switching
        self.sidebar.currentRowChanged.connect(self.stacked_widget.setCurrentIndex)
        
        # Assemble main layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stacked_widget)
        
        # System Tray Setup
        self.setup_system_tray()
        
        # CV Worker Setup
        self.total_alerts = 0
        self.setup_cv_worker()

    def setup_cv_worker(self):
        self.cv_worker = CVWorker()
        self.cv_worker.alert_signal.connect(self.on_cv_alert)
        self.cv_worker.calibration_signal.connect(self.on_calibration_signal)
        
        # Setup Live Alert Window
        self.live_alert = LiveCorrectionAlert()
        self.cv_worker.frame_signal.connect(self.on_frame_signal)
        self.cv_worker.hide_alert_signal.connect(self.on_hide_alert_signal)
        
        # Connect recalibrate button
        self.dashboard_page.recalibrate_btn.clicked.connect(self.cv_worker.force_recalibrate)
        
        # Connect toggles from dashboard
        if "Posture Detection" in self.dashboard_page.feature_widgets:
            posture_widget = self.dashboard_page.feature_widgets["Posture Detection"]
            posture_widget.toggled.connect(self.cv_worker.set_posture_enabled)
            
        if "Fatigue & Sleepiness Detection" in self.dashboard_page.feature_widgets:
            fatigue_widget = self.dashboard_page.feature_widgets["Fatigue & Sleepiness Detection"]
            fatigue_widget.toggled.connect(self.cv_worker.set_fatigue_enabled)
            
        self.cv_worker.start()
        
        # Ensure cleanup on quit
        QApplication.instance().aboutToQuit.connect(self.cleanup_worker)

    def on_frame_signal(self, q_image):
        if not self.live_alert.isVisible():
            self.live_alert.show()
        self.live_alert.update_frame(q_image)

    def on_hide_alert_signal(self):
        self.live_alert.hide()

    def cleanup_worker(self):
        self.cv_worker.stop()
        self.cv_worker.wait()

    def on_cv_alert(self, title, message):
        # Native Windows notification
        self.tray_icon.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Warning,
            5000
        )
        # Update dashboard alert counter
        self.total_alerts += 1
        self.dashboard_page.recent_alerts_label.setText(f"{self.total_alerts} alerts today")

    def on_calibration_signal(self, state):
        if state == "started":
            self.tray_icon.showMessage(
                "MyDesktopBuddy Calibration",
                "Sit up straight — calibrating...",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )

    def setup_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        # Use a standard icon for now (can be replaced with a custom logo later)
        icon = self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        
        # Tray context menu
        tray_menu = QMenu()
        
        show_action = QAction("Show Dashboard", self)
        show_action.triggered.connect(self.show_normal)
        
        quit_action = QAction("Quit MyDesktopBuddy", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()
        
    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_normal()

    def show_normal(self):
        self.show()
        self.activateWindow()

    def closeEvent(self, event):
        """Minimize to system tray on close instead of exiting."""
        event.ignore()
        self.hide()
        if hasattr(self, 'live_alert'):
            self.live_alert.hide()
        self.tray_icon.showMessage(
            "MyDesktopBuddy",
            "Application is still running in the background.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
