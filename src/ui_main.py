from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QMessageBox
from ui_client_list import ClientListUI

class MainUI(QMainWindow):
    def __init__(self, db=None):
        super().__init__()
        self.db = db
        self.setWindowTitle("VaultVet - Veterinary Management System")
        self.setMinimumSize(1000, 650)
        
        self.init_ui()

    def init_ui(self):
        # Único gerenciador de abas da janela principal
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # HABILITA O "X" NAS ABAS
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        # 1. Aba Início (Home)
        self.home_tab = QWidget()
        home_layout = QVBoxLayout(self.home_tab)

        # 2. Aba de Lista de Clientes
        self.client_list_ui = ClientListUI(parent=self, db=self.db)

        # 3. Aba de Consulta
        self.consultation_tab = QWidget()
        consultation_layout = QVBoxLayout(self.consultation_tab)
        consultation_layout.addWidget(QLabel("Consulta - Em desenvolvimento"))

        # Adiciona as três abas em uma única barra superior
        self.tabs.addTab(self.home_tab, "Início")
        self.tabs.addTab(self.client_list_ui, "Lista de Clientes")
        self.tabs.addTab(self.consultation_tab, "Consulta") 

        # Carrega os dados na lista de clientes ao iniciar
        self.client_list_ui.load_data()

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        
        # Bloqueia o fechamento das abas principais fixas
        if widget in [self.home_tab, self.client_list_ui, self.consultation_tab]:
            return

        # Para as abas de clientes (ClientDetailTab), faz a checagem de alterações
        if hasattr(widget, "has_unsaved_changes") and widget.has_unsaved_changes():
            resposta = QMessageBox.question(
                self,
                "Alterações não salvas",
                "Existem alterações que não foram salvas. Deseja fechar e descartar as alterações?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if resposta == QMessageBox.StandardButton.No:
                return

        self.tabs.removeTab(index)
        widget.deleteLater()