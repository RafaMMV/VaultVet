#////////////////////////////////////////////////////////////
#
# By: Rafael Miguel M. Vieira
# Project made with: Qt Designer and Pyside6
# Version: 1.0.0
#
# This project can be used for study and improvement. Since this 
# is my first Python code, I want it serve as an example in the 
# future so I can see my mistakes and learn from them.
# 
# there are limitations o Qt Licenses if you want to use your products
# commercially, I recommend reading them on the official website:
# https://doc.qt.io/qtfopython/licenses.html
#
#////////////////////////////////////////////////////////////

# Import Qt Core
from qt_core import *

# Import Data Services
from services.data_services import obter_data_atual

# MAIN WINDOW
class Ui_MainWindow(object):
    def setup_ui(self, parent):
        if not parent.objectName():
            parent.setObjectName("MainWindow")

        # Set Initial Parameters
        parent.resize(1200, 720)
        parent.setMinimumSize(QSize(960, 540))

        # Set Central Widget
        self.central_frame = QFrame()

        # Create Main Layout 
        self.main_layout = QHBoxLayout(self.central_frame)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Left Menu
        self.left_menu = QFrame()
        self.left_menu.setStyleSheet("background-color: #503b5e;")
        self.left_menu.setMinimumWidth(70)
        self.left_menu.setMaximumWidth(70)

        # Content Area
        self.content = QFrame()
        self.content.setStyleSheet("background-color: #585269;")
        
        # Vertical Layout 
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(15, 15, 15, 0)
        self.content_layout.setSpacing(15)

        # Custom Clickable LineEdit Class
        class ClickableLineEdit(QLineEdit):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.released = False  
                self.setFocusPolicy(Qt.ClickFocus)

            def mousePressEvent(self, event):
                if not self.released:
                    self.released = True
                    self.setPlaceholderText("")
                super().mousePressEvent(event)

            def focusOutEvent(self, event):
                super().focusOutEvent(event)
                if self.text() == "":
                    self.setPlaceholderText("Search...")
                    self.released = False

            def keyPressEvent(self, event):
                if self.released:
                    super().keyPressEvent(event)

        # Search Bar 
        self.search_bar = ClickableLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setMinimumHeight(40)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: #a9abae;
                color: #1a1521;
                border-radius: 20px;
                padding-left: 15px;
                font-size: 14px;
            }
            QLineEdit::placeholder {
                color: #2b2233;
            }
            QLineEdit:focus {
                border: 2px solid #736c85;
            }
        """)

        # Chart Contents 
        self.chart_contents = QFrame()
        self.chart_contents_layout = QHBoxLayout(self.chart_contents)
        self.chart_contents_layout.setContentsMargins(0, 0, 0, 0)
        self.chart_contents_layout.setSpacing(0)

        # Patient Record
        self.patient_record = QFrame()
        self.patient_record.setStyleSheet("background-color: #585269;")
        self.patient_record.setMinimumWidth(270)

        # Veterinary Consultation Summary
        self.veterinary_summary = QFrame()
        self.veterinary_summary.setStyleSheet("background-color: #736c85;")
        self.veterinary_summary.setMinimumWidth(390)

        # Agenda For The Day 
        self.agenda_for_the_day = QFrame()
        self.agenda_for_the_day.setStyleSheet("background-color: #585269;")
        self.agenda_for_the_day.setMinimumWidth(230)

        # Layout Agenda For The Day
        self.agenda_layout = QVBoxLayout(self.agenda_for_the_day)
        self.agenda_layout.setContentsMargins(15, 15, 15, 15)
        self.agenda_layout.setSpacing(5)

        # Get Current Date Data
        today = obter_data_atual()

        # Date Labels
        self.label_day = QLabel(today["dia"])
        self.label_day.setStyleSheet("font-size: 42px; font-weight: bold; color: white;")
        self.label_month_week = QLabel(f"{today['mes']} • {today['semana']}")
        self.label_month_week.setStyleSheet("font-size: 13px; color: #a9abae;")

        # Add Labels to Agenda Layout
        self.agenda_layout.addWidget(self.label_day)
        self.agenda_layout.addWidget(self.label_month_week)

        # Stretch
        self.agenda_layout.addStretch()

        # ADD WIDGETS TO THE HORIZONTAL LAYOUT 
        self.chart_contents_layout.addWidget(self.patient_record, 27)
        self.chart_contents_layout.addWidget(self.veterinary_summary, 39)
        self.chart_contents_layout.addWidget(self.agenda_for_the_day, 23)

        # ADD WIDGETS TO THE VERTICAL LAYOUT 
        self.content_layout.addWidget(self.search_bar)
        self.content_layout.addWidget(self.chart_contents)

        # ADD MAIN SECTIONS TO WINDOW LAYOUT
        self.main_layout.addWidget(self.left_menu)
        self.main_layout.addWidget(self.content)

        # Set Central Widget 
        parent.setCentralWidget(self.central_frame)