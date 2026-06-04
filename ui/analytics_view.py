from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt

class AnalyticsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Analytics & Session Health")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #cdd6f4;")
        layout.addWidget(title)

        self.score_label = QLabel("Session Health Score: 100%")
        self.score_label.setStyleSheet("font-size: 18px; color: #a6adc8;")
        layout.addWidget(self.score_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #313244;
                border-radius: 5px;
                text-align: center;
                background-color: #181825;
                color: #11111b;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #a6e3a1;
                border-radius: 5px;
            }
        """)
        self.progress_bar.setValue(100)
        layout.addWidget(self.progress_bar)

        log_title = QLabel("Recent Alerts Log")
        log_title.setStyleSheet("font-size: 16px; color: #a6adc8; margin-top: 15px;")
        layout.addWidget(log_title)

        self.log_table = QTableWidget(0, 3)
        self.log_table.setHorizontalHeaderLabels(["Timestamp", "Alert Type", "Status"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.log_table.setStyleSheet("""
            QTableWidget {
                background-color: #181825;
                color: #cdd6f4;
                border: 1px solid #313244;
                border-radius: 5px;
                gridline-color: #313244;
            }
            QHeaderView::section {
                background-color: #1e1e2e;
                color: #a6adc8;
                padding: 4px;
                border: 1px solid #313244;
            }
        """)
        layout.addWidget(self.log_table)

    def update_stats(self, stats):
        total = stats.get('total_frames', 0)
        good = stats.get('good_frames', 0)
        
        if total > 0:
            score = int((good / total) * 100)
            self.score_label.setText(f"Session Health Score: {score}%")
            self.progress_bar.setValue(score)
            
            # Change color dynamically based on health
            color = "#a6e3a1" if score > 85 else "#f9e2af" if score > 60 else "#f38ba8"
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{ border: 1px solid #313244; border-radius: 5px; text-align: center; background-color: #181825; color: #cdd6f4; font-weight: bold; }}
                QProgressBar::chunk {{ background-color: {color}; border-radius: 5px; }}
            """)

        alerts = stats.get('recent_alerts', [])
        self.log_table.setRowCount(len(alerts))
        for row, alert in enumerate(alerts):
            self.log_table.setItem(row, 0, QTableWidgetItem(alert.get("timestamp", "")))
            self.log_table.setItem(row, 1, QTableWidgetItem(alert.get("type", "")))
            
            status = alert.get("status", "")
            status_item = QTableWidgetItem(status)
            if status == "Triggered":
                from PyQt6.QtGui import QColor, QBrush
                status_item.setForeground(QBrush(QColor("#f38ba8")))
            elif status == "Resolved":
                from PyQt6.QtGui import QColor, QBrush
                status_item.setForeground(QBrush(QColor("#a6e3a1")))
            self.log_table.setItem(row, 2, status_item)
