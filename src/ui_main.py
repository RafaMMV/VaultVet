from PyQt6.QtWidgets import (
    QWidget, QLineEdit, QComboBox, 
    QFormLayout, QVBoxLayout, QPushButton, QHBoxLayout, QGroupBox
)

class MainUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
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

        client_layout.addRow("Nome:", self.first_name_input)
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
        self.species_input = QComboBox()
        self.species_input.addItems(["Canino", "Felino", "Reptil", "Ave", "Outro"])
        self.breed_input = QLineEdit()
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

        self.save_button = QPushButton("Salvar Cadastro")
        self.save_button.setStyleSheet("font-weight: bold; padding: 8px;")

        left_side = QVBoxLayout()
        left_side.addWidget(client_group)

        right_side = QVBoxLayout()
        right_side.addWidget(patient_group)
        right_side.addWidget(self.save_button)

        main_layout.addLayout(left_side)
        main_layout.addLayout(right_side)

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
        self.birth_date_input.blockSignals(False)

    def format_proper_name(self, text):
        """Formata o nome com iniciais maiúsculas, exceto preposições curtas."""
        exceptions = {'de', 'da', 'do', 'dos', 'das', 'di', 'du', 'e'}
        words = text.strip().split()
        formatted_words = []
        for i, word in enumerate(words):
            w_lower = word.lower()
            if i > 0 and w_lower in exceptions:
                formatted_words.append(w_lower)
            else:
                formatted_words.append(word.capitalize())
        return " ".join(formatted_words)

    def apply_name_formatting(self):
        """Aplica a formatação de nomes quando o usuário termina de digitar."""
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
        """Busca o endereço automaticamente usando a API pública do ViaCEP."""
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
                        # Preenche o campo de endereço automaticamente
                        logradouro = data.get("logradouro", "")
                        bairro = data.get("bairro", "")
                        estado = data.get("uf", "")
                        if bairro:
                            self.address_input.setText(f"{logradouro} - {bairro}/{estado}")
                        else:
                            self.address_input.setText(logradouro)
            except Exception as e:
                print("Não foi possível buscar o CEP:", e)