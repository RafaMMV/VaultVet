from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QCalendarWidget, 
    QListWidget, QPushButton, QLabel, QMessageBox, 
    QListWidgetItem, QMenu, QComboBox, QCompleter
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QAction, QKeyEvent, QTextCharFormat, QColor

class AgendaItemWidget(QWidget):
    """Widget personalizado para cada linha da lista, exibindo o nome limpo e o menu de três pontinhos."""
    def __init__(self, reg_id, hora, client, pet, service, parent_agenda):
        super().__init__()
        self.reg_id = reg_id
        self.parent_agenda = parent_agenda

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        partes_nome = client.split()
        if len(partes_nome) >= 2:
            nome_limpo = f"{partes_nome[0]} {partes_nome[1]}"
        else:
            nome_limpo = client

        texto_formatado = f"<b>{hora}</b> — {nome_limpo} - {pet} ({service})"
        self.lbl_info = QLabel(texto_formatado)
        layout.addWidget(self.lbl_info)

        layout.addStretch()

        self.btn_menu = QPushButton("⋮")
        self.btn_menu.setFixedSize(30, 25)
        self.btn_menu.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.menu = QMenu(self)
        acao_editar = QAction("Editar", self)
        acao_editar.triggered.connect(self.chamar_edicao)
        acao_excluir = QAction("Excluir", self)
        acao_excluir.triggered.connect(self.chamar_exclusao)
        
        self.menu.addAction(acao_editar)
        self.menu.addAction(acao_excluir)
        self.btn_menu.setMenu(self.menu)
        layout.addWidget(self.btn_menu)

    def chamar_edicao(self):
        self.parent_agenda.preparar_edicao(self.reg_id)

    def chamar_exclusao(self):
        self.parent_agenda.excluir_horario(self.reg_id)


