from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QTabBar, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QMessageBox, QListWidget, QListWidgetItem, QPushButton, QDateEdit, 
    QGroupBox, QFormLayout, QTextEdit, QTextBrowser, QLineEdit, QCheckBox, QGridLayout,
    QDialog, QDialogButtonBox
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QIcon, QTextCharFormat, QColor
from ui_client_list import ClientListUI
from ui_agenda import AgendaTab, AgendaItemWidget

class MoedaLineEdit(QLineEdit):
    """Campo de texto personalizado que formata automaticamente o valor para o padrão monetário (ex: 1.000,00)."""
    def __init__(self, parent=None, callback_mudanca=None):
        super().__init__(parent)
        self.callback_mudanca = callback_mudanca
        self.setPlaceholderText("0,00")

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.formatar_valor()
        if self.callback_mudanca:
            self.callback_mudanca()

    def formatar_valor(self):
        texto = self.text().strip()
        if not texto:
            return
        
        try:
            texto_limpo = texto.replace("R$", "").replace(".", "").replace(",", ".").strip()
            valor = float(texto_limpo)
            valor_formatado = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            self.setText(valor_formatado)
        except ValueError:
            pass


class DialogoDivisaoPagamento(QDialog):
    """Janela pop-up para gerenciar múltiplas formas de pagamento com cálculo automático em tempo real."""
    def __init__(self, parent=None, valor_total_sugerido=0.0):
        super().__init__(parent)
        self.setWindowTitle("Dividir Pagamento")
        self.setMinimumWidth(450)
        self.valor_total = valor_total_sugerido
        self.pagamentos_resultado = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        val_sug_str = f"{self.valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if self.valor_total > 0 else "0,00"
        self.lbl_info = QLabel(f"<b>Valor Total da Consulta: R$ {val_sug_str}</b>")
        layout.addWidget(self.lbl_info)

        grid_pag = QGridLayout()
        

        grid_pag.addWidget(QLabel("PIX: R$"), 0, 0)
        self.txt_pix = MoedaLineEdit(callback_mudanca=self.calcular_restante_pendente)
        grid_pag.addWidget(self.txt_pix, 0, 1)

        grid_pag.addWidget(QLabel("Dinheiro: R$"), 1, 0)
        self.txt_dinheiro = MoedaLineEdit(callback_mudanca=self.calcular_restante_pendente)
        grid_pag.addWidget(self.txt_dinheiro, 1, 1)

        grid_pag.addWidget(QLabel("Transferência: R$"), 2, 0)
        self.txt_transf = MoedaLineEdit(callback_mudanca=self.calcular_restante_pendente)
        grid_pag.addWidget(self.txt_transf, 2, 1)

        grid_pag.addWidget(QLabel("Débito: R$"), 3, 0)
        self.txt_debito = MoedaLineEdit(callback_mudanca=self.calcular_restante_pendente)
        grid_pag.addWidget(self.txt_debito, 3, 1)

        grid_pag.addWidget(QLabel("Crédito à vista: R$"), 4, 0)
        self.txt_cred_vista = MoedaLineEdit(callback_mudanca=self.calcular_restante_pendente)
        grid_pag.addWidget(self.txt_cred_vista, 4, 1)

        grid_pag.addWidget(QLabel("Crédito parcelado: R$"), 5, 0)
        self.txt_cred_parc = MoedaLineEdit(callback_mudanca=self.calcular_restante_pendente)
        grid_pag.addWidget(self.txt_cred_parc, 5, 1)
        
        self.txt_parcelas = QLineEdit()
        self.txt_parcelas.setPlaceholderText("Qtd. vezes")
        grid_pag.addWidget(self.txt_parcelas, 5, 3)

        grid_pag.addWidget(QLabel("<b>Valor Pendente: R$</b>"), 6, 0)
        self.txt_pendente = MoedaLineEdit()
        if self.valor_total > 0:
            self.txt_pendente.setText(val_sug_str)
        grid_pag.addWidget(self.txt_pendente, 6, 1)

        layout.addLayout(grid_pag)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(self.validar_e_salvar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def calcular_restante_pendente(self):
        try:
            def conv(campo):
                txt = campo.text().replace(".", "").replace(",", ".").strip()
                return float(txt) if txt else 0.0

            total_pago = (
                conv(self.txt_dinheiro) + 
                conv(self.txt_pix) + 
                conv(self.txt_transf) + 
                conv(self.txt_debito) + 
                conv(self.txt_cred_vista) + 
                conv(self.txt_cred_parc)
            )

            restante = self.valor_total - total_pago
            if restante < 0:
                restante = 0.0

            restante_str = f"{restante:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            self.txt_pendente.setText(restante_str)
        except ValueError:
            pass

    def validar_e_salvar(self):
        try:
            def converter_valor(campo):
                txt = campo.text().replace(".", "").replace(",", ".").strip()
                return float(txt) if txt else 0.0

            dinheiro = converter_valor(self.txt_dinheiro)
            pix = converter_valor(self.txt_pix)
            transf = converter_valor(self.txt_transf)
            debito = converter_valor(self.txt_debito)
            cred_vista = converter_valor(self.txt_cred_vista)
            cred_parc = converter_valor(self.txt_cred_parc)
            
            parcelas = int(self.txt_parcelas.text() or 1) if cred_parc > 0 else 1
            pendente = converter_valor(self.txt_pendente)

            self.pagamentos_resultado = []
            if dinheiro > 0: self.pagamentos_resultado.append(("Dinheiro", dinheiro, 1, "Pago"))
            if pix > 0: self.pagamentos_resultado.append(("PIX", pix, 1, "Pago"))
            if transf > 0: self.pagamentos_resultado.append(("Transferência", transf, 1, "Pago"))
            if debito > 0: self.pagamentos_resultado.append(("Débito", debito, 1, "Pago"))
            if cred_vista > 0: self.pagamentos_resultado.append(("Crédito à vista", cred_vista, 1, "Pago"))
            if cred_parc > 0: self.pagamentos_resultado.append(("Crédito parcelado", cred_parc, parcelas, "Pago"))
            if pendente > 0: self.pagamentos_resultado.append(("Valor Pendente", pendente, 1, "Pendente"))

            if not self.pagamentos_resultado:
                QMessageBox.warning(self, "Aviso", "Informe ao menos uma forma de pagamento ou valor pendente.")
                return

            self.accept()
        except ValueError:
            QMessageBox.critical(self, "Erro", "Verifique se os valores numéricos e parcelas foram digitados corretamente.")


class AgendaTableWidget(QWidget):
    """Widget com histórico inteligente, exibições de IDs, lembretes, vacinas e calendário dinâmico."""
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

        # ================= COLUNA 1 (ESQUERDA): FICHA + HISTÓRICO + LEMBRETES =================
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

        # Histórico Dinâmico de Atendimentos
        self.group_historico = QGroupBox("Histórico de Atendimentos")
        self.group_historico.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #ccc; border-radius: 6px; margin-top: 4px; padding-top: 8px; }")
        
        historico_layout = QVBoxLayout(self.group_historico)
        self.txt_historico = QTextBrowser()
        self.txt_historico.setPlaceholderText("Nenhum atendimento anterior a esta data.")
        historico_layout.addWidget(self.txt_historico)

        left_layout.addWidget(self.group_historico)

        # Bloco de Lembretes e Alertas
        self.group_lembretes = QGroupBox("Lembretes e Alertas")
        self.group_lembretes.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #ccc; border-radius: 6px; margin-top: 4px; padding-top: 8px; }")
        self.group_lembretes.setMinimumHeight(150)
        
        lembrete_layout = QVBoxLayout(self.group_lembretes)
        
        self.lbl_mensagem_alerta = QLabel("Nenhum alerta pendente para hoje.")
        self.lbl_mensagem_alerta.setWordWrap(True)
        self.lbl_mensagem_alerta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_mensagem_alerta.setStyleSheet("padding: 6px; font-weight: normal; font-size: 12px;")
        lembrete_layout.addWidget(self.lbl_mensagem_alerta)

        carrossel_control_layout = QHBoxLayout()
        carrossel_control_layout.addStretch()
        
        self.lbl_bolinha_1 = QLabel("●")
        self.lbl_bolinha_1.setStyleSheet("color: #333; font-size: 11px;")
        self.lbl_bolinha_2 = QLabel("○")
        self.lbl_bolinha_2.setStyleSheet("color: #ccc; font-size: 11px;")
        
        carrossel_control_layout.addWidget(self.lbl_bolinha_1)
        carrossel_control_layout.addWidget(self.lbl_bolinha_2)
        carrossel_control_layout.addStretch()
        
        lembrete_layout.addLayout(carrossel_control_layout)
        left_layout.addWidget(self.group_lembretes)

        main_layout.addLayout(left_layout, stretch=2)

        # ================= COLUNA 2 (CENTRO): RESUMO + VACINAS SEPARADAS + PAGAMENTO + BOTÃO SALVAR =================
        center_layout = QVBoxLayout()
        
        # 1. Caixa de Resumo do Atendimento do Dia
        self.group_atendimento = QGroupBox("Resumo do Atendimento do Dia")
        self.group_atendimento.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #ccc; border-radius: 6px; margin-top: 4px; padding-top: 8px; }")
        
        atendimento_layout = QVBoxLayout(self.group_atendimento)
        self.txt_atendimento = QTextEdit()
        self.txt_atendimento.setPlaceholderText("Digite o resumo ou deixe em branco para salvar o serviço automático...")
        atendimento_layout.addWidget(self.txt_atendimento)

        center_layout.addWidget(self.group_atendimento)

        # 2. Caixa de Vacinas por Checkboxes Separadas (Cães e Gatos)
        self.group_vacinas = QGroupBox("Vacinas Aplicadas (Marque as aplicadas)")
        self.group_vacinas.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #ccc; border-radius: 6px; margin-top: 4px; padding-top: 8px; }")
        
        vacinas_grid = QGridLayout(self.group_vacinas)
        
        self.chk_v8 = QCheckBox("V8")
        self.chk_v10 = QCheckBox("V10")
        self.chk_v4 = QCheckBox("V4 (Gatos)")
        self.chk_v5 = QCheckBox("V5 (Gatos)")
        self.chk_raiva = QCheckBox("Antirrábica (Raiva)")
        self.chk_giardia = QCheckBox("Giárdia")
        self.chk_gripe = QCheckBox("Gripe Canina")
        self.chk_feLV = QCheckBox("FeLV (Gatos)")

        for chk in [self.chk_v8, self.chk_v10, self.chk_v4, self.chk_v5, self.chk_raiva, self.chk_giardia, self.chk_gripe, self.chk_feLV]:
            chk.setStyleSheet("font-weight: normal; font-size: 12px;")

        vacinas_grid.addWidget(self.chk_v8, 0, 0)
        vacinas_grid.addWidget(self.chk_v10, 0, 1)
        vacinas_grid.addWidget(self.chk_v4, 1, 0)
        vacinas_grid.addWidget(self.chk_v5, 1, 1)
        vacinas_grid.addWidget(self.chk_raiva, 2, 0)
        vacinas_grid.addWidget(self.chk_giardia, 2, 1)
        vacinas_grid.addWidget(self.chk_gripe, 3, 0)
        vacinas_grid.addWidget(self.chk_feLV, 3, 1)

        center_layout.addWidget(self.group_vacinas)

        # 3. Caixa Separada para Vermífugo e Antipulgas (Campos de Texto)
        self.group_outros = QGroupBox("Outros Preventivos (Opcional)")
        self.group_outros.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #ccc; border-radius: 6px; margin-top: 4px; padding-top: 8px; }")
        
        outros_form = QFormLayout(self.group_outros)
        outros_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.txt_vermifugo_opc = QLineEdit()
        self.txt_vermifugo_opc.setPlaceholderText("Ex: Drontal Plus...")

        self.txt_antipulgas_opc = QLineEdit()
        self.txt_antipulgas_opc.setPlaceholderText("Ex: NexGard, Bravecto...")

        for field in [self.txt_vermifugo_opc, self.txt_antipulgas_opc]:
            field.setStyleSheet("font-weight: normal; font-size: 12px;")

        outros_form.addRow("<b>Vermífugo:</b>", self.txt_vermifugo_opc)
        outros_form.addRow("<b>Antipulgas:</b>", self.txt_antipulgas_opc)

        center_layout.addWidget(self.group_outros)

        # 4. Bloco de Pagamento Rápido na Base da Coluna Central (Ordem correta com Pendente por último)
        self.group_pagamento = QGroupBox("Forma de Pagamento")
        self.group_pagamento.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #ccc; border-radius: 6px; margin-top: 4px; padding-top: 8px; }")
        
        pag_layout = QVBoxLayout(self.group_pagamento)
        
        valor_layout = QHBoxLayout()
        valor_layout.addWidget(QLabel("Valor do Atendimento R$:"))
        self.txt_valor_atendimento = MoedaLineEdit()
        valor_layout.addWidget(self.txt_valor_atendimento)
        pag_layout.addLayout(valor_layout)

        self.chk_pag_pix = QCheckBox("PIX")
        self.chk_pag_dinheiro = QCheckBox("Dinheiro")
        self.chk_pag_transf = QCheckBox("Transferência")
        self.chk_pag_debito = QCheckBox("Débito")
        self.chk_pag_credito = QCheckBox("Crédito à vista")
        self.chk_pag_cred_parc = QCheckBox("Crédito parcelado")
        self.chk_pag_pendente = QCheckBox("Valor Pendente")
        
        # Adiciona as opções simples primeiro
        for c in [self.chk_pag_pix, self.chk_pag_dinheiro, self.chk_pag_transf, self.chk_pag_debito, self.chk_pag_credito]:
            c.setStyleSheet("font-weight: normal; font-size: 12px;")
            pag_layout.addWidget(c)
        
        # Adiciona o Crédito Parcelado com a caixa de texto ao lado
        cred_parc_layout = QHBoxLayout()
        self.txt_qtd_parcelas_main = QLineEdit()
        self.txt_qtd_parcelas_main.setPlaceholderText("Qtd. vezes")
        self.txt_qtd_parcelas_main.setMaximumWidth(90)
        cred_parc_layout.addWidget(self.chk_pag_cred_parc)
        cred_parc_layout.addWidget(self.txt_qtd_parcelas_main)
        cred_parc_layout.addStretch()

        self.chk_pag_cred_parc.setStyleSheet("font-weight: normal; font-size: 12px;")
        pag_layout.addLayout(cred_parc_layout)

        # Adiciona o Valor Pendente obrigatoriamente por ÚLTIMO embaixo de tudo
        self.chk_pag_pendente.setStyleSheet("font-weight: normal; font-size: 12px;")
        pag_layout.addWidget(self.chk_pag_pendente)

        self.btn_dividir_pagamento = QPushButton("Dividir Pagamento")
        self.btn_dividir_pagamento.clicked.connect(self.abrir_popup_divisao)
        pag_layout.addWidget(self.btn_dividir_pagamento)

        center_layout.addWidget(self.group_pagamento)

        # Botão unificado de salvar no centro exato
        self.btn_salvar_atendimento = QPushButton("Salvar Atendimento")
        self.btn_salvar_atendimento.setStyleSheet("font-weight: bold; padding: 8px; font-size: 14px;")
        self.btn_salvar_atendimento.clicked.connect(self.salvar_ou_atualizar_atendimento)
        center_layout.addWidget(self.btn_salvar_atendimento)

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

        calendario_popup = self.date_edit.calendarWidget()
        if calendario_popup:
            calendario_popup.currentPageChanged.connect(self.pintar_dias_com_eventos)
            self.pintar_dias_com_eventos(QDate.currentDate().year(), QDate.currentDate().month())

        date_control_layout.addWidget(self.date_edit)

        self.btn_hoje = QPushButton("Hoje")
        self.btn_hoje.clicked.connect(lambda: self.date_edit.setDate(QDate.currentDate()))
        date_control_layout.addWidget(self.btn_hoje)

        self.btn_atualizar = QPushButton("Atualizar")
        self.btn_atualizar.clicked.connect(self.carregar_horarios)
        date_control_layout.addWidget(self.btn_atualizar)
        
        date_control_layout.addStretch()
        right_layout.addLayout(date_control_layout)

        self.lista_horarios = QListWidget()
        self.lista_horarios.itemClicked.connect(self.ao_clicar_horario)
        self.lista_horarios.currentItemChanged.connect(lambda current, previous: self.ao_clicar_horario(current))
        right_layout.addWidget(self.lista_horarios)

        main_layout.addLayout(right_layout, stretch=2)
        self.carregar_horarios()

    def abrir_popup_divisao(self):
        try:
            txt = self.txt_valor_atendimento.text().replace(".", "").replace(",", ".").strip()
            total = float(txt) if txt else 0.0
        except ValueError:
            total = 0.0

        dlg = DialogoDivisaoPagamento(self, valor_total_sugerido=total)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.pagamentos_personalizados = dlg.pagamentos_resultado
            QMessageBox.information(self, "Sucesso", "Divisão de pagamento configurada com sucesso! Clique em 'Salvar Atendimento' para registrar.")
        else:
            self.pagamentos_personalizados = None

    def showEvent(self, event):
        super().showEvent(event)
        self.carregar_horarios()
        cal = self.date_edit.calendarWidget()
        if cal:
            self.pintar_dias_com_eventos(cal.yearShown(), cal.monthShown())

    def pintar_dias_com_eventos(self, year, month):
        if not self.db:
            return
        try:
            calendario_popup = self.date_edit.calendarWidget()
            if not calendario_popup:
                return

            formato_amarelo = QTextCharFormat()
            formato_amarelo.setForeground(QColor("#ffbf00"))

            primeiro_dia = QDate(year, month, 1)
            ultimo_dia = QDate(year, month, primeiro_dia.daysInMonth())

            d_atual = primeiro_dia
            while d_atual <= ultimo_dia:
                calendario_popup.setDateTextFormat(d_atual, QTextCharFormat())
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
                    calendario_popup.setDateTextFormat(qdate_evento, formato_amarelo)
        except Exception as e:
            print(f"Erro ao pintar dias no calendário: {e}")

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

                    html_content += f"<b>{data_formatada}</b><br>{notes_ant.replace('\n', '<br>')}<br><span style='color: #888; font-size: 10px;'>ID: #{hist_id}</span><br><br>"
                
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

    def salvar_ou_atualizar_atendimento(self):
        if not self.current_pet_id or not self.current_client_id:
            QMessageBox.warning(self, "Aviso", "Selecione um agendamento válido.")
            return

        texto = self.txt_atendimento.toPlainText().strip()
        data_app = self.date_edit.date()
        data_str = data_app.toString("yyyy-MM-dd")
        
        if not texto:
            texto = f"- {self.current_service_type}"
        
        vacinas_marcadas = []
        if self.chk_v8.isChecked(): vacinas_marcadas.append("V8")
        if self.chk_v10.isChecked(): vacinas_marcadas.append("V10")
        if self.chk_v4.isChecked(): vacinas_marcadas.append("V4")
        if self.chk_v5.isChecked(): vacinas_marcadas.append("V5")
        if self.chk_raiva.isChecked(): vacinas_marcadas.append("Antirrábica")
        if self.chk_giardia.isChecked(): vacinas_marcadas.append("Giárdia")
        if self.chk_gripe.isChecked(): vacinas_marcadas.append("Gripe Canina")
        if self.chk_feLV.isChecked(): vacinas_marcadas.append("FeLV")

        vermifugo = self.txt_vermifugo_opc.text().strip()
        antipulgas = self.txt_antipulgas_opc.text().strip()

        complementos = []
        if vacinas_marcadas:
            complementos.append(f"• Vacinas Aplicadas: {', '.join(vacinas_marcadas)}")
            try:
                self.db.cursor.execute("SELECT birth_date FROM patients WHERE id = ?", (self.current_pet_id,))
                pet_row = self.db.cursor.fetchone()
                birth_date_str = pet_row[0] if pet_row else ""

                is_filhote = False
                if birth_date_str:
                    try:
                        b_date = datetime.strptime(birth_date_str, "%d/%m/%Y")
                        hoje = datetime.now()
                        dias_de_vida = (hoje - b_date).days
                        if 0 <= dias_de_vida < 365:
                            is_filhote = True
                    except ValueError:
                        pass

                for vac in vacinas_marcadas:
                    self.db.cursor.execute(
                        "SELECT COUNT(*) FROM pet_vaccines WHERE pet_id = ? AND vaccine_name = ?", 
                        (self.current_pet_id, vac)
                    )
                    res = self.db.cursor.fetchone()
                    dose_count = res[0] if res else 0

                    if vac == "Antirrábica":
                        prox_data = data_app.addYears(1).toString("yyyy-MM-dd")
                    elif is_filhote and dose_count < 2:
                        prox_data = data_app.addDays(21).toString("yyyy-MM-dd")
                    else:
                        prox_data = data_app.addYears(1).toString("yyyy-MM-dd")

                    self.db.cursor.execute("""
                        INSERT INTO pet_vaccines (pet_id, vaccine_name, application_date, next_due_date)
                        VALUES (?, ?, ?, ?)
                    """, (self.current_pet_id, vac, data_str, prox_data))
                self.db.conn.commit()
            except Exception as ex:
                print(f"Erro ao registrar histórico de vacinas: {ex}")

        if vermifugo:
            complementos.append(f"• Vermífugo: {vermifugo}")
        if antipulgas:
            complementos.append(f"• Antipulgas: {antipulgas}")

        if complementos:
            texto += "\n\n" + "\n".join(complementos)
        
        try:
            if self.current_historico_id:
                self.db.atualizar_historico(self.current_historico_id, texto)
                historico_id = self.current_historico_id
                msg = "Atendimento atualizado com sucesso!"
            else:
                historico_id = self.db.salvar_historico(self.current_pet_id, self.current_client_id, data_str, texto)
                msg = "Atendimento salvo com sucesso!"

            if hasattr(self, 'pagamentos_personalizados') and self.pagamentos_personalizados:
                self.db.salvar_pagamentos(historico_id, self.pagamentos_personalizados)
                self.pagamentos_personalizados = None
            else:
                try:
                    txt_v = self.txt_valor_atendimento.text().replace(".", "").replace(",", ".").strip()
                    valor_total = float(txt_v) if txt_v else 0.0
                except ValueError:
                    valor_total = 0.0

                metodo_escolhido = "Dinheiro"
                status_pagamento = "Pago"
                parcelas = 1

                if self.chk_pag_pix.isChecked(): metodo_escolhido = "PIX"
                elif self.chk_pag_transf.isChecked(): metodo_escolhido = "Transferência"
                elif self.chk_pag_debito.isChecked(): metodo_escolhido = "Débito"
                elif self.chk_pag_credito.isChecked(): metodo_escolhido = "Crédito à vista"
                elif self.chk_pag_pendente.isChecked():
                    metodo_escolhido = "Valor Pendente"
                    status_pagamento = "Pendente"
                elif self.chk_pag_cred_parc.isChecked():
                    metodo_escolhido = "Crédito parcelado"
                    try:
                        parcelas = int(self.txt_qtd_parcelas_main.text() or 1)
                    except ValueError:
                        parcelas = 1

                if valor_total > 0:
                    self.db.salvar_pagamentos(historico_id, [(metodo_escolhido, valor_total, parcelas, status_pagamento)])

            QMessageBox.information(self, "Sucesso", msg)

            self.chk_v8.setChecked(False)
            self.chk_v10.setChecked(False)
            self.chk_v4.setChecked(False)
            self.chk_v5.setChecked(False)
            self.chk_raiva.setChecked(False)
            self.chk_giardia.setChecked(False)
            self.chk_gripe.setChecked(False)
            self.chk_feLV.setChecked(False)
            self.txt_vermifugo_opc.clear()
            self.txt_antipulgas_opc.clear()
            self.txt_valor_atendimento.clear()
            self.chk_pag_pix.setChecked(False)
            self.chk_pag_dinheiro.setChecked(False)
            self.chk_pag_transf.setChecked(False)
            self.chk_pag_debito.setChecked(False)
            self.chk_pag_credito.setChecked(False)
            self.chk_pag_pendente.setChecked(False)
            self.chk_pag_cred_parc.setChecked(False)
            self.txt_qtd_parcelas_main.clear()

            self.atualizar_paineis_atendimento(self.current_pet_id)
            
            cal = self.date_edit.calendarWidget()
            if cal:
                self.pintar_dias_com_eventos(cal.yearShown(), cal.monthShown())
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
        self.pagamentos_personalizados = None
        self.chk_v8.setChecked(False)
        self.chk_v10.setChecked(False)
        self.chk_v4.setChecked(False)
        self.chk_v5.setChecked(False)
        self.chk_raiva.setChecked(False)
        self.chk_giardia.setChecked(False)
        self.chk_gripe.setChecked(False)
        self.chk_feLV.setChecked(False)
        self.txt_vermifugo_opc.clear()
        self.txt_antipulgas_opc.clear()
        self.txt_valor_atendimento.clear()
        self.chk_pag_pix.setChecked(False)
        self.chk_pag_dinheiro.setChecked(False)
        self.chk_pag_transf.setChecked(False)
        self.chk_pag_debito.setChecked(False)
        self.chk_pag_credito.setChecked(False)
        self.chk_pag_pendente.setChecked(False)
        self.chk_pag_cred_parc.setChecked(False)
        self.txt_qtd_parcelas_main.clear()
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
                
                cal = self.date_edit.calendarWidget()
                if cal:
                    self.pintar_dias_com_eventos(cal.yearShown(), cal.monthShown())
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