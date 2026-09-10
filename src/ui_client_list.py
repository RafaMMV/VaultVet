from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QHeaderView, QMessageBox
)

class ClientListUI(QWidget):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Tabela de registros
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID Tutor", "Nome do Tutor", "Telefone", "Nome do Pet", "Espécie"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Botões de ação
        button_layout = QHBoxLayout()
        
        self.btn_edit = QPushButton("Editar")
        self.btn_add_pet = QPushButton("Adicionar Novo Pet")
        self.btn_remove = QPushButton("Remover")

        self.btn_edit.setStyleSheet("padding: 6px; font-weight: bold;")
        self.btn_add_pet.setStyleSheet("padding: 6px; font-weight: bold;")
        self.btn_remove.setStyleSheet("padding: 6px; font-weight: bold; color: darkred;")

        button_layout.addWidget(self.btn_edit)
        button_layout.addWidget(self.btn_add_pet)
        button_layout.addWidget(self.btn_remove)

        main_layout.addWidget(self.table)
        main_layout.addLayout(button_layout)

        # Conexões básicas
        self.btn_edit.clicked.connect(self.edit_selected)
        self.btn_add_pet.clicked.connect(self.add_pet_to_client)
        self.btn_remove.clicked.connect(self.remove_selected)

    def load_data(self):
        self.table.setRowCount(0)
        if not self.db:
            return
        
        records = self.db.get_all_records()
        for row_idx, row_data in enumerate(records):
            self.table.insertRow(row_idx)
            for col_idx, data in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(data if data else "")))

    def edit_selected(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um cliente na tabela para editar.")
            return
        print("Editar item da linha:", selected)

    def add_pet_to_client(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um cliente para adicionar um novo pet.")
            return
        print("Adicionar pet para o cliente da linha:", selected)

    def remove_selected(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um item na tabela para remover.")
            return
        print("Remover item da linha:", selected)