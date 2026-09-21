from datetime import datetime
import os
import shutil
import subprocess
import sys
from PyQt6.QtWidgets import (
    QWidget, QLineEdit, QFormLayout, QVBoxLayout, 
    QPushButton, QHBoxLayout, QGroupBox, QLabel, 
    QListWidget, QMessageBox, QComboBox, QDialog, QDialogButtonBox, QListWidgetItem, QTextBrowser, QFileDialog, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


class ClientDetailTab(QWidget):
    def __init__(self, parent=None, db=None, client_id=None, main_window=None, select_pet_id=None):
        super().__init__(parent)
        self.db = db
        self.client_id = client_id
        self.main_window = main_window
        self.select_pet_id = select_pet_id  # Guarda o ID do pet recebido
        
        self.current_selected_pet_id = None 
        self._is_loading = False 
        self._is_modified_flag = False  # Flag interna de alterações
        
        self.init_ui()
        self.load_client_data()
        self.load_pets_list()
        self.load_historico_cliente(None) # Carrega o histórico geral de todos os pets inicialmente
        self.load_vacinas_cliente(None)   # Carrega o histórico de vacinas geral inicialmente
        self.connect_change_trackers()

        # Lógica de seleção automática:
        if self.select_pet_id:
            # Se veio um ID específico de pet (ex: clicando direto em um pet), abre ele
            self.auto_select_pet(self.select_pet_id)
        elif self.pets_list_widget.count() > 0:
            # Se não veio nenhum específico, mas o tutor tem pets cadastrados, seleciona o 1º da lista!
            primeiro_item = self.pets_list_widget.item(0)
            pet_data = primeiro_item.data(Qt.ItemDataRole.UserRole)
            self.pets_list_widget.setCurrentItem(primeiro_item)
            self.load_pet_into_form(pet_data)

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
        self.delete_client_button.setStyleSheet("font-weight: bold;color: #c53030;")
        self.delete_client_button.clicked.connect(self.confirm_delete_client)

        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        top_layout.addWidget(self.save_client_button)
        top_layout.addWidget(self.delete_client_button)
        main_layout.addLayout(top_layout)

        # Layout dividido em TRÊS colunas (Esquerda | Meio | Direita)
        # Ajuste o stretch das colunas aqui se quiser mudar a largura geral delas
        content_layout = QHBoxLayout()

        # --- COLUNA ESQUERDA: Dados do Tutor + Histórico de Atendimentos ---
        left_container = QVBoxLayout()

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

        left_container.addWidget(tutor_group)

        # Bloco de Histórico de Atendimentos dos Pets
        self.group_historico_cliente = QGroupBox("Histórico de Atendimentos")
        self.group_historico_cliente.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #ccc; border-radius: 6px; margin-top: 4px; padding-top: 8px; }")
        
        hist_cliente_layout = QVBoxLayout(self.group_historico_cliente)
        self.txt_historico_cliente = QTextBrowser()
        self.txt_historico_cliente.setPlaceholderText("Nenhum atendimento registrado.")
        hist_cliente_layout.addWidget(self.txt_historico_cliente)

        btn_excluir_hist_layout = QHBoxLayout()
        self.btn_excluir_hist_cli = QPushButton("Excluir Atendimento por ID")
        self.btn_excluir_hist_cli.setStyleSheet("font-size: 11px; padding: 4px;")
        self.btn_excluir_hist_cli.clicked.connect(self.solicitar_exclusao_historico_por_id)
        btn_excluir_hist_layout.addWidget(self.btn_excluir_hist_cli)
        
        hist_cliente_layout.addLayout(btn_excluir_hist_layout)
        left_container.addWidget(self.group_historico_cliente)

        content_layout.addLayout(left_container, stretch=3)

        # --- COLUNA DO MEIO: Resumo + Exames + Vacinas ---
        self.middle_widget = QWidget()
        middle_layout = QVBoxLayout(self.middle_widget)
        middle_layout.setContentsMargins(4, 0, 4, 0)

        # 1. Bloco de Resumo / Pendências
        self.middle_group = QGroupBox("Resumo / Pendências")
        self.middle_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #ccc; border-radius: 6px; margin-top: 4px; padding-top: 8px; }")
        self.middle_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        middle_group_layout = QVBoxLayout(self.middle_group)
        self.txt_middle_info = QTextBrowser()
        self.txt_middle_info.setPlaceholderText("Informações centrais...")
        middle_group_layout.addWidget(self.txt_middle_info)
        middle_layout.addWidget(self.middle_group, stretch=35)

        # 2. Bloco de Resultados de Exames
        self.group_exames = QGroupBox("Resultados de Exames")
        self.group_exames.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #ccc; border-radius: 6px; margin-top: 4px; padding-top: 8px; }")
        self.group_exames.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        exames_layout = QVBoxLayout(self.group_exames)
        self.exames_list_widget = QListWidget()
        self.exames_list_widget.itemDoubleClicked.connect(self.abrir_exame_selecionado)
        exames_layout.addWidget(self.exames_list_widget)

        exames_btn_layout = QHBoxLayout()
        self.btn_anexar_exame = QPushButton("Anexar")
        self.btn_anexar_exame.setStyleSheet("font-size: 11px; padding: 4px;")
        self.btn_anexar_exame.clicked.connect(self.anexar_exame_pet)

        self.btn_remover_exame = QPushButton("Remover")
        self.btn_remover_exame.setStyleSheet("font-size: 11px; padding: 4px; color: #c53030;")
        self.btn_remover_exame.clicked.connect(self.remover_exame_pet)

        exames_btn_layout.addWidget(self.btn_anexar_exame)
        exames_btn_layout.addWidget(self.btn_remover_exame)
        exames_layout.addLayout(exames_btn_layout)
        
        middle_layout.addWidget(self.group_exames, stretch=35)

        # 3. Bloco de Controle e Histórico de Vacinas (Movido para cá!)
        self.group_vacinas_cliente = QGroupBox("Controle e Histórico de Vacinas")
        self.group_vacinas_cliente.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #ccc; border-radius: 6px; margin-top: 4px; padding-top: 8px; }")
        self.group_vacinas_cliente.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        vacinas_cliente_layout = QVBoxLayout(self.group_vacinas_cliente)
        self.txt_vacinas_cliente = QTextBrowser()
        self.txt_vacinas_cliente.setPlaceholderText("Nenhum registro de vacina encontrado.")
        vacinas_cliente_layout.addWidget(self.txt_vacinas_cliente)

        middle_layout.addWidget(self.group_vacinas_cliente, stretch=30)

        content_layout.addWidget(self.middle_widget, stretch=3)

        # --- COLUNA DIREITA: Lista de Pets + Ficha do Pet (Com a Foto no Topo) ---
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
        self.remove_pet_button.clicked.connect(self.confirm_delete_pet)

        pets_btn_layout.addWidget(self.add_pet_button)
        pets_btn_layout.addWidget(self.remove_pet_button)
        pets_layout.addLayout(pets_btn_layout)
        right_container.addWidget(pets_group)

        # Ficha do Pet (inicialmente oculta) - Contém a Foto no topo + formulário
        self.patient_group = QGroupBox("Ficha do Paciente (Pet)")
        patient_main_layout = QVBoxLayout(self.patient_group)

        # Layout da Foto dentro da Ficha
        foto_layout = QVBoxLayout()
        self.lbl_foto_pet = QLabel("Sem foto")
        self.lbl_foto_pet.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_foto_pet.setFixedSize(120, 120)
        self.lbl_foto_pet.setStyleSheet("border: 1px dashed #aaa; background-color: #f9f9f9; color: #666; border-radius: 4px;")
        
        botoes_foto_layout = QHBoxLayout()
        self.btn_carregar_foto = QPushButton("Carregar")
        self.btn_carregar_foto.setStyleSheet("font-size: 11px; padding: 4px;")
        self.btn_carregar_foto.clicked.connect(self.upload_pet_photo)

        self.btn_remover_foto = QPushButton("Remover")
        self.btn_remover_foto.setStyleSheet("font-size: 11px; padding: 4px; color: #c53030;")
        self.btn_remover_foto.clicked.connect(self.remove_pet_photo)

        botoes_foto_layout.addWidget(self.btn_carregar_foto)
        botoes_foto_layout.addWidget(self.btn_remover_foto)
        
        foto_layout.addWidget(self.lbl_foto_pet, alignment=Qt.AlignmentFlag.AlignCenter)
        foto_layout.addLayout(botoes_foto_layout)
        patient_main_layout.addLayout(foto_layout)

        # Campos do Formulário do Pet
        patient_form_layout = QFormLayout()

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

        patient_form_layout.addRow("Nome do Pet:", self.pet_name_input)
        patient_form_layout.addRow("Espécie:", self.species_input)
        patient_form_layout.addRow("Raça:", self.breed_input)
        patient_form_layout.addRow("Sexo:", self.gender_input)
        patient_form_layout.addRow("Castrado:", self.neutered_input)
        patient_form_layout.addRow("Nascimento:", self.birth_date_input)
        patient_form_layout.addRow("Idade:", self.age_input)
        patient_form_layout.addRow("Peso (kg):", self.weight_input)
        patient_form_layout.addRow("Microchip:", self.microchip_input)

        patient_main_layout.addLayout(patient_form_layout)

        self.save_pet_button = QPushButton("Salvar Alterações / Cadastrar Pet")
        self.save_pet_button.setStyleSheet("font-weight: bold; padding: 6px;")
        
        try:
            self.save_pet_button.clicked.disconnect()
        except TypeError:
            pass
            
        self.save_pet_button.clicked.connect(self.save_pet_data)
        patient_main_layout.addWidget(self.save_pet_button)
        
        right_container.addWidget(self.patient_group)
        self.patient_group.hide()

        content_layout.addLayout(right_container, stretch=3)
        main_layout.addLayout(content_layout)

    # --- FUNÇÕES DE EXAMES ---
    def anexar_exame_pet(self):
        if not self.current_selected_pet_id:
            QMessageBox.warning(self, "Aviso", "Selecione ou clique em um pet na lista primeiro para anexar exames.")
            return

        file_name, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Resultado de Exame", "", 
            "Documentos e Imagens (*.pdf *.png *.jpg *.jpeg)"
        )
        if file_name:
            try:
                os.makedirs("pet_exams", exist_ok=True)
                base_name = os.path.basename(file_name)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_unico = f"pet_{self.current_selected_pet_id}_{timestamp}_{base_name}"
                dest_path = os.path.join("pet_exams", nome_unico)
                
                shutil.copy(file_name, dest_path)

                self.db.cursor.execute(
                    "INSERT INTO pet_exams (pet_id, file_name, file_path) VALUES (?, ?, ?)", 
                    (self.current_selected_pet_id, base_name, dest_path)
                )
                self.db.conn.commit()

                self.load_exames_pet(self.current_selected_pet_id)
                QMessageBox.information(self, "Sucesso", "Exame anexado com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível salvar o exame: {e}")

    def load_exames_pet(self, pet_id):
        self.exames_list_widget.clear()
        if not self.db or not pet_id:
            return

        try:
            self.db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS pet_exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pet_id INTEGER,
                    file_name TEXT,
                    file_path TEXT,
                    FOREIGN KEY(pet_id) REFERENCES patients(id) ON DELETE CASCADE
                )
            """)
            self.db.conn.commit()

            self.db.cursor.execute("SELECT id, file_name, file_path FROM pet_exams WHERE pet_id = ?", (pet_id,))
            registros = self.db.cursor.fetchall()

            for exam_id, file_name, file_path in registros:
                item = QListWidgetItem(f"📄 {file_name}")
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                self.exames_list_widget.addItem(item)
        except Exception as e:
            print(f"Erro ao carregar exames: {e}")

    def abrir_exame_selecionado(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path and os.path.exists(file_path):
            try:
                if sys.platform == "win32":
                    os.startfile(file_path)
                elif sys.platform == "darwin":
                    subprocess.run(["open", file_path])
                else:
                    subprocess.run(["xdg-open", file_path])
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível abrir o arquivo: {e}")
        else:
            QMessageBox.warning(self, "Aviso", "O arquivo físico não foi encontrado na pasta.")

    def remover_exame_pet(self):
        selected_item = self.exames_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Aviso", "Selecione um exame na lista para remover.")
            return

        file_path = selected_item.data(Qt.ItemDataRole.UserRole)

        resposta = QMessageBox.question(
            self, "Remover Exame", "Deseja realmente remover este exame do prontuário?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if resposta == QMessageBox.StandardButton.Yes:
            try:
                self.db.cursor.execute("DELETE FROM pet_exams WHERE file_path = ?", (file_path,))
                self.db.conn.commit()

                if os.path.exists(file_path):
                    os.remove(file_path)

                self.load_exames_pet(self.current_selected_pet_id)
                QMessageBox.information(self, "Sucesso", "Exame removido com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível remover o exame: {e}")

    # --- FUNÇÕES DE FOTO DO PET ---
    def upload_pet_photo(self):
        if not self.current_selected_pet_id:
            QMessageBox.warning(self, "Aviso", "Selecione ou clique em um pet na lista primeiro para adicionar a foto.")
            return

        file_name, _ = QFileDialog.getOpenFileName(self, "Selecionar Foto do Pet", "", "Imagens (*.png *.jpg *.jpeg)")
        if file_name:
            try:
                os.makedirs("pet_photos", exist_ok=True)
                ext = os.path.splitext(file_name)[1]
                dest_path = f"pet_photos/pet_{self.current_selected_pet_id}{ext}"
                
                shutil.copy(file_name, dest_path)

                self.db.cursor.execute("UPDATE patients SET photo_path = ? WHERE id = ?", (dest_path, self.current_selected_pet_id))
                self.db.conn.commit()

                self.display_pet_photo(dest_path)
                QMessageBox.information(self, "Sucesso", "Foto do pet atualizada com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível salvar a foto: {e}")

    def remove_pet_photo(self):
        if not self.current_selected_pet_id:
            QMessageBox.warning(self, "Aviso", "Nenhum pet selecionado.")
            return

        resposta = QMessageBox.question(
            self, "Remover Foto", "Deseja realmente remover a foto deste paciente?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if resposta == QMessageBox.StandardButton.Yes:
            try:
                self.db.cursor.execute("UPDATE patients SET photo_path = NULL WHERE id = ?", (self.current_selected_pet_id,))
                self.db.conn.commit()

                self.display_pet_photo(None)
                QMessageBox.information(self, "Sucesso", "Foto removida com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível remover a foto: {e}")

    def display_pet_photo(self, path_or_none):
        if path_or_none and os.path.exists(path_or_none):
            pixmap = QPixmap(path_or_none)
            scaled_pixmap = pixmap.scaled(self.lbl_foto_pet.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_foto_pet.setPixmap(scaled_pixmap)
        else:
            self.lbl_foto_pet.clear()
            self.lbl_foto_pet.setText("Sem foto")

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

    def load_historico_cliente(self, pet_id=None):
        if not self.db or not self.client_id:
            return

        try:
            if pet_id:
                query = """
                    SELECT ch.id, ch.date, ch.notes, p.pet_name 
                    FROM consultation_history ch
                    JOIN patients p ON ch.pet_id = p.id
                    WHERE ch.client_id = ? AND ch.pet_id = ?
                    ORDER BY ch.date DESC, ch.id DESC
                """
                self.db.cursor.execute(query, (self.client_id, pet_id))
            else:
                query = """
                    SELECT ch.id, ch.date, ch.notes, p.pet_name 
                    FROM consultation_history ch
                    JOIN patients p ON ch.pet_id = p.id
                    WHERE ch.client_id = ?
                    ORDER BY ch.date DESC, ch.id DESC
                """
                self.db.cursor.execute(query, (self.client_id,))
                
            registros = self.db.cursor.fetchall()

            if registros:
                html_content = ""
                for hist_id, data_atend, notes, pet_name in registros:
                    partes_data = data_atend.split("-")
                    if len(partes_data) == 3:
                        data_formatada = f"{partes_data[2]}/{partes_data[1]}/{partes_data[0]}"
                    else:
                        data_formatada = data_atend

                    html_content += f"<b>{data_formatada} — Pet: {pet_name}</b><br>{notes.replace('\n', '<br>')}<br><span style='color: #888; font-size: 10px;'>ID: #{hist_id}</span><br><br>"
                
                self.txt_historico_cliente.setHtml(html_content.strip())
            else:
                self.txt_historico_cliente.setHtml("<i>Nenhum atendimento registrado para este filtro.</i>")
        except Exception as e:
            print(f"Erro ao carregar histórico: {e}")
            self.txt_historico_cliente.setHtml("<i>Erro ao carregar histórico.</i>")

    def load_vacinas_cliente(self, pet_id=None):
        if not self.db or not self.client_id:
            return

        try:
            vacinas_caninas = [
                "V8 (Múltipla)", "V10 (Múltipla)", "Antirrábica", 
                "Giárdia", "Gripe Canina (Traqueobronquite)", "Leishmaniose"
            ]
            
            vacinas_felinas = [
                "V3 (Tríplice Felina)", "V4 (Quádrupla Felina)", "V5 (Quíntupla Felina)", 
                "Antirrábica", "FeLV (Leucemia Felina)"
            ]

            if pet_id:
                self.db.cursor.execute("SELECT pet_name, species FROM patients WHERE id = ?", (pet_id,))
                res_pet = self.db.cursor.fetchone()
                
                if not res_pet:
                    self.txt_vacinas_cliente.setHtml("<i>Pet não encontrado.</i>")
                    return

                nome_pet, especie_pet = res_pet
                
                if especie_pet and especie_pet.lower() in ["felino", "gato"]:
                    vacinas_padrao = vacinas_felinas
                    tipo_esp = "Felino"
                else:
                    vacinas_padrao = vacinas_caninas
                    tipo_esp = "Canino"

                query = """
                    SELECT vaccine_name, application_date, next_due_date 
                    FROM pet_vaccines 
                    WHERE pet_id = ?
                """
                self.db.cursor.execute(query, (pet_id,))
                registros_aplicados = {row[0]: (row[1], row[2]) for row in self.db.cursor.fetchall()}

                html_content = f"""
                    <b style="font-size: 12px; color: #333;">Paciente: {nome_pet} ({tipo_esp})</b>
                    <table width="100%" cellspacing="0" cellpadding="4" style="font-size: 11px; margin-top: 5px;">
                        <tr style="font-weight: bold;">
                            <td>Vacina</td>
                            <td>Última Aplicação</td>
                            <td>Próxima Dose (Reforço)</td>
                        </tr>
                """

                for vac in vacinas_padrao:
                    vac_encontrada = None
                    for v_cad in registros_aplicados:
                        if vac.lower() in v_cad.lower() or v_cad.lower() in vac.lower():
                            vac_encontrada = v_cad
                            break

                    if vac_encontrada:
                        app_date, due_date = registros_aplicados[vac_encontrada]
                        app_fmt = f"{app_date.split('-')[2]}/{app_date.split('-')[1]}/{app_date.split('-')[0]}" if len(str(app_date)) == 10 and '-' in app_date else app_date
                        due_fmt = f"{due_date.split('-')[2]}/{due_date.split('-')[1]}/{due_date.split('-')[0]}" if len(str(due_date)) == 10 and '-' in due_date else due_date
                        
                        html_content += f"""
                            <tr>
                                <td><b>{vac}</b></td>
                                <td>{app_fmt}</td>
                                <td><span style="color: #ffbf00; font-weight: bold;">{due_fmt}</span></td>
                            </tr>
                        """
                    else:
                        html_content += f"""
                            <tr>
                                <td><b>{vac}</b></td>
                                <td colspan="2" style="color: #888; font-style: italic;">Não aplicada / Sem registro</td>
                            </tr>
                        """
                html_content += "</table>"
                self.txt_vacinas_cliente.setHtml(html_content)

            else:
                query = """
                    p.pet_name, p.species, v.vaccine_name, v.application_date, v.next_due_date 
                    FROM patients p
                    LEFT JOIN pet_vaccines v ON p.id = v.pet_id
                    WHERE p.client_id = ?
                    ORDER BY p.pet_name ASC
                """
                self.db.cursor.execute(f"SELECT {query}", (self.client_id,))
                registros = self.db.cursor.fetchall()

                if registros and any(r[2] is not None for r in registros):
                    html_content = """
                        <table width="100%" cellspacing="0" cellpadding="4" style="font-size: 11px;">
                            <tr style="background-color: #f2f2f2; font-weight: bold;">
                                <td>Pet (Espécie)</td>
                                <td>Vacina</td>
                                <td>Aplicada em</td>
                                <td>Próxima Dose</td>
                            </tr>
                    """
                    for pet_name, especie, vac_name, app_date, due_date in registros:
                        if not vac_name:
                            continue
                        app_fmt = f"{app_date.split('-')[2]}/{app_date.split('-')[1]}/{app_date.split('-')[0]}" if len(str(app_date)) == 10 and '-' in app_date else app_date
                        due_fmt = f"{due_date.split('-')[2]}/{due_date.split('-')[1]}/{due_date.split('-')[0]}" if len(str(due_date)) == 10 and '-' in due_date else due_date

                        html_content += f"""
                            <tr>
                                <td><b>{pet_name}</b> ({especie})</td>
                                <td>{vac_name}</td>
                                <td>{app_fmt}</td>
                                <td><span style="color: #d97706; font-weight: bold;">{due_fmt}</span></td>
                            </tr>
                        """
                    html_content += "</table>"
                    self.txt_vacinas_cliente.setHtml(html_content)
                else:
                    self.txt_vacinas_cliente.setHtml("<i>Nenhum registro de vacina encontrado para os pets deste cliente.</i>")

        except Exception as e:
            print(f"Erro ao carregar vacinas do cliente: {e}")
            self.txt_vacinas_cliente.setHtml("<i>Erro ao carregar histórico de vacinas.</i>")

    def solicitar_exclusao_historico_por_id(self):
        from PyQt6.QtWidgets import QInputDialog
        id_str, ok = QInputDialog.getText(self, "Excluir Atendimento", "Digite o número do ID do atendimento que deseja apagar (ex: 12):")
        
        if ok and id_str.strip():
            try:
                id_limpo = id_str.replace("#", "").strip()
                hist_id = int(id_limpo)

                resposta = QMessageBox.question(
                    self, "Confirmação", f"Deseja realmente excluir permanentemente o atendimento ID #{hist_id}?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if resposta == QMessageBox.StandardButton.Yes:
                    self.db.deletar_historico_por_id(hist_id)
                    QMessageBox.information(self, "Sucesso", f"Atendimento ID #{hist_id} removido com sucesso!")
                    self.load_historico_cliente(self.current_selected_pet_id)
            except ValueError:
                QMessageBox.warning(self, "Erro", "Por favor, digite apenas números válidos para o ID.")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir histórico: {e}")

    def auto_select_pet(self, pet_id):
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

            self._is_modified_flag = False
            self.load_pets_list()
            self.load_historico_cliente(self.current_selected_pet_id)
            self.load_vacinas_cliente(self.current_selected_pet_id)
            
            if hasattr(self.main_window, "client_list_ui"):
                self.main_window.client_list_ui.load_data()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar o pet: {e}")

    def connect_change_trackers(self):
        tutor_inputs = [
            self.first_name_input, self.last_name_input, self.zip_code_input,
            self.address_input, self.number_input, self.complement_input,
            self.phone_input, self.email_input, self.emergency_name_input,
            self.emergency_phone_input, self.cpf_input, self.rg_input
        ]
        for field in tutor_inputs:
            field.textChanged.connect(self.mark_as_modified)

        self.pet_name_input.textChanged.connect(self.mark_as_modified)
        self.species_input.currentIndexChanged.connect(self.mark_as_modified)
        self.breed_input.currentIndexChanged.connect(self.mark_as_modified)
        self.gender_input.currentIndexChanged.connect(self.mark_as_modified)
        self.neutered_input.currentIndexChanged.connect(self.mark_as_modified)
        self.birth_date_input.textChanged.connect(self.mark_as_modified)
        self.age_input.textChanged.connect(self.mark_as_modified)
        self.weight_input.textChanged.connect(self.mark_as_modified)
        self.microchip_input.textChanged.connect(self.mark_as_modified)

    def mark_as_modified(self):
        if not self._is_loading:
            self._is_modified_flag = True

    def has_unsaved_changes(self):
        return self._is_modified_flag

    def check_unsaved_changes(self):
        if self.has_unsaved_changes():
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
        
        # --- CARREGA A FOTO E OS EXAMES DO PET DO BANCO ---
        self.db.cursor.execute("SELECT photo_path FROM patients WHERE id = ?", (pet[0],))
        res_foto = self.db.cursor.fetchone()
        caminho_foto = res_foto[0] if res_foto else None
        self.display_pet_photo(caminho_foto)

        self.load_exames_pet(pet[0])

        self._is_modified_flag = False
        self._is_loading = False
        self.patient_group.show()

        self.load_historico_cliente(pet[0])
        self.load_vacinas_cliente(pet[0])

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
        
        self.display_pet_photo(None) # Limpa a foto
        self.exames_list_widget.clear() # Limpa a lista de exames

        self._is_modified_flag = False
        self._is_loading = False
        self.patient_group.show()

        self.load_historico_cliente(None)
        self.load_vacinas_cliente(None)

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
            
            self._is_modified_flag = False  
            
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
                self.load_historico_cliente(None)
                self.load_vacinas_cliente(None)
                self.display_pet_photo(None)
                self.exames_list_widget.clear()
                if hasattr(self.main_window, "client_list_ui"):
                    self.main_window.client_list_ui.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível remover o pet: {e}")