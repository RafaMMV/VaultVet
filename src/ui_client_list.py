from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, 
    QTreeWidgetItem, QMessageBox, QHBoxLayout, QPushButton, QDialog
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

        # --- Criação de um topo com botão de Ação ---
        top_layout = QHBoxLayout()
        self.btn_novo_cadastro = QPushButton("+ Novo Cadastro")
        self.btn_novo_cadastro.setStyleSheet("font-weight: bold; padding: 6px;")
        # Conecta o clique do botão à função que troca de aba
        self.btn_novo_cadastro.clicked.connect(self.ir_para_cadastro)
        
        top_layout.addWidget(self.btn_novo_cadastro)
        top_layout.addStretch() # Joga o botão para a esquerda
        
        main_layout.addLayout(top_layout)

        # Usamos QTreeWidget para a listagem em árvore
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Lista de Clientes e Pacientes"])
        
        main_layout.addWidget(self.tree)

        # Duplo clique no item da lista abre o perfil do cliente ou o pet específico
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)

    def load_data(self):
        self.tree.clear()
        if not self.db:
            return
        
        # Ajustado para trazer o ID do pet também (p.id, c.id, c.first_name..., p.pet_name, p.species)
        try:
            self.db.cursor.execute("""
                SELECT p.id, c.id, c.first_name || ' ' || c.last_name, c.phone, p.pet_name, p.species
                FROM clients c
                LEFT JOIN patients p ON c.id = p.client_id
            """)
            records = self.db.cursor.fetchall()
        except Exception:
            records = []
        
        # Dicionário para agrupar tutores por letra inicial e guardar os dados
        alphabet_dict = {}
        
        for row in records:
            pet_id, client_id, tutor_name, phone, pet_name, species = row
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
                alphabet_dict[first_letter][client_id]["pets"].append({
                    "pet_id": pet_id,
                    "pet_name": pet_name,
                    "species": species
                })

        # 1. Preenche a árvore ordenada de A a Z
        for letter in sorted(alphabet_dict.keys()):
            letter_item = QTreeWidgetItem(self.tree)
            letter_item.setText(0, letter)
            letter_item.setFlags(letter_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            
            for client_id, data in sorted(alphabet_dict[letter].items(), key=lambda x: x[1]["name"]):
                tutor_item = QTreeWidgetItem(letter_item)
                tutor_item.setText(0, data["name"])
                # Guarda apenas o ID do cliente se clicar no tutor
                tutor_item.setData(0, Qt.ItemDataRole.UserRole, {"client_id": client_id, "pet_id": None})
                
                for pet_info in data["pets"]:
                    pet_item = QTreeWidgetItem(tutor_item)
                    pet_item.setText(0, f"{pet_info['pet_name']} ({pet_info['species']})")
                    # Permite selecionar o item do pet para o duplo clique funcionar
                    pet_item.setFlags(pet_item.flags() | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    # Guarda um dicionário com o ID do cliente e o ID do pet
                    pet_item.setData(0, Qt.ItemDataRole.UserRole, {
                        "client_id": client_id, 
                        "pet_id": pet_info["pet_id"]
                    })

        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            letter_item = root.child(i)
            letter_item.setExpanded(True)  

            for j in range(letter_item.childCount()):
                tutor_item = letter_item.child(j)
                tutor_item.setExpanded(False)  

    def on_item_double_clicked(self, item, column):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        client_id = data.get("client_id")
        pet_id = data.get("pet_id")

        if client_id is not None:
            # Se for pet, pega o nome do pai (tutor). Se for tutor, pega o próprio texto.
            if pet_id is not None:
                client_name = item.parent().text(0)
            else:
                client_name = item.text(0)
            
            # Importa a aba de detalhes corretamente
            from ui_client_detail import ClientDetailTab
            
            # Acessa o QTabWidget principal através da janela principal
            main_window = self.window()
            if hasattr(main_window, "tabs"):
                detail_tab = ClientDetailTab(
                    parent=main_window, 
                    db=self.db, 
                    client_id=client_id, 
                    main_window=main_window, 
                    select_pet_id=pet_id
                )
                main_window.tabs.addTab(detail_tab, f"Tutor: {client_name}")
                main_window.tabs.setCurrentWidget(detail_tab)

    def ir_para_cadastro(self):
        from ui_register import RegisterTab
        
        # Cria a janela de cadastro como um diálogo flutuante (modal)
        dialog = RegisterTab(parent=self, db=self.db)
        
        # Se o usuário salvar com sucesso, recarrega a lista de clientes por trás
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()