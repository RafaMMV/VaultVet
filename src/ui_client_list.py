from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, 
    QTreeWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class ClientListUI(QWidget):
    # Sinal para avisar a janela principal que um cliente foi selecionado para abrir a aba dele
    client_selected = pyqtSignal(int)

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Usamos QTreeWidget para a listagem em árvore
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Lista de Clientes e Pacientes"])
        
        main_layout.addWidget(self.tree)

        # Duplo clique no item da lista abre o perfil do cliente
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)

    def load_data(self):
        self.tree.clear()
        if not self.db:
            return
        
        records = self.db.get_all_records()
        
        # Dicionário para agrupar tutores por letra inicial e guardar os dados
        # records retorna: (client_id, tutor_name, phone, pet_name, species)
        alphabet_dict = {}
        tutors_data = {}
        
        for row in records:
            client_id, tutor_name, phone, pet_name, species = row
            if not tutor_name:
                continue
                
            first_letter = tutor_name[0].upper()
            if first_letter not in alphabet_dict:
                alphabet_dict[first_letter] = {}
                
            if client_id not in alphabet_dict[first_letter]:
                alphabet_dict[first_letter][client_id] = {
                    "name": tutor_name,
                    "pets": []
                }
            
            if pet_name:
                alphabet_dict[first_letter][client_id]["pets"].append(f"{pet_name} ({species})")

        # Preenche a árvore ordenada de A a Z
        for letter in sorted(alphabet_dict.keys()):
            # Nó pai da Letra (ex: "A", "B", "C")
            letter_item = QTreeWidgetItem(self.tree)
            letter_item.setText(0, letter)
            letter_item.setFlags(letter_item.flags() & ~Qt.ItemFlag.ItemIsSelectable) # Letra não é clicável/selecionável
            
            for client_id, data in sorted(alphabet_dict[letter].items(), key=lambda x: x[1]["name"]):
                # Nó do Cliente (com a setinha para expandir os pets)
                tutor_item = QTreeWidgetItem(letter_item)
                tutor_item.setText(0, data["name"])
                tutor_item.setData(0, Qt.ItemDataRole.UserRole, client_id) # Guarda o ID do banco oculto
                
                # Adiciona os pets logo abaixo do tutor
                for pet_info in data["pets"]:
                    pet_item = QTreeWidgetItem(tutor_item)
                    pet_item.setText(0, pet_info)
                    pet_item.setFlags(pet_item.flags() & ~Qt.ItemFlag.ItemIsSelectable) # Pet é só informativo na lista

        self.tree.expandAll()

    def on_item_double_clicked(self, item, column):
        # Verifica se o item clicado é um Tutor (ele tem o ID armazenado e tem um pai que é uma letra)
        client_id = item.data(0, Qt.ItemDataRole.UserRole)
        if client_id is not None:
            # Emite o sinal informando qual ID de cliente foi aberto
            self.client_selected.emit(client_id)