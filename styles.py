MAIN_STYLE = """
QMainWindow {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QWidget {
    font-family: 'Segoe UI', sans-serif;
    color: #cdd6f4;
}
QListWidget {
    background-color: #181825;
    border: none;
    padding: 10px;
    font-size: 14px;
}
QListWidget::item {
    padding: 10px;
    border-radius: 5px;
    margin-bottom: 5px;
}
QListWidget::item:selected {
    background-color: #89b4fa;
    color: #11111b;
}
QListWidget::item:hover:!selected {
    background-color: #313244;
}
QLabel {
    font-size: 14px;
}
"""