class AutoCompleteComboBox(QComboBox):
    """ComboBox personalizado que força a seleção da primeira sugestão ao apertar Tab ou sair do campo."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            completer = self.completer()
            if completer and completer.popup().isVisible():
                currentIndex = completer.currentIndex()
                if not currentIndex.isValid():
                    currentIndex = completer.model().index(0, 0)
                
                if currentIndex.isValid():
                    texto_sugerido = completer.model().data(currentIndex, Qt.ItemDataRole.DisplayRole)
                    if texto_sugerido:
                        self.setEditText(texto_sugerido)
                        completer.popup().hide()
                        event.accept()
                        super().keyPressEvent(event)
                        return
        super().keyPressEvent(event)

    def focusOutEvent(self, event):
        texto_atual = self.currentText().strip()
        completer = self.completer()
        if completer and texto_atual:
            model = completer.model()
            for i in range(model.rowCount()):
                item_texto = model.data(model.index(i, 0), Qt.ItemDataRole.DisplayRole)
                if item_texto.lower().startswith(texto_atual.lower()):
                    self.setEditText(item_texto)
                    break
        super().focusOutEvent(event)


class AgendaTab(QWidget):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.editando_id = None
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # --- LADO ESQUERDO: Calendário Estilo Windows ---
        left_layout = QVBoxLayout()
        self.calendar = QCalendarWidget()
        self.calendar.setNavigationBarVisible(True)
        self.calendar.clicked.connect(self.carregar_horarios_do_dia)
        
        # Conecta a mudança de mês para atualizar o destaque em amarelo no calendário
        self.calendar.currentPageChanged.connect(self.pintar_dias_com_eventos)
        
        left_layout.addWidget(QLabel("<b>Selecione o Dia:</b>"))
        left_layout.addWidget(self.calendar)
        left_layout.addStretch()
        main_layout.addLayout(left_layout, stretch=1)

        # --- LADO DIREITO: Lista e Formulário Organizado ---
        right_layout = QVBoxLayout()
        
        self.lbl_data_selecionada = QLabel("Agenda do dia: ")
        self.lbl_data_selecionada.setStyleSheet("font-size: 14px; font-weight: bold;")
        right_layout.addWidget(self.lbl_data_selecionada)

        self.lista_horarios = QListWidget()
        right_layout.addWidget(self.lista_horarios)

        # --- FORMULÁRIO DE AGENDAMENTO ---
        form_layout = QVBoxLayout()
        
        # 1. Seleção de Horário (Hora e Minuto)
        hora_layout = QHBoxLayout()
        
        self.combo_hora = QComboBox()
        horas = [f"{i:02d}" for i in range(24)]
        self.combo_hora.addItems(horas)
        self.combo_hora.setEditable(True)

        self.combo_minuto = QComboBox()
        minutos = [f"{i:02d}" for i in range(0, 60, 5)]
        self.combo_minuto.addItems(minutos)
        self.combo_minuto.setEditable(True)

        hora_layout.addWidget(QLabel("Hora:"))
        hora_layout.addWidget(self.combo_hora)
        hora_layout.addWidget(QLabel("Minuto:"))
        hora_layout.addWidget(self.combo_minuto)
        form_layout.addLayout(hora_layout)

        # 2. Tutor / Cliente
        form_layout.addWidget(QLabel("Tutor / Cliente:"))
        self.combo_client = AutoCompleteComboBox()
        form_layout.addWidget(self.combo_client)

        # 3. Paciente / Pet
        form_layout.addWidget(QLabel("Paciente (Pet):"))
        self.combo_pet = AutoCompleteComboBox()
        form_layout.addWidget(self.combo_pet)

        self.combo_client.currentTextChanged.connect(self.atualizar_pets_por_cliente)

        # 4. Tipo de Atendimento
        form_layout.addWidget(QLabel("Tipo de Atendimento:"))
        self.combo_service = AutoCompleteComboBox()
        self.combo_service.addItems(["Consulta", "Vacina", "Retorno"])
        form_layout.addWidget(self.combo_service)

        right_layout.addLayout(form_layout)

        # Botão de Salvar/Adicionar
        self.btn_salvar = QPushButton("Adicionar Horário")
        self.btn_salvar.clicked.connect(self.salvar_horario)
        self.btn_salvar.setStyleSheet("font-weight: bold; padding: 6px;")
        right_layout.addWidget(self.btn_salvar)

        main_layout.addLayout(right_layout, stretch=1)

        # Carrega os dados iniciais e pinta o calendário do mês atual
        self.carregar_dados_clientes()
        self.carregar_horarios_do_dia(self.calendar.selectedDate())
        self.pintar_dias_com_eventos(QDate.currentDate().year(), QDate.currentDate().month())

    def pintar_dias_com_eventos(self, year, month):
        """Busca no banco de dados os dias do mês visível que possuem agendamentos e pinta de amarelo."""
        if not self.db:
            return
        try:
            formato_amarelo = QTextCharFormat()
            formato_amarelo.setForeground(QColor("#ffbf00")) # Texto escuro

            primeiro_dia = QDate(year, month, 1)
            ultimo_dia = QDate(year, month, primeiro_dia.daysInMonth())

            # Reseta o formato do mês inteiro antes de pintar
            d_atual = primeiro_dia
            while d_atual <= ultimo_dia:
                self.calendar.setDateTextFormat(d_atual, QTextCharFormat())
                d_atual = d_atual.addDays(1)

            inicio_str = primeiro_dia.toString("yyyy-MM-dd")
            fim_str = ultimo_dia.toString("yyyy-MM-dd")

            self.db.cursor.execute("""
                SELECT DISTINCT date FROM appointments 
                WHERE date BETWEEN ? AND ?
            """, (inicio_str, fim_str))
            
            dias_com_agendamento = self.db.cursor.fetchall()

            for (data_db,) in dias_com_agendamento:
                partes = data_db.split("-")
                if len(partes) == 3:
                    ano, mes, dia = int(partes[0]), int(partes[1]), int(partes[2])
                    qdate_evento = QDate(ano, mes, dia)
                    self.calendar.setDateTextFormat(qdate_evento, formato_amarelo)
        except Exception as e:
            print(f"Erro ao pintar dias no calendário da agenda: {e}")

    def carregar_dados_clientes(self):
        if not self.db:
            return

        try:
            self.combo_client.blockSignals(True)
            self.combo_client.clear()
            
            self.db.cursor.execute("SELECT first_name || ' ' || COALESCE(last_name, '') FROM clients ORDER BY first_name ASC")
            registros = self.db.cursor.fetchall()
            
            nomes_clientes = [reg[0].strip() for reg in registros]
            self.combo_client.addItems(nomes_clientes)
            self.combo_client.setCurrentIndex(-1)
            self.combo_client.blockSignals(False)

            completer = QCompleter(nomes_clientes, self.combo_client)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self.combo_client.setCompleter(completer)
            
            completer.activated.connect(lambda text: self.combo_client.setEditText(text))
            
        except Exception as e:
            print(f"Erro ao carregar clientes para a agenda: {e}")

    def atualizar_pets_por_cliente(self, texto_digitado):
        if not self.db or not texto_digitado:
            self.combo_pet.clear()
            return

        try:
            self.combo_pet.blockSignals(True)
            self.combo_pet.clear()
            
            nome_limpo = texto_digitado.strip()

            self.db.cursor.execute(
                "SELECT id FROM clients WHERE (first_name || ' ' || COALESCE(last_name, '')) LIKE ?", 
                (f"%{nome_limpo}%",)
            )
            res = self.db.cursor.fetchone()
            
            if res:
                client_id = res[0]
                pets = self.db.get_pets_by_client_id(client_id)
                nomes_pets = [pet[2] for pet in pets]
                
                self.combo_pet.addItems(nomes_pets)

                if nomes_pets:
                    self.combo_pet.setCurrentIndex(0)
                else:
                    self.combo_pet.setCurrentIndex(-1)
                    self.combo_pet.clearEditText()

                completer_pet = QCompleter(nomes_pets, self.combo_pet)
                completer_pet.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                completer_pet.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
                completer_pet.setFilterMode(Qt.MatchFlag.MatchContains)
                self.combo_pet.setCompleter(completer_pet)
                completer_pet.activated.connect(lambda text: self.combo_pet.setEditText(text))
            
            self.combo_pet.blockSignals(False)
        except Exception as e:
            print(f"Erro ao atualizar pets do cliente: {e}")
            self.combo_pet.blockSignals(False)

    def carregar_horarios_do_dia(self, date: QDate):
        data_str = date.toString("yyyy-MM-dd")
        self.lbl_data_selecionada.setText(f"Agenda do dia: {date.toString('dd/MM/yyyy')}")
        self.lista_horarios.clear()
        
        self.limpar_formulario()
        self.carregar_dados_clientes()

        if not self.db:
            return

        try:
            self.db.cursor.execute(
                "SELECT id, time, client_name, pet_name, service_type FROM appointments WHERE date = ? ORDER BY time ASC", 
                (data_str,)
            )
            registros = self.db.cursor.fetchall()
            
            for reg_id, hora, client, pet, service in registros:
                item = QListWidgetItem(self.lista_horarios)
                widget_item = AgendaItemWidget(reg_id, hora, client, pet, service, self)
                item.setSizeHint(widget_item.sizeHint())
                
                self.lista_horarios.addItem(item)
                self.lista_horarios.setItemWidget(item, widget_item)
                
        except Exception as e:
            print(f"Erro ao carregar agenda: {e}")

    def salvar_horario(self):
        data_str = self.calendar.selectedDate().toString("yyyy-MM-dd")
        
        h = self.combo_hora.currentText().strip()
        m = self.combo_minuto.currentText().strip()
        hora = f"{h}:{m}"
        
        client = self.combo_client.currentText().strip()
        pet = self.combo_pet.currentText().strip()
        service = self.combo_service.currentText().strip()

        if not client or not pet or not service:
            QMessageBox.warning(self, "Aviso", "Preencha o tutor, o pet e o tipo de atendimento.")
            return

        if not self.db:
            return

        try:
            if self.editando_id is None:
                self.db.cursor.execute(
                    "INSERT INTO appointments (date, time, client_name, pet_name, service_type) VALUES (?, ?, ?, ?, ?)", 
                    (data_str, hora, client, pet, service)
                )
                msg = "Agendamento salvo com sucesso!"
            else:
                self.db.cursor.execute(
                    "UPDATE appointments SET time = ?, client_name = ?, pet_name = ?, service_type = ? WHERE id = ?", 
                    (hora, client, pet, service, self.editando_id)
                )
                msg = "Agendamento atualizado com sucesso!"
                self.editando_id = None
                self.btn_salvar.setText("Adicionar Horário")

            self.db.conn.commit()
            QMessageBox.information(self, "Sucesso", msg)
            
            self.limpar_formulario()
            self.carregar_horarios_do_dia(self.calendar.selectedDate())
            
            # Atualiza o destaque em amarelo no calendário após salvar
            self.pintar_dias_com_eventos(self.calendar.yearShown(), self.calendar.monthShown())
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar no banco: {e}")

    def preparar_edicao(self, reg_id):
        if not self.db:
            return
            
        try:
            self.db.cursor.execute(
                "SELECT time, client_name, pet_name, service_type FROM appointments WHERE id = ?", 
                (reg_id,)
            )
            reg = self.db.cursor.fetchone()
            if reg:
                hora, client, pet, service = reg
                
                if ":" in hora:
                    h_part, m_part = hora.split(":", 1)
                    self.combo_hora.setEditText(h_part)
                    self.combo_minuto.setEditText(m_part)
                
                self.combo_client.setEditText(client)
                self.atualizar_pets_por_cliente(client)
                self.combo_pet.setEditText(pet)
                self.combo_service.setEditText(service)
                
                self.editando_id = reg_id
                self.btn_salvar.setText("Salvar Alteração")
        except Exception as e:
            print(f"Erro ao preparar edição: {e}")

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
                self.carregar_horarios_do_dia(self.calendar.selectedDate())
                
                # Atualiza o destaque em amarelo no calendário após excluir
                self.pintar_dias_com_eventos(self.calendar.yearShown(), self.calendar.monthShown())
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir: {e}")

    def limpar_formulario(self):
        self.editando_id = None
        self.btn_salvar.setText("Adicionar Horário")
        self.combo_hora.setCurrentIndex(0)
        self.combo_minuto.setCurrentIndex(0)
        self.combo_client.setCurrentIndex(-1)
        self.combo_client.clearEditText()
        self.combo_pet.setCurrentIndex(-1)
        self.combo_pet.clearEditText()
        self.combo_service.setCurrentIndex(0)