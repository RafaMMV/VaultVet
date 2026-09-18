from PyQt6.QtWidgets import QMainWindow, QTabBar, QTabWidget, QWidget, QVBoxLayout, QLabel, QMessageBox
from ui_client_list import ClientListUI
from ui_agenda import AgendaTab
from PyQt6.QtGui import QIcon

class MainUI(QMainWindow):
    def __init__(self, db=None):
        super().__init__()
        self.db = db
        self.setWindowTitle("VaultVet - Veterinary Management System")
        self.setMinimumSize(1000, 650)
        self.setWindowIcon(QIcon("../assets/logo_VaultVet.png"))  
        
        self.init_ui()

    def init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        # 1. Aba Início
        self.home_tab = QWidget()
        home_layout = QVBoxLayout(self.home_tab)
        home_layout.addWidget(QLabel("Início - Em desenvolvimento"))

        # 2. Aba Clientes
        self.client_list_ui = ClientListUI(parent=self, db=self.db)

        # 3. Aba Agendamento
        self.agenda_tab = AgendaTab(parent=self, db=self.db)

        # 4. Aba Estoque
        self.inventory_tab = QWidget()  
        inventory_layout = QVBoxLayout(self.inventory_tab)
        inventory_layout.addWidget(QLabel("Estoque - Em desenvolvimento"))

        # 5. Aba Caixa
        self.cash_flow_tab = QWidget()
        cash_flow_layout = QVBoxLayout(self.cash_flow_tab)
        cash_flow_layout.addWidget(QLabel("Caixa - Em desenvolvimento"))

        # Embojuapy porã umi aba tapére héraporãitépe
        self.tabs.addTab(self.home_tab, "Início")
        self.tabs.addTab(self.client_list_ui, "Clientes")
        self.tabs.addTab(self.agenda_tab, "Agendamento")  
        self.tabs.addTab(self.inventory_tab, "Estoque")
        self.tabs.addTab(self.cash_flow_tab, "Caixa") 

        # Eipe'a "X" umi 5 aba guasupegua ani hag̃ua ojepe'a
        for i in range(5):
            self.tabs.tabBar().setTabButton(i, QTabBar.ButtonPosition.RightSide, None)

        self.client_list_ui.load_data()

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        
        if widget in [self.home_tab, self.client_list_ui, self.agenda_tab, self.inventory_tab, self.cash_flow_tab]:
            return

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