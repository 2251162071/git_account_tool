# git_account_tool/main.py
import sys
import os
from PyQt5.QtWidgets import QApplication

# Set Qt platform to Wayland if running on Gnome with Wayland
if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
    os.environ['QT_QPA_PLATFORM'] = 'wayland'

from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())