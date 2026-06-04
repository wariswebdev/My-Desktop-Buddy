import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from styles import MAIN_STYLE

def main():
    app = QApplication(sys.argv)
    
    # Apply global stylesheet
    app.setStyleSheet(MAIN_STYLE)
    
    # Crucial for system tray apps: prevent quitting when the main window hides
    app.setQuitOnLastWindowClosed(False)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
