from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QCalendarWidget, 
    QListWidget, QPushButton, QLabel, QLineEdit, QMessageBox, 
    QListWidgetItem, QMenu, QComboBox, QCompleter
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QAction

class AgendaItemWidget(QWidget):
    """Widget personalizado para cada linha da lista, contendo o horário, descrição e o menu de três pontinhos."""
    def __init__(self, reg_id, hora, descricao, parent_agenda):
        super().__init__()
        self.reg_id = reg_id
        self.parent_agenda = parent_agenda

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # Texto do horário e descrição do agendamento
        self.lbl_info = QLabel(f"<b>{hora}</b> - {descricao}")
        layout.addWidget(self.lbl_info)

        layout.addStretch()

        # Botão de três pontinhos (...)
        self.btn_menu = QPushButton("⋮")
        self.btn_menu.setFixedSize(30, 25)
        self.btn_menu.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        # Cria o menu suspenso para as opções
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
        self.parent_agenda.preparar_edicao(self.reg_id, self.lbl_info.text())

    def chamar_exclusao(self):
        self.parent_agenda.excluir_horario(self.reg_id)


class AgendaTab(QWidget):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.editando_id = None
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # --- LADO ESQUERDO: Calendário ---
        left_layout = QVBoxLayout()
        self.calendar = QCalendarWidget()
        self.calendar.setNavigationBarVisible(True)
        self.calendar.clicked.connect(self.carregar_horarios_do_dia)
        
        left_layout.addWidget(QLabel("<b>Selecione o Dia:</b>"))
        left_layout.addWidget(self.calendar)
        left_layout.addStretch()
        main_layout.addLayout(left_layout, stretch=1)

        # --- LADO DIREITO: Lista e Formulário ---
        right_layout = QVBoxLayout()
        
        self.lbl_data_selecionada = QLabel("Agenda do dia: ")
        self.lbl_data_selecionada.setStyleSheet("font-size: 14px; font-weight: bold;")
        right_layout.addWidget(self.lbl_data_selecionada)

        self.lista_horarios = QListWidget()
        right_layout.addWidget(self.lista_horarios)

        # --- SELEÇÃO DE HORÁRIO INTELIGENTE (Hora e Minuto separados) ---
        form_layout = QVBoxLayout()
        
        form_layout.addWidget(QLabel("Horário do Atendimento:"))
        
        hora_layout = QHBoxLayout()

        # 1. Combo de Horas (00 a 23) - Editável com sugestões
        self.combo_hora = QComboBox()
        horas = [f"{i:02d}" for i in range(24)]
        self.combo_hora.addItems(horas)
        self.combo_hora.setEditable(True)
        completer_hora = QCompleter(horas, self)
        completer_hora.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer_hora.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.combo_hora.setCompleter(completer_hora)

        # 2. Combo de Minutos (de 5 em 5) - Editável
        self.combo_minuto = QComboBox()
        minutos = [f"{i:02d}" for i in range(0, 60, 5)]
        self.combo_minuto.addItems(minutos)
        self.combo_minuto.setEditable(True)
        completer_minuto = QCompleter(minutos, self)
        completer_minuto.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer_minuto.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.combo_minuto.setCompleter(completer_minuto)

        hora_layout.addWidget(QLabel("Hora:"))
        hora_layout.addWidget(self.combo_hora)
        hora_layout.addWidget(QLabel("Minuto:"))
        hora_layout.addWidget(self.combo_minuto)

        form_layout.addLayout(hora_layout)

        # Campo de Descrição / Paciente
        self.input_descricao_field = QLineEdit()
        self.input_descricao_field.setPlaceholderText("Ex: Consulta - Rex (Cachorro) / Tutor João")
        form_layout.addWidget(QLabel("Descrição / Paciente:"))
        form_layout.addWidget(self.input_descricao_field)

        right_layout.addLayout(form_layout)

        # Botão de Ação
        self.btn_salvar = QPushButton("Adicionar Horário")
        self.btn_salvar.clicked.connect(self.salvar_horario)
        self.btn_salvar.setStyleSheet("font-weight: bold; padding: 6px;")
        right_layout.addWidget(self.btn_salvar)

        main_layout.addLayout(right_layout, stretch=1)

        self.carregar_horarios_do_dia(self.calendar.selectedDate())

    def carregar_horarios_do_dia(self, date: QDate):
        data_str = date.toString("yyyy-MM-dd")
        self.lbl_data_selecionada.setText(f"Agenda do dia: {date.toString('dd/MM/yyyy')}")
        self.lista_horarios.clear()
        
        self.editando_id = None
        self.btn_salvar.setText("Adicionar Horário")
        self.combo_hora.setCurrentIndex(0)
        self.combo_minuto.setCurrentIndex(0)
        self.input_descricao_field.clear()

        if not self.db:
            return

        try:
            self.db.cursor.execute(
                "SELECT id, time, description FROM appointments WHERE date = ? ORDER BY time ASC", 
                (data_str,)
            )
            registros = self.db.cursor.fetchall()
            
            for reg_id, hora, desc in registros:
                item = QListWidgetItem(self.lista_horarios)
                widget_item = AgendaItemWidget(reg_id, hora, desc, self)
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
        
        desc = self.input_descricao_field.text().strip()

        if not h or not m or not desc:
            QMessageBox.warning(self, "Aviso", "Preencha o horário completo e a descrição.")
            return

        if not self.db:
            return

        try:
            if self.editando_id is None:
                self.db.cursor.execute(
                    "INSERT INTO appointments (date, time, description) VALUES (?, ?, ?)", 
                    (data_str, hora, desc)
                )
                msg = "Horário agendado com sucesso!"
            else:
                self.db.cursor.execute(
                    "UPDATE appointments SET time = ?, description = ? WHERE id = ?", 
                    (hora, desc, self.editando_id)
                )
                msg = "Agendamento atualizado com sucesso!"
                self.editando_id = None
                self.btn_salvar.setText("Adicionar Horário")

            self.db.conn.commit()
            QMessageBox.information(self, "Sucesso", msg)
            
            self.input_descricao_field.clear()
            self.carregar_horarios_do_dia(self.calendar.selectedDate())
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar no banco: {e}")

    def preparar_edicao(self, reg_id, texto_atual):
        self.editando_id = reg_id
        self.btn_salvar.setText("Salvar Alteração")
        
        if " - " in texto_atual:
            partes = texto_atual.split(" - ", 1)
            hora_limpa = partes[0].replace("<b>", "").replace("</b>", "").strip()
            
            if ":" in hora_limpa:
                h_part, m_part = hora_limpa.split(":", 1)
                self.combo_hora.setEditText(h_part)
                self.combo_minuto.setEditText(m_part)
                
            self.input_descricao_field.setText(partes[1])

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
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir: {e}")