from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QLineEdit, QFormLayout, QVBoxLayout, 
    QPushButton, QHBoxLayout, QGroupBox, QLabel, 
    QListWidget, QMessageBox, QComboBox, QDialog, QDialogButtonBox, QListWidgetItem
)
from PyQt6.QtCore import Qt


class ClientDetailTab(QWidget):
    def __init__(self, parent=None, db=None, client_id=None, main_window=None, select_pet_id=None):
        super().__init__(parent)
        self.db = db
        self.client_id = client_id
        self.main_window = main_window
        self.select_pet_id = select_pet_id  # Guarda o ID do pet recebido
        
        self.current_selected_pet_id = None 
        self._is_loading = False 
        
        self.init_ui()
        self.load_client_data()
        self.load_pets_list()
        self.connect_change_trackers()

        # Se foi aberto clicando diretamente em um pet na lista, já seleciona ele na tela
        if self.select_pet_id:
            self.auto_select_pet(self.select_pet_id)

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Cabeçalho / Ações Gerais
        top_layout = QHBoxLayout()
        self.title_label = QLabel("Detalhes do Cliente")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.save_client_button = QPushButton("Salvar Alterações do Tutor")
        self.save_client_button.setStyleSheet("font-weight: bold;")
        self.save_client_button.clicked.connect(self.save_client_changes)

        self.delete_client_button = QPushButton("Remover Cliente")
        self.delete_client_button.setStyleSheet("background-color: #ffcccc; color: #990000; font-weight: bold;")
        self.delete_client_button.clicked.connect(self.confirm_delete_client)

        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        top_layout.addWidget(self.save_client_button)
        top_layout.addWidget(self.delete_client_button)
        main_layout.addLayout(top_layout)

        # Layout dividido em duas colunas (Dados do Tutor | Gestão de Pets)
        content_layout = QHBoxLayout()

        # --- COLUNA ESQUERDA: Dados do Tutor ---
        tutor_group = QGroupBox("Dados do Tutor")
        tutor_layout = QFormLayout(tutor_group)

        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.zip_code_input = QLineEdit()
        self.address_input = QLineEdit()
        self.number_input = QLineEdit()
        self.complement_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.emergency_name_input = QLineEdit()
        self.emergency_phone_input = QLineEdit()
        self.cpf_input = QLineEdit()
        self.rg_input = QLineEdit()

        tutor_layout.addRow("Nome:", self.first_name_input)
        tutor_layout.addRow("Sobrenome:", self.last_name_input)
        tutor_layout.addRow("CEP:", self.zip_code_input)
        tutor_layout.addRow("Endereço:", self.address_input)
        tutor_layout.addRow("Número:", self.number_input)
        tutor_layout.addRow("Complemento:", self.complement_input)
        tutor_layout.addRow("Telefone:", self.phone_input)
        tutor_layout.addRow("E-mail:", self.email_input)
        tutor_layout.addRow("Contato de Emergência:", self.emergency_name_input)
        tutor_layout.addRow("Telefone de Emergência:", self.emergency_phone_input)
        tutor_layout.addRow("CPF:", self.cpf_input)
        tutor_layout.addRow("RG:", self.rg_input)

        content_layout.addWidget(tutor_group)

        # --- COLUNA DIREITA: Lista de Pets + Ficha do Pet ---
        right_container = QVBoxLayout()

        pets_group = QGroupBox("Pets Vinculados")
        pets_layout = QVBoxLayout(pets_group)

        self.pets_list_widget = QListWidget()
        self.pets_list_widget.setMaximumHeight(150)
        self.pets_list_widget.itemClicked.connect(self.on_pet_item_clicked)
        pets_layout.addWidget(self.pets_list_widget)

        pets_btn_layout = QHBoxLayout()
        self.add_pet_button = QPushButton("+ Adicionar Novo Pet")
        self.add_pet_button.clicked.connect(self.prepare_new_pet_form)
        
        self.remove_pet_button = QPushButton("Remover Pet Selecionado")
        self.remove_pet_button.setStyleSheet("color: #ffcccc;")
        self.remove_pet_button.clicked.connect(self.confirm_delete_pet)

        pets_btn_layout.addWidget(self.add_pet_button)
        pets_btn_layout.addWidget(self.remove_pet_button)
        pets_layout.addLayout(pets_btn_layout)
        right_container.addWidget(pets_group)

        # Ficha do Pet (inicialmente oculta)
        self.patient_group = QGroupBox("Ficha do Paciente (Pet)")
        patient_layout = QFormLayout(self.patient_group)

        self.pet_name_input = QLineEdit()
        self.pet_name_input.editingFinished.connect(self.format_pet_name)

        self.species_input = QComboBox()
        self.species_input.addItems(["Canino", "Felino", "Réptil", "Ave", "Outro"])
        self.species_input.currentIndexChanged.connect(self.on_species_changed)

        self.breed_input = QComboBox()
        self.breed_input.setEditable(True)
        self.update_breeds("Canino")
        self.breed_input.currentIndexChanged.connect(self.on_breed_changed)

        self.gender_input = QComboBox()
        self.gender_input.addItems(["Macho", "Fêmea"])
        
        self.neutered_input = QComboBox()
        self.neutered_input.addItems(["Sim", "Não"])
        
        self.birth_date_input = QLineEdit()
        self.birth_date_input.setPlaceholderText("DD/MM/AAAA")
        self.birth_date_input.textChanged.connect(self.format_birth_date)
        
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Ex: 3 anos e 2 meses")
        
        self.weight_input = QLineEdit()
        self.microchip_input = QLineEdit()

        patient_layout.addRow("Nome do Pet:", self.pet_name_input)
        patient_layout.addRow("Espécie:", self.species_input)
        patient_layout.addRow("Raça:", self.breed_input)
        patient_layout.addRow("Sexo:", self.gender_input)
        patient_layout.addRow("Castrado:", self.neutered_input)
        patient_layout.addRow("Nascimento:", self.birth_date_input)
        patient_layout.addRow("Idade:", self.age_input)
        patient_layout.addRow("Peso (kg):", self.weight_input)
        patient_layout.addRow("Microchip:", self.microchip_input)

        self.save_pet_button = QPushButton("Salvar Alterações / Cadastrar Pet")
        self.save_pet_button.setStyleSheet("font-weight: bold; padding: 6px;")
        
        # Proteção contra conexões duplicadas
        try:
            self.save_pet_button.clicked.disconnect()
        except TypeError:
            pass
            
        self.save_pet_button.clicked.connect(self.save_pet_data)
        patient_layout.addRow(self.save_pet_button)
        
        right_container.addWidget(self.patient_group)
        self.patient_group.hide()

        content_layout.addLayout(right_container)
        main_layout.addLayout(content_layout)

    def load_client_data(self):
        if not self.db or not self.client_id:
            return
        
        client_data = self.db.get_client_by_id(self.client_id)
        if client_data:
            self.first_name_input.setText(str(client_data[0] or ""))
            self.last_name_input.setText(str(client_data[1] or ""))
            self.zip_code_input.setText(str(client_data[2] or ""))
            self.address_input.setText(str(client_data[3] or ""))
            self.number_input.setText(str(client_data[4] or ""))
            self.complement_input.setText(str(client_data[5] or ""))
            self.phone_input.setText(str(client_data[6] or ""))
            self.email_input.setText(str(client_data[7] or ""))
            self.emergency_name_input.setText(str(client_data[8] or ""))
            self.emergency_phone_input.setText(str(client_data[9] or ""))
            self.cpf_input.setText(str(client_data[10] or ""))
            self.rg_input.setText(str(client_data[11] or ""))

    def load_pets_list(self):
        self.pets_list_widget.clear()
        if not self.db:
            return
        
        pets = self.db.get_pets_by_client_id(self.client_id)
        for pet in pets:
            name = pet[2]
            species = pet[5]
            
            item = QListWidgetItem(f"{name} ({species})")
            item.setData(Qt.ItemDataRole.UserRole, pet)
            self.pets_list_widget.addItem(item)

    def auto_select_pet(self, pet_id):
        """Varre a lista de pets da aba e abre a ficha do pet correspondente automaticamente"""
        for i in range(self.pets_list_widget.count()):
            item = self.pets_list_widget.item(i)
            pet_data = item.data(Qt.ItemDataRole.UserRole)
            if pet_data[0] == pet_id:
                self.pets_list_widget.setCurrentItem(item)
                self.load_pet_into_form(pet_data)
                break

    def save_pet_data(self):
        if not self.db:
            return

        pet_name = self.pet_name_input.text().strip()
        if not pet_name:
            QMessageBox.warning(self, "Aviso", "O nome do pet é obrigatório.")
            return

        gender = self.gender_input.currentText()
        neutered = self.neutered_input.currentText()
        species = self.species_input.currentText()
        breed = self.breed_input.currentText()
        birth_date = self.birth_date_input.text().strip()
        age = self.age_input.text().strip()
        microchip = self.microchip_input.text().strip()
        
        weight_text = self.weight_input.text().strip().replace(',', '.')
        try:
            weight = float(weight_text) if weight_text else 0.0
        except ValueError:
            weight = 0.0

        try:
            if self.current_selected_pet_id is None:
                self.db.cursor.execute("""
                    INSERT INTO patients (
                        client_id, pet_name, gender, neutered, species, 
                        breed, birth_date, age, weight, microchip
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (self.client_id, pet_name, gender, neutered, species, breed, birth_date, age, weight, microchip))
                self.db.conn.commit()
                QMessageBox.information(self, "Sucesso", "Novo pet cadastrado com sucesso!")
            else:
                self.db.cursor.execute("""
                    UPDATE patients SET 
                        pet_name = ?, gender = ?, neutered = ?, species = ?, 
                        breed = ?, birth_date = ?, age = ?, weight = ?, microchip = ?
                    WHERE id = ?
                """, (pet_name, gender, neutered, species, breed, birth_date, age, weight, microchip, self.current_selected_pet_id))
                self.db.conn.commit()
                QMessageBox.information(self, "Sucesso", "Alterações do pet salvas com sucesso!")

            self.has_unsaved_changes = False
            self.load_pets_list()
            
            if hasattr(self.main_window, "client_list_ui"):
                self.main_window.client_list_ui.load_data()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar o pet: {e}")

    def connect_change_trackers(self):
        self.pet_name_input.textChanged.connect(self.mark_as_modified)
        self.species_input.currentIndexChanged.connect(self.mark_as_modified)
        self.breed_input.currentIndexChanged.connect(self.mark_as_modified)
        self.gender_input.currentIndexChanged.connect(self.mark_as_modified)
        self.neutered_input.currentIndexChanged.connect(self.mark_as_modified)
        self.birth_date_input.textChanged.connect(self.mark_as_modified)
        self.age_input.textChanged.connect(self.mark_as_modified)
        self.weight_input.textChanged.connect(self.mark_as_modified)
        self.microchip_input.textChanged.connect(self.mark_as_modified)
        self.has_unsaved_changes = False

    def mark_as_modified(self):
        if not self._is_loading:
            self.has_unsaved_changes = True

    def check_unsaved_changes(self):
        if getattr(self, "has_unsaved_changes", False):
            reply = QMessageBox.question(
                self, "Alterações Não Salvas",
                "Você possui alterações não salvas ou está preenchendo um novo pet. Deseja descartar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            return reply == QMessageBox.StandardButton.Yes
        return True

    def on_pet_item_clicked(self, item):
        pet_data = item.data(Qt.ItemDataRole.UserRole)
        target_pet_id = pet_data[0]

        if self.current_selected_pet_id == target_pet_id and self.patient_group.isVisible():
            return

        if not self.check_unsaved_changes():
            return

        self.load_pet_into_form(pet_data)

    def load_pet_into_form(self, pet):
        self._is_loading = True
        self.current_selected_pet_id = pet[0]
        self.pet_name_input.setText(str(pet[2] or ""))
        
        species = str(pet[5] or "Canino")
        index = self.species_input.findText(species)
        if index >= 0:
            self.species_input.setCurrentIndex(index)
        else:
            self.species_input.insertItem(0, species)
            self.species_input.setCurrentIndex(0)
            
        self.update_breeds(species)
        
        breed = str(pet[6] or "")
        b_index = self.breed_input.findText(breed)
        if b_index >= 0:
            self.breed_input.setCurrentIndex(b_index)
        else:
            self.breed_input.setEditText(breed)

        self.gender_input.setCurrentText(str(pet[3] or "Macho"))
        self.neutered_input.setCurrentText(str(pet[4] or "Sim"))
        self.birth_date_input.setText(str(pet[7] or ""))
        self.age_input.setText(str(pet[8] or ""))
        
        weight_val = pet[9]
        if weight_val is not None and weight_val != "":
            self.weight_input.setText(str(weight_val).replace('.', ','))
        else:
            self.weight_input.clear()
            
        self.microchip_input.setText(str(pet[10] or ""))
        
        self.has_unsaved_changes = False
        self._is_loading = False
        self.patient_group.show()

    def prepare_new_pet_form(self):
        if not self.check_unsaved_changes():
            return

        self._is_loading = True
        self.current_selected_pet_id = None 
        self.pets_list_widget.clearSelection()
        
        self.pet_name_input.clear()
        self.species_input.setCurrentIndex(0)
        self.update_breeds("Canino")
        self.gender_input.setCurrentIndex(0)
        self.neutered_input.setCurrentIndex(0)
        self.birth_date_input.clear()
        self.age_input.clear()
        self.weight_input.clear()
        self.microchip_input.clear()
        
        self.has_unsaved_changes = False
        self._is_loading = False
        self.patient_group.show()

    def update_breeds(self, species):
        self.breed_input.clear()
        if species == "Canino":
            breeds = [
                "SRD (Vira-lata)", "Shih Tzu", "Poodle", "Yorkshire Terrier", 
                "Golden Retriever", "Labrador Retriever", "Bulldog Francês", 
                "Pitbull", "Pastor Alemão", "Lhasa Apso", "Beagle", "Pug", 
                "Spitz Alemão", "Border Collie", "Dachshund", "Outro..."
            ]
        elif species == "Felino":
            breeds = [
                "SRD (Gato de Rua)", "Persa", "Siamês", "Maine Coon", 
                "Angorá", "British Shorthair", "Ragdoll", "Sphynx", 
                "Azul Russo", "Scottish Fold", "Outro..."
            ]
        else:
            breeds = ["Outro..."]
        self.breed_input.addItems(breeds)

    def on_species_changed(self, index):
        if self._is_loading:
            return
        species = self.species_input.currentText()
        if species == "Outro":
            custom_species = self.open_custom_popup("Cadastrar Outra Espécie", "Digite a espécie:")
            if custom_species:
                self.species_input.blockSignals(True)
                self.species_input.insertItem(0, custom_species)
                self.species_input.setCurrentIndex(0)
                self.species_input.blockSignals(False)
                self.update_breeds(custom_species)
            else:
                self.species_input.setCurrentIndex(0)
        else:
            self.update_breeds(species)

    def on_breed_changed(self, index):
        if self._is_loading:
            return
        if self.breed_input.currentText() == "Outro...":
            custom_breed = self.open_custom_popup("Cadastrar Outra Raça", "Digite a raça:")
            if custom_breed:
                self.breed_input.blockSignals(True)
                self.breed_input.insertItem(0, custom_breed)
                self.breed_input.setCurrentIndex(0)
                self.breed_input.blockSignals(False)
            else:
                self.breed_input.setCurrentIndex(1)

    def open_custom_popup(self, title, label_text):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(300, 130)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(label_text))
        line_edit = QLineEdit()
        layout.addWidget(line_edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return line_edit.text().strip()
        return None

    def format_pet_name(self):
        text = self.pet_name_input.text().strip()
        if text:
            formatted = text[0].upper() + text[1:]
            self.pet_name_input.blockSignals(True)
            self.pet_name_input.setText(formatted)
            self.pet_name_input.blockSignals(False)

    def format_birth_date(self, text):
        digits = "".join([c for c in text if c.isdigit()])[:8]
        formatted = ""
        if len(digits) > 4:
            formatted = f"{digits[:2]}/{digits[2:4]}/{digits[4:]}"
        elif len(digits) > 2:
            formatted = f"{digits[:2]}/{digits[2:]}"
        else:
            formatted = digits

        self.birth_date_input.blockSignals(True)
        self.birth_date_input.setText(formatted)
        self.birth_date_input.setCursorPosition(len(formatted))
        self.birth_date_input.blockSignals(False)

        if len(digits) == 8:
            calculated_age = self.calculate_age_from_date(formatted)
            if calculated_age:
                self.age_input.setText(calculated_age)

        if not self._is_loading:
            self.has_unsaved_changes = True

    def calculate_age_from_date(self, date_str):
        try:
            birth_date = datetime.strptime(date_str, "%d/%m/%Y")
            today = datetime.now()
            
            years = today.year - birth_date.year
            months = today.month - birth_date.month
            
            if today.day < birth_date.day:
                months -= 1
            if months < 0:
                years -= 1
                months += 12
                
            if years > 0 and months > 0:
                return f"{years} ano(s) e {months} mes(es)"
            elif years > 0:
                return f"{years} ano(s)"
            elif months > 0:
                return f"{months} mes(es)"
            else:
                return "Menos de 1 mês"
        except ValueError:
            return ""

    def save_client_changes(self):
        if not self.db:
            return
        updated_data = (
            self.first_name_input.text().strip(),
            self.last_name_input.text().strip(),
            self.zip_code_input.text().strip(),
            self.address_input.text().strip(),
            self.number_input.text().strip(),
            self.complement_input.text().strip(),
            self.phone_input.text().strip(),
            self.email_input.text().strip(),
            self.emergency_name_input.text().strip(),
            self.emergency_phone_input.text().strip(),
            self.cpf_input.text().strip(),
            self.rg_input.text().strip(),
            self.client_id
        )
        try:
            self.db.cursor.execute("""
                UPDATE clients SET 
                    first_name = ?, last_name = ?, zip_code = ?, address = ?, 
                    number = ?, complement = ?, phone = ?, email = ?, 
                    emergency_contact = ?, emergency_phone = ?, cpf = ?, rg = ?
                WHERE id = ?
            """, updated_data)
            self.db.conn.commit()
            QMessageBox.information(self, "Sucesso", "Alterações do tutor salvas com sucesso!")
            if hasattr(self.main_window, "client_list_ui"):
                self.main_window.client_list_ui.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar as alterações: {e}")

    def confirm_delete_client(self):
        reply = QMessageBox.question(
            self, "Confirmação de Exclusão",
            "Tem certeza que deseja remover este cliente e todos os seus pets?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_client(self.client_id)
            if hasattr(self.main_window, "client_list_ui"):
                self.main_window.client_list_ui.load_data()
            current_index = self.main_window.tabs.currentIndex()
            self.main_window.tabs.removeTab(current_index)

    def confirm_delete_pet(self):
        selected_item = self.pets_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Aviso", "Selecione um pet na lista para remover.")
            return

        pet_data = selected_item.data(Qt.ItemDataRole.UserRole)
        pet_id = pet_data[0]

        reply = QMessageBox.question(
            self, "Confirmação de Exclusão",
            "Tem certeza que deseja remover este pet?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.cursor.execute("DELETE FROM patients WHERE id = ?", (pet_id,))
                self.db.conn.commit()
                QMessageBox.information(self, "Sucesso", "Pet removido com sucesso!")
                self.load_pets_list()
                if hasattr(self.main_window, "client_list_ui"):
                    self.main_window.client_list_ui.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível remover o pet: {e}")