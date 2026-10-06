"""Plain stock editor with per-row quantity, expiration date and optional cost."""
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from theme import apply_widget_style
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QHeaderView, QLineEdit, QPushButton,
)

class InventoryUI(QWidget):
    stock_saved = pyqtSignal()

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.editors = {}
        self.dirty = False
        self.init_ui()
        self.reload()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        title = QLabel('Estoque de vacinas')
        title.setObjectName('inventoryTitle')
        apply_widget_style(title, "inventoryTitle")
        layout.addWidget(title)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(['Vacina', 'Quantidade', 'Vencimento', 'Custo (R$)'])
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in (1, 2, 3):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.feedback = QLabel('')
        self.feedback.setWordWrap(True)
        self.feedback.hide()
        layout.addWidget(self.feedback)
        buttons = QHBoxLayout()
        buttons.addStretch()
        save = QPushButton('Salvar')
        save.clicked.connect(self.save)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def mark_dirty(self, *_):
        self.dirty = True
        self.feedback.hide()

    def reload(self, force=False):
        # Preserve unsaved fields when changing tabs.
        if self.dirty and not force:
            return
        if self.db is None:
            self.message('Banco de dados não conectado.')
            return
        try:
            rows = self.db.list_stock_details()
        except Exception as error:
            self.message(str(error))
            return
        for controls in self.editors.values():
            for editor in controls:
                editor.hide()
        self.table.setRowCount(0)
        self.table.setRowCount(len(rows))
        self.editors = {}
        for row, (code, name, quantity, expiry, cost) in enumerate(rows):
            item = QTableWidgetItem(name)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, item)
            quantity_widget = QWidget()
            quantity_layout = QHBoxLayout(quantity_widget)
            quantity_layout.setContentsMargins(4, 3, 4, 3)
            quantity_layout.setSpacing(4)
            minus = QPushButton('−')
            minus.setFixedWidth(28)
            number = QLineEdit(str(quantity))
            number.setAlignment(Qt.AlignmentFlag.AlignCenter)
            number.setValidator(QIntValidator(-2147483647, 2147483647, number))
            plus = QPushButton('+')
            plus.setFixedWidth(28)
            minus.clicked.connect(lambda _, key=code: self.adjust(key, -1))
            plus.clicked.connect(lambda _, key=code: self.adjust(key, 1))
            quantity_layout.addWidget(minus)
            quantity_layout.addWidget(number, 1)
            quantity_layout.addWidget(plus)
            self.table.setCellWidget(row, 1, quantity_widget)
            date_input = QLineEdit()
            date_input.setPlaceholderText('DD/MM/AAAA')
            if expiry:
                date_input.setText(datetime.strptime(expiry, '%Y-%m-%d').strftime('%d/%m/%Y'))
            self.table.setCellWidget(row, 2, date_input)
            cost_input = QLineEdit('' if cost is None else f'{cost:.2f}'.replace('.', ','))
            cost_input.setAlignment(Qt.AlignmentFlag.AlignRight)
            cost_input.editingFinished.connect(lambda field=cost_input: self.format_cost(field))
            self.table.setCellWidget(row, 3, cost_input)
            self.editors[code] = (number, date_input, cost_input)
            for editor in self.editors[code]:
                editor.textChanged.connect(self.mark_dirty)
        self.dirty = False
        self.feedback.hide()

    def format_cost(self, field):
        """Format currency on Enter or focus loss without shifting decimal places."""
        text = field.text().strip()
        if not text:
            return
        cleaned = text.replace('R$', '').replace(' ', '')
        if ',' in cleaned:
            cleaned = cleaned.replace('.', '').replace(',', '.')
        try:
            value = Decimal(cleaned)
            if not value.is_finite():
                return
            formatted = format(value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), '.2f').replace('.', ',')
        except InvalidOperation:
            # Leave invalid input intact so Save can report the validation error.
            return
        if field.text() != formatted:
            field.setText(formatted)

    def adjust(self, code, change):
        number = self.editors[code][0]
        try:
            value = int(number.text()) + change
            if not -2147483647 <= value <= 2147483647:
                raise ValueError
        except ValueError:
            self.message('Informe uma quantidade inteira válida.')
            return
        number.setText(str(value))

    def message(self, text):
        self.feedback.setText(text)
        self.feedback.show()

    def save(self):
        details = {}
        try:
            for code, (number, expiry, cost) in self.editors.items():
                quantity = int(number.text().strip())
                expiry_text = expiry.text().strip()
                expiry_iso = None
                if expiry_text:
                    try:
                        expiry_iso = datetime.strptime(expiry_text, '%d/%m/%Y').date().isoformat()
                    except ValueError:
                        raise ValueError(f'{code}: informe o vencimento como DD/MM/AAAA ou deixe em branco.')
                cost_text = cost.text().strip()
                price = None
                if cost_text:
                    cleaned = cost_text.replace('R$', '').replace(' ', '')
                    if ',' in cleaned:
                        cleaned = cleaned.replace('.', '').replace(',', '.')
                    try:
                        price = float(cleaned)
                    except ValueError:
                        raise ValueError(f'{code}: informe um custo válido ou deixe em branco.')
                details[code] = (quantity, expiry_iso, price)
            self.db.set_stock_details(details)
        except Exception as error:
            self.message(str(error))
            return
        self.dirty = False
        self.feedback.hide()
        self.stock_saved.emit()
