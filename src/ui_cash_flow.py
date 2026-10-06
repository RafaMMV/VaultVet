from theme import apply_widget_style
from datetime import datetime
from collections import defaultdict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QGroupBox, QLabel, 
    QTableWidget, QTableWidgetItem, QMessageBox, 
    QComboBox, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont


class CashFlowTab(QWidget):
    def __init__(self, parent=None, db=None, main_window=None):
        super().__init__(parent)
        self.db = db
        self.main_window = main_window
        
        self.init_ui()
        from theme import compact_controls
        compact_controls(self)
        self.carregar_dados_caixa()
    
    def load_data(self):
        self.carregar_dados_caixa()

    def carregar_dados(self):
        self.carregar_dados_caixa()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Cabeçalho / Título da Aba
        top_layout = QHBoxLayout()
        self.title_label = QLabel("Controle de Caixa e Financeiro")
        apply_widget_style(self.title_label, "style4")
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        
        # Botão de atualizar dados
        self.btn_atualizar = QPushButton("Atualizar Caixa")
        self.btn_atualizar.clicked.connect(self.carregar_dados_caixa)
        top_layout.addWidget(self.btn_atualizar)
        
        main_layout.addLayout(top_layout)

        # --- BLOCO SUPERIOR: Resumo / Indicadores ---
        self.resumo_group = QGroupBox("Indicadores do Período")
        apply_widget_style(self.resumo_group, "style5")
        resumo_layout = QHBoxLayout(self.resumo_group)

        self.lbl_fat_mes = QLabel("Faturamento: —")
        apply_widget_style(self.lbl_fat_mes, "style6")
        
        self.lbl_total_recebido = QLabel("Total Recebido: —")
        apply_widget_style(self.lbl_total_recebido, "style6")
        
        self.lbl_total_pendente = QLabel("Total Pendente: —")
        apply_widget_style(self.lbl_total_pendente, "style7")

        resumo_layout.addWidget(self.lbl_fat_mes)
        resumo_layout.addWidget(self.lbl_total_recebido)
        resumo_layout.addWidget(self.lbl_total_pendente)
        
        main_layout.addWidget(self.resumo_group)

        # --- BLOCO PRINCIPAL: Extrato de Movimentações ---
        extrato_group = QGroupBox("Extrato e Movimentações")
        apply_widget_style(extrato_group, "style5")
        extrato_layout = QVBoxLayout(extrato_group)

        # Filtros (Status, Mês, Ano e Botões de Atalho Rápido Mensal/Anual)
        filtro_layout = QHBoxLayout()
        
        filtro_layout.addWidget(QLabel("Status:"))
        self.combo_filtro_status = QComboBox()
        self.combo_filtro_status.addItems(["Todas as Movimentações", "Apenas Entradas", "Apenas Pendências"])
        self.combo_filtro_status.currentIndexChanged.connect(self.carregar_dados_caixa)
        filtro_layout.addWidget(self.combo_filtro_status)

        filtro_layout.addWidget(QLabel("Mês:"))
        self.combo_filtro_mes = QComboBox()
        self.combo_filtro_mes.addItem("Todos os Meses")
        meses_nomes = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        for i, m in enumerate(meses_nomes, start=1):
            self.combo_filtro_mes.addItem(f"{i:02d} - {m}", f"{i:02d}")
        self.combo_filtro_mes.currentIndexChanged.connect(self.carregar_dados_caixa)
        filtro_layout.addWidget(self.combo_filtro_mes)

        filtro_layout.addWidget(QLabel("Ano:"))
        self.combo_filtro_ano = QComboBox()
        self.combo_filtro_ano.addItem("Todos os Anos")
        
        ano_atual = datetime.now().year
        ano_limite_futuro = ano_atual + 2
        for ano in range(ano_limite_futuro, 2023, -1):
            self.combo_filtro_ano.addItem(str(ano))

        index_ano_atual = self.combo_filtro_ano.findText(str(ano_atual))
        if index_ano_atual >= 0:
            self.combo_filtro_ano.setCurrentIndex(index_ano_atual)

        self.combo_filtro_ano.currentIndexChanged.connect(self.carregar_dados_caixa)
        filtro_layout.addWidget(self.combo_filtro_ano)

        filtro_layout.addStretch()
        extrato_layout.addLayout(filtro_layout)

        # Tabela de Movimentações
        self.tabela_extrato = QTableWidget()
        self.tabela_extrato.setColumnCount(5)
        self.tabela_extrato.setHorizontalHeaderLabels(["Data", "Pet / Tutor", "Forma Pgto", "Valor Total", "Status"])
        self.tabela_extrato.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.tabela_extrato.cellDoubleClicked.connect(self.abrir_consulta)
        self.tabela_extrato.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_extrato.verticalHeader().setVisible(False)
        self.tabela_extrato.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        extrato_layout.addWidget(self.tabela_extrato)

        # Botão de Ação na Tabela (Dar baixa)
        acoes_tabela_layout = QHBoxLayout()
        self.btn_dar_baixa = QPushButton("Dar Baixa em Selecionado (Marcar como Pago)")
        self.btn_dar_baixa.clicked.connect(self.dar_baixa_pagamento)
        acoes_tabela_layout.addWidget(self.btn_dar_baixa)

        extrato_layout.addLayout(acoes_tabela_layout)
        
        main_layout.addWidget(extrato_group)

    def abrir_consulta(self, row, column):
        item = self.tabela_extrato.item(row, 0)
        pay_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        if pay_id and self.main_window:
            self.main_window.carregar_pagamento_para_edicao(pay_id)

    def ativar_visao_mensal(self):
        """Atalho para selecionar o mês atual e manter o ano atual."""
        mes_atual_str = datetime.now().strftime("%m")
        for i in range(self.combo_filtro_mes.count()):
            if self.combo_filtro_mes.itemData(i) == mes_atual_str:
                self.combo_filtro_mes.setCurrentIndex(i)
                break
        
        ano_atual_str = str(datetime.now().year)
        idx_ano = self.combo_filtro_ano.findText(ano_atual_str)
        if idx_ano >= 0:
            self.combo_filtro_ano.setCurrentIndex(idx_ano)

    def ativar_visao_anual(self):
        """Atalho para selecionar 'Todos os Meses' e focar no ano atual."""
        self.combo_filtro_mes.setCurrentIndex(0)
        
        ano_atual_str = str(datetime.now().year)
        idx_ano = self.combo_filtro_ano.findText(ano_atual_str)
        if idx_ano >= 0:
            self.combo_filtro_ano.setCurrentIndex(idx_ano)

    def carregar_dados_caixa(self):
        """Puxa os dados agrupando pagamentos. Mantém as pendências sempre visíveis para controle."""
        if not self.db:
            return
        
        try:
            self.db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS consultation_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    consultation_id INTEGER,
                    payment_method TEXT,
                    amount REAL,
                    installments INTEGER,
                    status TEXT,
                    FOREIGN KEY(consultation_id) REFERENCES consultation_history(id) ON DELETE CASCADE
                )
            """)
            self.db.conn.commit()

            status_filtro = self.combo_filtro_status.currentText()
            mes_idx = self.combo_filtro_mes.currentIndex()
            ano_filtro = self.combo_filtro_ano.currentText()
            
            # 1. BUSCA OS DADOS DO PERÍODO SELECIONADO (Faturado / Recebido do Mês/Ano)
            query = """
                SELECT cp.id, cp.consultation_id, ch.date, p.pet_name, c.first_name, cp.payment_method, cp.amount, cp.installments, cp.status
                FROM consultation_payments cp
                JOIN consultation_history ch ON cp.consultation_id = ch.id
                JOIN patients p ON ch.pet_id = p.id
                JOIN clients c ON ch.client_id = c.id
                WHERE 1=1
            """
            params = []


            if mes_idx > 0:
                mes_num = self.combo_filtro_mes.currentData()
                query += " AND SUBSTR(ch.date, 6, 2) = ?"
                params.append(mes_num)

            if ano_filtro != "Todos os Anos":
                query += " AND SUBSTR(ch.date, 1, 4) = ?"
                params.append(ano_filtro)

            query += " ORDER BY ch.date DESC, cp.consultation_id DESC, cp.id DESC"

            self.db.cursor.execute(query, tuple(params))
            registros = self.db.cursor.fetchall()

            # 2. BUSCA GERAL DE TODAS AS PENDÊNCIAS EM ABERTO (Independente de mês/ano)
            self.db.cursor.execute("""
                SELECT cp.amount 
                FROM consultation_payments cp 
                WHERE LOWER(cp.status) = 'pendente'
            """)
            pendencias_geral_db = self.db.cursor.fetchall()
            total_pendente = sum(p[0] for p in pendencias_geral_db)

            meses_dict = {
                "01": "Janeiro", "02": "Fevereiro", "03": "Março", "04": "Abril",
                "05": "Maio", "06": "Junho", "07": "Julho", "08": "Agosto",
                "09": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro"
            }

            consultas_dict = {}
            for pay_id, consult_id, data_atend, pet_name, client_name, metodo, valor, parcelas, status in registros:
                if consult_id not in consultas_dict:
                    consultas_dict[consult_id] = {
                        "consultation_id": consult_id,
                        "date": data_atend,
                        "pet_tutor": f"{pet_name} ({client_name})",
                        "status": status,
                        "pagamentos": []
                    }
                
                if metodo and metodo.lower() == "crédito parcelado" and parcelas and parcelas > 1:
                    detalhe_metodo = f"{metodo} ({parcelas}x)"
                else:
                    detalhe_metodo = metodo if metodo else "Outros"
                
                val_fmt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                consultas_dict[consult_id]["pagamentos"].append({
                    "id": pay_id,
                    "texto": detalhe_metodo,
                    "valor_str": val_fmt,
                    "valor_num": valor,
                    "status": status
                })

            for dados in consultas_dict.values():
                dados["status"] = "Pendente" if any((p["status"] or "").lower() == "pendente" for p in dados["pagamentos"]) else "Pago"
            if status_filtro == "Apenas Entradas":
                consultas_dict = {k:v for k,v in consultas_dict.items() if v["status"] == "Pago"}
            elif status_filtro == "Apenas Pendências":
                consultas_dict = {k:v for k,v in consultas_dict.items() if v["status"] == "Pendente"}
            self.tabela_extrato.clearSpans()
            linhas_processadas = []
            mes_atual_controle = None

            for consult_id, dados_cons in consultas_dict.items():
                data_atend = dados_cons["date"]
                partes = data_atend.split("-") 
                if len(partes) == 3:
                    ano, mes_num, dia = partes[0], partes[1], partes[2]
                    data_fmt = f"{dia}/{mes_num}/{ano}"
                else:
                    data_fmt = data_atend
                    mes_num = "00"

                if mes_num != mes_atual_controle:
                    mes_atual_controle = mes_num
                    nome_mes_extenso = meses_dict.get(mes_num, "Mês")
                    linhas_processadas.append((True, f"— {nome_mes_extenso} —"))

                linhas_processadas.append((False, dados_cons))

            self.tabela_extrato.setRowCount(len(linhas_processadas))
            
            for row_idx, (is_separator, dados) in enumerate(linhas_processadas):
                if is_separator:
                    item_div = QTableWidgetItem(dados)
                    item_div.setBackground(QColor("#2d3748"))
                    item_div.setForeground(QColor("#ffffff"))
                    font = item_div.font()
                    font.setBold(False)
                    item_div.setFont(font)
                    item_div.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    self.tabela_extrato.setItem(row_idx, 0, item_div)
                    for c in range(1, 5):
                        self.tabela_extrato.setItem(row_idx, c, QTableWidgetItem(""))
                    
                    self.tabela_extrato.setSpan(row_idx, 0, 1, 5)
                else:
                    dados_cons = dados
                    data_atend = dados_cons["date"]
                    partes = data_atend.split("-")
                    data_fmt = f"{partes[2]}/{partes[1]}/{partes[0]}" if len(partes) == 3 else data_atend

                    pags = dados_cons["pagamentos"]
                    
                    lista_metodos = " + ".join(p["texto"] for p in pags)
                    total = sum(p["valor_num"] for p in pags)
                    lista_valores = f"{total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    if len(pags) > 1:
                        detalhes = " + ".join(f'{p["valor_str"].removeprefix("R$ ")} {p["texto"]}' for p in pags)
                        lista_valores += f" ({detalhes})"

                    item_id = QTableWidgetItem(data_fmt)
                    item_id.setData(Qt.ItemDataRole.UserRole, pags[0]["id"])

                    self.tabela_extrato.setItem(row_idx, 0, item_id)
                    self.tabela_extrato.setItem(row_idx, 1, QTableWidgetItem(dados_cons["pet_tutor"]))
                    
                    item_pgto = QTableWidgetItem()
                    item_pgto.setData(Qt.ItemDataRole.DisplayRole, lista_metodos)
                    self.tabela_extrato.setItem(row_idx, 2, item_pgto)
                    
                    item_valor = QTableWidgetItem(lista_valores)
                    item_valor.setToolTip(lista_valores)
                    self.tabela_extrato.setItem(row_idx, 3, item_valor)
                    
                    status_geral = dados_cons["status"]
                    item_status = QTableWidgetItem(status_geral)
                    if status_geral and status_geral.lower() == "pendente":
                        item_status.setForeground(QColor("#ffbf00"))
                    else:
                        item_status.setForeground(QColor("#2f855a"))
                    self.tabela_extrato.setItem(row_idx, 4, item_status)

            # Cálculo do Recebido apenas para os registros exibidos no período
            total_recebido = 0
            todas_transacoes = []
            for d in consultas_dict.values():
                for p in d["pagamentos"]:
                    todas_transacoes.append(p)
                    if p["status"] and p["status"].lower() == 'pago':
                        total_recebido += p["valor_num"]

            faturamento = total_recebido

            # Atualiza o título do painel
            mes_texto = self.combo_filtro_mes.currentText()
            ano_texto = self.combo_filtro_ano.currentText()

            if mes_idx > 0 and ano_texto != "Todos os Anos":
                rotulo_periodo = f"Mês ({mes_texto.split(' - ')[1]} / {ano_texto})"
            elif mes_idx > 0:
                rotulo_periodo = f"Mês ({mes_texto.split(' - ')[1]})"
            elif ano_texto != "Todos os Anos":
                rotulo_periodo = f"Consolidado Anual ({ano_texto})"
            else:
                rotulo_periodo = "Geral (Todos os Anos e Meses)"

            self.resumo_group.setTitle(f"Indicadores — {rotulo_periodo}")

            if todas_transacoes or total_pendente > 0:
                self.lbl_fat_mes.setText(f"Faturamento: R$ {faturamento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                self.lbl_total_recebido.setText(f"Total Recebido: R$ {total_recebido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                
                # Exibe o total pendente GERAL
                pendente_str = f"R$ {total_pendente:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                self.lbl_total_pendente.setText(f"Total Pendente: {pendente_str}")
            else:
                self.lbl_fat_mes.setText("Faturamento: —")
                self.lbl_total_recebido.setText("Total Recebido: —")
                self.lbl_total_pendente.setText("Total Pendente: —")

        except Exception as e:
            print(f"Erro ao carregar dados do caixa: {e}")

    def dar_baixa_pagamento(self):
        """Altera o status de um pagamento selecionado na tabela de Pendente para Pago."""
        selected_row = self.tabela_extrato.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um item na tabela para dar baixa.")
            return
            
        item_data = self.tabela_extrato.item(selected_row, 0)
        if not item_data:
            return

        pay_id = item_data.data(Qt.ItemDataRole.UserRole)
        if not pay_id:
            QMessageBox.warning(self, "Aviso", "Selecione uma linha de lançamento válida (as linhas de divisão de mês não podem receber baixa).")
            return

        status_item = self.tabela_extrato.item(selected_row, 4)
        if status_item and status_item.text().lower() == "pago":
            QMessageBox.information(self, "Aviso", "Este pagamento já está marcado como Pago.")
            return

        try:
            self.db.cursor.execute("SELECT consultation_id FROM consultation_payments WHERE id = ?", (pay_id,))
            res = self.db.cursor.fetchone()
            if res:
                consult_id = res[0]
                self.db.cursor.execute("UPDATE consultation_payments SET status = 'Pago' WHERE consultation_id = ?", (consult_id,))
                self.db.conn.commit()
                QMessageBox.information(self, "Sucesso", "Pagamentos da consulta marcados como Pago!")
                self.carregar_dados_caixa()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao dar baixa: {e}")