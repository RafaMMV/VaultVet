#////////////////////////////////////////////////////////////
#
# By: Rafael Miguel M. Vieira
# Projct made with: Qt Designer and Pyside6
# Version: 1.0.0
#
# This project can be used for study and improvement. Since this 
# is my first Python code, I want it serve as an example in the 
# future so I can see my mistakes and learn from them.
# 
# there are limitations o Qt Licenses if you want to use your products
# commercially, I recommend reading them on the official website:
# https://doc.qt.io/qtfopython/licenses.html
#
#////////////////////////////////////////////////////////////

#Import Data Services
from services.data_services import obter_data_atual

# Import Modules
import sys
import os

# Import Qt Core
from qt_core import *

# Import Main Window
from gui.windows.main_window.ui_main_window import Ui_MainWindow

# MAIN WINDOW
class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Setup main window
        self.ui = Ui_MainWindow()
        self.ui.setup_ui(self)

        # display the main window
        self.show()
    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = mainWindow()
    window.show()
    sys.exit(app.exec())