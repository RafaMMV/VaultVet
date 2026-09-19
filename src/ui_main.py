from PyQt6.QtWidgets import (
    QMainWindow, QTabBar, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QMessageBox, QListWidget, QListWidgetItem, QPushButton, QDateEdit, 
    QGroupBox, QFormLayout, QTextEdit, QTextBrowser
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QIcon
from ui_client_list import ClientListUI
from ui_agenda import AgendaTab, AgendaItemWidget

class AgendaTableWidget(QWidget):
    """Widget com histórico inteligente, exibição de IDs e botão para excluir atendimento diretamente."""
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.current_pet_id = None
        self.current_client_id = None
        self.current_historico_id = None
        self.current_service_type = "Consulta"
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # ================= COLUNA 1 (ESQUERDA): FICHA + HISTÓRICOS + EXCLUSÃO =================
        left_layout = QVBoxLayout()
        
        self.group_detalhes = QGroupBox("Informações do Paciente")
        self.group_detalhes.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #ccc; border-radius: 6px; margin-top: 4px; padding-top: 8px; }")
        
        form_detalhes = QFormLayout(self.group_detalhes)
        form_detalhes.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.lbl_det_cliente = QLabel("-")
        self.lbl_det_pet = QLabel("-")
        self.lbl_det_raca = QLabel("-")
        self.lbl_det_nascimento = QLabel("-")
        self.lbl_det_idade = QLabel("-")
        self.lbl_det_peso = QLabel("-")

        for lbl in [self.lbl_det_cliente, self.lbl_det_pet, self.lbl_det_raca, self.lbl_det_nascimento, self.lbl_det_idade, self.lbl_det_peso]:
            lbl.setStyleSheet("font-weight: normal; font-size: 12px;")

        form_detalhes.addRow("<b>Cliente:</b>", self.lbl_det_cliente)
        form_detalhes.addRow("<b>Pet:</b>", self.lbl_det_pet)
        form_detalhes.addRow("<b>Raça:</b>", self.lbl_det_raca)
        form_detalhes.addRow("<b>Nascimento:</b>", self.lbl_det_nascimento)
        form_detalhes.addRow("<b>Idade:</b>", self.lbl_det_idade)
        form_detalhes.addRow("<b>Peso:</b>", self.lbl_det_peso)

        left_layout.addWidget(self.group_detalhes)

        # Histórico Dinâmico mostrando as duas últimas datas anteriores com os IDs
        self.group_historico = QGroupBox("Histórico de Atendimentos")
        self.group_historico.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #ccc; border-radius: 6px; margin-top: 4px; padding-top: 8px; }")
        
        historico_layout = QVBoxLayout(self.group_historico)
        self.txt_historico = QTextBrowser()
        self.txt_historico.setPlaceholderText("Nenhum atendimento anterior a esta data.")
        historico_layout.addWidget(self.txt_historico)

        # Botão discreto para apagar um histórico informado pelo ID no canto esquerdo
        excluir_hist_layout = QHBoxLayout()
        self.btn_excluir_historico = QPushButton("Excluir Atendimento por ID")
        self.btn_excluir_historico.setStyleSheet("font-weight: bold; font-size: 11px; padding: 4px;")
        self.btn_excluir_historico.clicked.connect(self.solicitar_exclusao_historico_por_id)
        excluir_hist_layout.addWidget(self.btn_excluir_historico)
        
        historico_layout.addLayout(excluir_hist_layout)
        left_layout.addWidget(self.group_historico)
        main_layout.addLayout(left_layout, stretch=2)

        # ================= COLUNA 2 (CENTRO): RESUMO DO ATENDIMENTO DO DIA =================
        center_layout = QVBoxLayout()
        
        self.group_atendimento = QGroupBox("Resumo do Atendimento do Dia")
        self.group_atendimento.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #ccc; border-radius: 6px; margin-top: 4px; padding-top: 8px; }")
        
        atendimento_layout = QVBoxLayout(self.group_atendimento)
        self.txt_atendimento = QTextEdit()
        self.txt_atendimento.setPlaceholderText("Digite o resumo ou deixe em branco para salvar o serviço automático...")
        atendimento_layout.addWidget(self.txt_atendimento)

        self.btn_salvar_atendimento = QPushButton("Salvar Atendimento")
        self.btn_salvar_atendimento.setStyleSheet("font-weight: bold; padding: 6px;")
        self.btn_salvar_atendimento.clicked.connect(self.salvar_ou_atualizar_atendimento)
        atendimento_layout.addWidget(self.btn_salvar_atendimento)

        center_layout.addWidget(self.group_atendimento)
        main_layout.addLayout(center_layout, stretch=2)

        # ================= COLUNA 3 (DIREITA): LISTA DE HORÁRIOS DO DIA =================
        right_layout = QVBoxLayout()
        
        self.lbl_titulo = QLabel("<b>Agendamentos</b>")
        self.lbl_titulo.setStyleSheet("font-size: 14px; font-weight: bold;")
        right_layout.addWidget(self.lbl_titulo)
        
        date_control_layout = QHBoxLayout()
        date_control_layout.addWidget(QLabel("Data:"))
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.dateChanged.connect(self.carregar_horarios)
        date_control_layout.addWidget(self.date_edit)

        self.btn_hoje = QPushButton("Hoje")
        self.btn_hoje.clicked.connect(lambda: self.date_edit.setDate(QDate.currentDate()))
        date_control_layout.addWidget(self.btn_hoje)
        
        date_control_layout.addStretch()
        right_layout.addLayout(date_control_layout)

        self.lista_horarios = QListWidget()
        self.lista_horarios.itemClicked.connect(self.ao_clicar_horario)
        self.lista_horarios.currentItemChanged.connect(lambda current, previous: self.ao_clicar_horario(current))
        right_layout.addWidget(self.lista_horarios)

        main_layout.addLayout(right_layout, stretch=2)
        self.carregar_horarios()

    def showEvent(self, event):
        super().showEvent(event)
        self.carregar_horarios()

    def carregar_horarios(self):
        self.lista_horarios.clear()
        self.limpar_detalhes()
        
        if not self.db:
            return

        try:
            data_selecionada = self.date_edit.date()
            data_str = data_selecionada.toString("yyyy-MM-dd")
            
            self.lbl_titulo.setText(f"<b>Agendamentos de {data_selecionada.toString('dd/MM/yyyy')}</b>")

            self.db.cursor.execute(
                "SELECT id, time, client_name, pet_name, service_type FROM appointments WHERE date = ? ORDER BY time ASC", 
                (data_str,)
            )
            registros = self.db.cursor.fetchall()
            
            for reg_id, hora, client, pet, service in registros:
                item = QListWidgetItem(self.lista_horarios)
                item.setData(Qt.ItemDataRole.UserRole, reg_id)
                
                widget_item = AgendaItemWidget(reg_id, hora, client, pet, service, self)
                item.setSizeHint(widget_item.sizeHint())
                
                self.lista_horarios.addItem(item)
                self.lista_horarios.setItemWidget(item, widget_item)

            if registros:
                self.lista_horarios.setCurrentRow(0)
                
        except Exception as e:
            print(f"Erro ao carregar tabela de horários: {e}")

    def ao_clicar_horario(self, item):
        if not item or not self.db:
            return

        reg_id = item.data(Qt.ItemDataRole.UserRole)
        if not reg_id:
            return

        try:
            self.db.cursor.execute(
                "SELECT client_name, pet_name, service_type FROM appointments WHERE id = ?", (reg_id,)
            )
            appt = self.db.cursor.fetchone()
            if not appt:
                return

            client_name_str, pet_name_str, service_type = appt
            self.current_service_type = service_type

            query = """
                SELECT 
                    c.id,
                    p.id,
                    c.first_name || ' ' || COALESCE(c.last_name, ''),
                    p.pet_name,
                    p.breed,
                    p.birth_date,
                    p.age,
                    p.weight
                FROM clients c
                JOIN patients p ON c.id = p.client_id
                WHERE (c.first_name || ' ' || COALESCE(c.last_name, '')) LIKE ? AND p.pet_name LIKE ?
            """
            self.db.cursor.execute(query, (f"%{client_name_str.strip()}%", f"%{pet_name_str.strip()}%"))
            resultado = self.db.cursor.fetchone()

            if not resultado:
                self.db.cursor.execute("""
                    SELECT 
                        c.id,
                        p.id,
                        c.first_name || ' ' || COALESCE(c.last_name, ''),
                        p.pet_name,
                        p.breed,
                        p.birth_date,
                        p.age,
                        p.weight
                    FROM clients c
                    JOIN patients p ON c.id = p.client_id
                    WHERE p.pet_name LIKE ?
                """, (f"%{pet_name_str.strip()}%",))
                resultado = self.db.cursor.fetchone()

            if resultado:
                c_id, p_id, cliente, pet, raca, nasc, idade, peso = resultado
                self.current_client_id = c_id
                self.current_pet_id = p_id

                self.lbl_det_cliente.setText(cliente.strip() or "-")
                self.lbl_det_pet.setText(pet or "-")
                self.lbl_det_raca.setText(raca or "-")
                self.lbl_det_nascimento.setText(nasc or "-")
                self.lbl_det_idade.setText(str(idade) if idade is not None and str(idade).strip() != "" else "-")
                
                peso_str = f"{peso} kg" if peso is not None and str(peso).strip() != "" else "-"
                self.lbl_det_peso.setText(peso_str)

                self.atualizar_paineis_atendimento(p_id)
            else:
                self.limpar_detalhes()

        except Exception as e:
            print(f"Erro ao buscar detalhes do paciente: {e}")
            self.limpar_detalhes()

    def atualizar_paineis_atendimento(self, pet_id):
        """Atualiza a caixa de histórico exibindo as duas últimas consultas e seus IDs."""
        data_selecionada_str = self.date_edit.date().toString("yyyy-MM-dd")

        try:
            self.db.cursor.execute("""
                SELECT id, date, notes FROM consultation_history 
                WHERE pet_id = ? AND date < ? 
                ORDER BY date DESC, id DESC 
                LIMIT 2
            """, (pet_id, data_selecionada_str))
            historicos = self.db.cursor.fetchall()

            if historicos:
                html_content = ""
                for hist_id, data_ant, notes_ant in historicos:
                    partes_data = data_ant.split("-")
                    if len(partes_data) == 3:
                        data_formatada = f"{partes_data[2]}/{partes_data[1]}/{partes_data[0]}"
                    else:
                        data_formatada = data_ant

                    html_content += f"<b>{data_formatada}</b><br>{notes_ant.replace('\n', '<br>')}<br><span style=; font-size: 10px;'>ID: #{hist_id}</span><br><br>"
                
                self.txt_historico.setHtml(html_content.strip())
            else:
                self.txt_historico.setHtml("<i>Nenhum atendimento anterior a esta data.</i>")
        except Exception as e:
            print(f"Erro ao buscar históricos anteriores: {e}")
            self.txt_historico.setHtml("<i>Erro ao carregar histórico.</i>")

        resumo_do_dia = self.db.get_historico_do_dia(pet_id, data_selecionada_str)
        if resumo_do_dia:
            self.current_historico_id, texto_salvo = resumo_do_dia
            self.txt_atendimento.setText(texto_salvo)
            self.btn_salvar_atendimento.setText("Atualizar Atendimento")
        else:
            self.current_historico_id = None
            self.txt_atendimento.clear()
            self.btn_salvar_atendimento.setText("Salvar Atendimento")

    def solicitar_exclusao_historico_por_id(self):
        """Abre uma caixinha solicitando o número do ID que deseja apagar."""
        if not self.current_pet_id:
            QMessageBox.warning(self, "Aviso", "Selecione um paciente primeiro.")
            return

        from PyQt6.QtWidgets import QInputDialog
        id_str, ok = QInputDialog.getText(self, "Excluir Atendimento", "Digite o número do ID que deseja apagar (ex: 12):")
        
        if ok and id_str.strip():
            try:
                # Remove o prefixo '#' caso a pessoa tenha digitado junto
                id_limpo = id_str.replace("#", "").strip()
                hist_id = int(id_limpo)

                resposta = QMessageBox.question(
                    self, "Confirmação", f"Deseja realmente excluir permanentemente o atendimento ID #{hist_id}?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if resposta == QMessageBox.StandardButton.Yes:
                    self.db.deletar_historico_por_id(hist_id)
                    QMessageBox.information(self, "Sucesso", f"Atendimento ID #{hist_id} removido com sucesso!")
                    self.atualizar_paineis_atendimento(self.current_pet_id)
            except ValueError:
                QMessageBox.warning(self, "Erro", "Por favor, digite apenas números válidos para o ID.")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir histórico: {e}")

    def salvar_ou_atualizar_atendimento(self):
        if not self.current_pet_id or not self.current_client_id:
            QMessageBox.warning(self, "Aviso", "Selecione um agendamento válido.")
            return

        texto = self.txt_atendimento.toPlainText().strip()
        data_str = self.date_edit.date().toString("yyyy-MM-dd")
        
        if not texto:
            texto = f"- {self.current_service_type}"
        
        try:
            if self.current_historico_id:
                self.db.atualizar_historico(self.current_historico_id, texto)
                QMessageBox.information(self, "Sucesso", "Atendimento atualizado com sucesso!")
            else:
                self.db.salvar_historico(self.current_pet_id, self.current_client_id, data_str, texto)
                QMessageBox.information(self, "Sucesso", "Atendimento salvo com sucesso!")

            self.atualizar_paineis_atendimento(self.current_pet_id)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")

    def limpar_detalhes(self):
        self.current_pet_id = None
        self.current_client_id = None
        self.current_historico_id = None
        self.current_service_type = "Consulta"
        self.lbl_det_cliente.setText("-")
        self.lbl_det_pet.setText("-")
        self.lbl_det_raca.setText("-")
        self.lbl_det_nascimento.setText("-")
        self.lbl_det_idade.setText("-")
        self.lbl_det_peso.setText("-")
        self.txt_atendimento.clear()
        self.txt_historico.clear()
        self.btn_salvar_atendimento.setText("Salvar Atendimento")

    def preparar_edicao(self, reg_id):
        parent_main = self.window()
        if hasattr(parent_main, "agenda_tab"):
            parent_main.agenda_tab.preparar_edicao(reg_id)
            parent_main.tabs.setCurrentWidget(parent_main.agenda_tab)

    def excluir_horario(self, reg_id):
        resposta = QMessageBox.question(
            self, "Confirmação", "Deseja realmente excluir este agendamento?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if resposta == QMessageBox.StandardButton.Yes:
            try:
                self.db.cursor.execute("DELETE FROM appointments WHERE id = ?", (reg_id,))
                self.db.conn.commit()
                QMessageBox.information(self, "Sucesso", "Agendamento excluído!")
                self.carregar_horarios()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir: {e}")

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
        self.tabs.currentChanged.connect(self.ao_mudar_aba)

        self.home_tab = AgendaTableWidget(parent=self, db=self.db)
        self.client_list_ui = ClientListUI(parent=self, db=self.db)
        self.agenda_tab = AgendaTab(parent=self, db=self.db)

        self.inventory_tab = QWidget()  
        inventory_layout = QVBoxLayout(self.inventory_tab)
        inventory_layout.addWidget(QLabel("Estoque - Em desenvolvimento"))

        self.cash_flow_tab = QWidget()
        cash_flow_layout = QVBoxLayout(self.cash_flow_tab)
        cash_flow_layout.addWidget(QLabel("Caixa - Em desenvolvimento"))

        self.tabs.addTab(self.home_tab, "Início")
        self.tabs.addTab(self.client_list_ui, "Clientes")
        self.tabs.addTab(self.agenda_tab, "Agendamento")  
        self.tabs.addTab(self.inventory_tab, "Estoque")
        self.tabs.addTab(self.cash_flow_tab, "Caixa") 

        for i in range(5):
            self.tabs.tabBar().setTabButton(i, QTabBar.ButtonPosition.RightSide, None)

        self.client_list_ui.load_data()

    def ao_mudar_aba(self, index):
        widget_atual = self.tabs.widget(index)
        if widget_atual == self.agenda_tab:
            self.agenda_tab.carregar_dados_clientes()

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        if widget in [self.home_tab, self.client_list_ui, self.agenda_tab, self.inventory_tab, self.cash_flow_tab]:
            return
        self.tabs.removeTab(index)
        widget.deleteLater()