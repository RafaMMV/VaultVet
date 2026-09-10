import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from database import Database
from ui_main import MainUI

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VaultVet - Sistema de Gestão Veterinária")
        self.setMinimumSize(950, 600)

        self.db = Database()
        self.main_ui = MainUI(self)
        self.setCentralWidget(self.main_ui)

        self.main_ui.save_button.clicked.connect(self.handle_save)

    def handle_save(self):
        print("Botão salvar clicado!")  

    def closeEvent(self, event):
        self.db.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())