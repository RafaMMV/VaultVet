"""Apply styles stored in assets while retaining Qt's original widget scope."""
from pathlib import Path
import re
from functools import lru_cache

STYLE_PATH = Path(__file__).resolve().parent.parent / "assets" / "style.qss"

@lru_cache(maxsize=1)
def _read_styles():
    text = STYLE_PATH.read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    rules = {}
    for selector, key, declarations in re.findall(
        r'(QWidget|QGroupBox)\[vaultStyle="([^"\n]+)"\]\s*\{([^{}]*)\}', text
    ):
        rules[key] = ("QGroupBox {" + declarations + "}") if selector == "QGroupBox" else declarations
    return rules

def apply_widget_style(widget, key):
    """Read appearance by its QSS key without modifying layout or behavior."""
    widget.setStyleSheet(_read_styles()[key])


def _install_scrollbars(area):
    """Use explicitly painted native bars so platform/QSS overlays cannot hide them."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QScrollBar, QStyleFactory, QStyleOptionSlider, QStyle
    from PyQt6.QtGui import QPainter, QColor, QPolygon
    from PyQt6.QtCore import QPoint
    if area.property("vaultvetVisibleScrollbars"):
        return
    area.setProperty("vaultvetVisibleScrollbars", True)

    class VisibleScrollbar(QScrollBar):
        def __init__(self, orientation, parent):
            super().__init__(orientation, parent)
            self.native_style = QStyleFactory.create("Fusion")
            self.native_style.setParent(self)
            self.setStyle(self.native_style)
            if orientation == Qt.Orientation.Vertical:
                self.setFixedWidth(10)
            else:
                self.setFixedHeight(10)

        def paintEvent(self, event):
            option = QStyleOptionSlider()
            self.initStyleOption(option)
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor("#303030"))
            style = self.style()
            thumb = style.subControlRect(QStyle.ComplexControl.CC_ScrollBar, option,
                                         QStyle.SubControl.SC_ScrollBarSlider, self)
            if self.maximum() > self.minimum():
                painter.fillRect(thumb.adjusted(1, 1, -1, -1), QColor("#969696"))
            painter.setPen(QColor("#d0d0d0"))
            painter.setBrush(QColor("#d0d0d0"))
            for control, direction in ((QStyle.SubControl.SC_ScrollBarSubLine, -1),
                                       (QStyle.SubControl.SC_ScrollBarAddLine, 1)):
                rect = style.subControlRect(QStyle.ComplexControl.CC_ScrollBar, option, control, self)
                center = rect.center()
                if self.orientation() == Qt.Orientation.Vertical:
                    points = [QPoint(center.x(), center.y() + 2 * direction),
                              QPoint(center.x() - 2, center.y() - direction),
                              QPoint(center.x() + 2, center.y() - direction)]
                else:
                    points = [QPoint(center.x() + 2 * direction, center.y()),
                              QPoint(center.x() - direction, center.y() - 2),
                              QPoint(center.x() - direction, center.y() + 2)]
                painter.drawPolygon(QPolygon(points))
            painter.end()

    for orientation, old, setter in (
        (Qt.Orientation.Vertical, area.verticalScrollBar(), area.setVerticalScrollBar),
        (Qt.Orientation.Horizontal, area.horizontalScrollBar(), area.setHorizontalScrollBar),
    ):
        bar = VisibleScrollbar(orientation, area)
        bar.setRange(old.minimum(), old.maximum())
        bar.setSingleStep(old.singleStep())
        bar.setPageStep(old.pageStep())
        bar.setValue(old.value())
        setter(bar)


def apply_base_style(app):
    """Apply text defaults and install persistent scrollbar rendering."""
    from PyQt6.QtCore import QObject, QEvent
    from PyQt6.QtWidgets import QAbstractScrollArea
    class ScrollbarFilter(QObject):
        def eventFilter(self, obj, event):
            if isinstance(obj, QAbstractScrollArea) and event.type() == QEvent.Type.Show:
                _install_scrollbars(obj)
            return False
    app._vaultvet_scrollbar_filter = ScrollbarFilter(app)
    app.installEventFilter(app._vaultvet_scrollbar_filter)
    app.setStyleSheet("QWidget {" + _read_styles()["base"] + "}")
    for widget in app.allWidgets():
        if isinstance(widget, QAbstractScrollArea):
            _install_scrollbars(widget)


def compact_controls(widget):
    """Reduce spacing while retaining the original layout tree and order."""
    from PyQt6.QtWidgets import QLayout, QFormLayout, QTableWidget, QHeaderView, QAbstractScrollArea
    for area in widget.findChildren(QAbstractScrollArea):
        _install_scrollbars(area)
    for layout in widget.findChildren(QLayout):
        layout.setSpacing(4)
        if isinstance(layout, QFormLayout):
            layout.setVerticalSpacing(4)
            layout.setHorizontalSpacing(6)
        if layout.parentWidget() is not None:
            layout.setContentsMargins(6, 6, 6, 6)
    for table in widget.findChildren(QTableWidget):
        table.verticalHeader().setDefaultSectionSize(24)
        for header in (table.horizontalHeader(), table.verticalHeader()):
            font = header.font()
            font.setBold(False)
            header.setFont(font)
