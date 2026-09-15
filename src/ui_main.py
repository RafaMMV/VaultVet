from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel
from ui_register import RegisterTab
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

        # 1. Aba Início (Home)
        self.home_tab = QWidget()
        home_layout = QVBoxLayout(self.home_tab)
        home_layout.addWidget(QLabel("Bem-vindo ao VaultVet! Selecione uma aba acima."))

        # 2. Aba de Cadastro
        self.register_tab = RegisterTab(parent=self, db=self.db)

        # 3. Aba de Lista de Clientes
        self.client_list_ui = ClientListUI(parent=self, db=self.db)

        # Adiciona as três abas em uma única barra superior
        self.tabs.addTab(self.home_tab, "Início")
        self.tabs.addTab(self.register_tab, "Novo Cadastro")
        self.tabs.addTab(self.client_list_ui, "Lista de Clientes")

        # Carrega os dados na lista de clientes ao iniciar
        self.client_list_ui.load_data()