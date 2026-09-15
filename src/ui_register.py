from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QLineEdit, QComboBox, 
    QFormLayout, QVBoxLayout, QPushButton, QHBoxLayout, QGroupBox,
    QDialog, QLabel, QDialogButtonBox, QMessageBox
)

class RegisterTab(QDialog):  # Mudado de QWidget para QDialog
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Novo Cadastro de Cliente e Pet")
        self.setMinimumSize(700, 500)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # --- Client Form Group (Tutor) ---
        client_group = QGroupBox("Dados do Tutor", self)
        client_layout = QFormLayout(client_group)

        self.first_name_input = QLineEdit()
        self.first_name_input.editingFinished.connect(self.apply_name_formatting)
        
        self.last_name_input = QLineEdit()
        self.last_name_input.editingFinished.connect(self.apply_name_formatting)

        self.cpf_input = QLineEdit()
        self.cpf_input.setPlaceholderText("000.000.000-00")
        self.cpf_input.textChanged.connect(self.format_cpf)

        self.rg_input = QLineEdit()
        self.rg_input.setPlaceholderText("00.000.000-0")
        self.rg_input.textChanged.connect(self.format_rg)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("(00) 00000-0000")
        self.phone_input.textChanged.connect(self.format_phone)

        self.email_input = QLineEdit()
        
        # Emergency contact fields
        self.emergency_name_input = QLineEdit()
        self.emergency_name_input.setPlaceholderText("Nome do contato de emergência")
        self.emergency_name_input.editingFinished.connect(self.apply_name_formatting)

        self.emergency_phone_input = QLineEdit()
        self.emergency_phone_input.setPlaceholderText("(00) 00000-0000")
        self.emergency_phone_input.textChanged.connect(self.format_phone)
        
        # Address fields
        self.zip_code_input = QLineEdit()
        self.zip_code_input.setPlaceholderText("00000-000")
        self.zip_code_input.textChanged.connect(self.format_cep)
        self.zip_code_input.editingFinished.connect(self.fetch_cep_address)

        self.address_input = QLineEdit()  
        self.number_input = QLineEdit()   
        self.complement_input = QLineEdit() 
        self.complement_input.setPlaceholderText("Ex: Apto 101, Bloco B")

        client_layout.addRow("Nome*:", self.first_name_input)
        client_layout.addRow("Sobrenome:", self.last_name_input)
        client_layout.addRow("CPF:", self.cpf_input)
        client_layout.addRow("RG:", self.rg_input)
        client_layout.addRow("Telefone:", self.phone_input)
        client_layout.addRow("E-mail:", self.email_input)
        client_layout.addRow("Contato de Emergência:", self.emergency_name_input)
        client_layout.addRow("Telefone de Emergência:", self.emergency_phone_input)
        client_layout.addRow("CEP:", self.zip_code_input)
        client_layout.addRow("Endereço:", self.address_input)
        client_layout.addRow("Número:", self.number_input)
        client_layout.addRow("Complemento:", self.complement_input)

        # --- Pet ---
        patient_group = QGroupBox("Dados do Paciente (Pet)", self)
        patient_layout = QFormLayout(patient_group)

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

        patient_layout.addRow("Nome do Pet*:", self.pet_name_input)
        patient_layout.addRow("Espécie:", self.species_input)
        patient_layout.addRow("Raça:", self.breed_input)
        patient_layout.addRow("Sexo:", self.gender_input)
        patient_layout.addRow("Castrado:", self.neutered_input)
        patient_layout.addRow("Nascimento:", self.birth_date_input)
        patient_layout.addRow("Idade:", self.age_input)
        patient_layout.addRow("Peso (kg):", self.weight_input)
        patient_layout.addRow("Microchip:", self.microchip_input)

        self.save_button = QPushButton("Salvar Cadastro")
        self.save_button.setStyleSheet("font-weight: bold; padding: 8px;")
        # Conecta o botão à função de salvar que faltava
        self.save_button.clicked.connect(self.save_registration)

        left_side = QVBoxLayout()
        left_side.addWidget(client_group)

        right_side = QVBoxLayout()
        right_side.addWidget(patient_group)
        right_side.addWidget(self.save_button)

        main_layout.addLayout(left_side)
        main_layout.addLayout(right_side)

    def save_registration(self):
        if not self.db:
            QMessageBox.critical(self, "Erro", "Conexão com o banco de dados não disponível.")
            return

        # Coleta e valida dados obrigatórios
        first_name = self.first_name_input.text().strip()
        pet_name = self.pet_name_input.text().strip()

        if not first_name:
            QMessageBox.warning(self, "Aviso", "O nome do tutor é obrigatório.")
            self.first_name_input.setFocus()
            return

        if not pet_name:
            QMessageBox.warning(self, "Aviso", "O nome do pet é obrigatório.")
            self.pet_name_input.setFocus()
            return

        # Demais dados do tutor
        last_name = self.last_name_input.text().strip()
        cpf = self.cpf_input.text().strip()
        rg = self.rg_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        emergency_name = self.emergency_name_input.text().strip()
        emergency_phone = self.emergency_phone_input.text().strip()
        zip_code = self.zip_code_input.text().strip()
        address = self.address_input.text().strip()
        number = self.number_input.text().strip()
        complement = self.complement_input.text().strip()

        # Demais dados do pet
        species = self.species_input.currentText()
        breed = self.breed_input.currentText()
        gender = self.gender_input.currentText()
        neutered = self.neutered_input.currentText()
        birth_date = self.birth_date_input.text().strip()
        age = self.age_input.text().strip()
        microchip = self.microchip_input.text().strip()

        # Tratamento seguro do peso (substitui vírgula por ponto para o banco REAL)
        weight_text = self.weight_input.text().strip().replace(',', '.')
        try:
            weight = float(weight_text) if weight_text else 0.0
        except ValueError:
            weight = 0.0

        try:
            # 1. Insere o tutor na tabela clients
            self.db.cursor.execute("""
                INSERT INTO clients (
                    first_name, last_name, zip_code, address, number, complement,
                    phone, email, emergency_contact, emergency_phone, cpf, rg
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                first_name, last_name, zip_code, address, number, complement,
                phone, email, emergency_name, emergency_phone, cpf, rg
            ))
            
            # Pega o ID gerado para o cliente recém-cadastrado
            client_id = self.db.cursor.lastrowid

            # 2. Insere o pet vinculado ao ID do cliente na tabela patients
            self.db.cursor.execute("""
                INSERT INTO patients (
                    client_id, pet_name, gender, neutered, species, 
                    breed, birth_date, age, weight, microchip
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client_id, pet_name, gender, neutered, species, 
                breed, birth_date, age, weight, microchip
            ))

            self.db.conn.commit()
            QMessageBox.information(self, "Sucesso", "Cadastro de cliente e pet realizado com sucesso!")
            self.accept()  # Fecha a janela de diálogo com sucesso

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar o cadastro:\n{e}")

    def format_cpf(self, text):
        digits = "".join([c for c in text if c.isdigit()])[:11]
        formatted = ""
        if len(digits) > 9:
            formatted = f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
        elif len(digits) > 6:
            formatted = f"{digits[:3]}.{digits[3:6]}.{digits[6:]}"
        elif len(digits) > 3:
            formatted = f"{digits[:3]}.{digits[3:]}"
        else:
            formatted = digits

        self.cpf_input.blockSignals(True)
        self.cpf_input.setText(formatted)
        self.cpf_input.blockSignals(False)

    def format_rg(self, text):
        digits = "".join([c for c in text if c.isdigit()])[:9]
        formatted = ""
        if len(digits) > 8:
            formatted = f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}-{digits[8:]}"
        elif len(digits) > 5:
            formatted = f"{digits[:2]}.{digits[2:5]}.{digits[5:]}"
        elif len(digits) > 2:
            formatted = f"{digits[:2]}.{digits[2:]}"
        else:
            formatted = digits

        self.rg_input.blockSignals(True)
        self.rg_input.setText(formatted)
        self.rg_input.blockSignals(False)

    def format_phone(self, text):
        digits = "".join([c for c in text if c.isdigit()])[:11]
        formatted = ""
        if len(digits) > 10:
            formatted = f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
        elif len(digits) > 6:
            formatted = f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
        elif len(digits) > 2:
            formatted = f"({digits[:2]}) {digits[2:]}"
        else:
            formatted = digits

        sender = self.sender()
        if sender:
            sender.blockSignals(True)
            sender.setText(formatted)
            sender.blockSignals(False)

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

    def format_proper_name(self, text):
            exceptions = {'de', 'da', 'do', 'dos', 'das', 'di', 'du', 'e'}
            words = text.strip().split()
            if not words:
                return ""
                
            formatted_words = []
            sender = self.sender()
            
            for i, word in enumerate(words):
                w_lower = word.lower()
                if sender == getattr(self, 'last_name_input', None) and i == 0 and w_lower in exceptions:
                    formatted_words.append(w_lower)
                elif i > 0 and w_lower in exceptions:
                    formatted_words.append(w_lower)
                else:
                    formatted_words.append(word.capitalize())
                    
            return " ".join(formatted_words)

    def apply_name_formatting(self):
        sender = self.sender()
        if sender:
            current_text = sender.text()
            formatted = self.format_proper_name(current_text)
            sender.blockSignals(True)
            sender.setText(formatted)
            sender.blockSignals(False)

    def format_cep(self, text):
        digits = "".join([c for c in text if c.isdigit()])[:8]
        formatted = ""
        if len(digits) > 5:
            formatted = f"{digits[:5]}-{digits[5:]}"
        else:
            formatted = digits

        self.zip_code_input.blockSignals(True)
        self.zip_code_input.setText(formatted)
        self.zip_code_input.blockSignals(False)

    def fetch_cep_address(self):
        import urllib.request
        import json

        cep_digits = "".join([c for c in self.zip_code_input.text() if c.isdigit()])
        if len(cep_digits) == 8:
            try:
                url = f"https://viacep.com.br/ws/{cep_digits}/json/"
                req = urllib.request.Request(url, headers={'User-Agent': 'VaultVetApp'})
                with urllib.request.urlopen(req, timeout=3) as response:
                    data = json.loads(response.read().decode())
                    if "erro" not in data:
                        logradouro = data.get("logradouro", "")
                        bairro = data.get("bairro", "")
                        cidade = data.get("localidade", "")
                        estado = data.get("uf", "")
                        
                        partes = [p for p in [logradouro, bairro, f"{cidade}/{estado}"] if p]
                        endereco_completo = ", ".join(partes)
                        self.address_input.setText(endereco_completo)
            except Exception as e:
                print("Não foi possível buscar o CEP:", e)

    def format_pet_name(self):
        text = self.pet_name_input.text().strip()
        if text:
            formatted = text[0].upper() + text[1:]
            self.pet_name_input.blockSignals(True)
            self.pet_name_input.setText(formatted)
            self.pet_name_input.blockSignals(False)

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