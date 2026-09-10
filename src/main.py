import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from database import Database
from ui_main import MainUI
from ui_client_list import ClientListUI

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VaultVet - Veterinary Management System")
        self.setMinimumSize(1000, 650)

        self.db = Database()
        
        # Tab system to switch between Registration and Listing
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Instantiate screens passing the database
        self.main_ui = MainUI(self)
        self.client_list_ui = ClientListUI(self, self.db)

        # Add tabs to the main window
        self.tabs.addTab(self.main_ui, "Cadastro")
        self.tabs.addTab(self.client_list_ui, "Lista de Clientes")

        # Load previously saved data into the table on app startup
        self.client_list_ui.load_data()

        # Connect the form's save button
        self.main_ui.save_button.clicked.connect(self.handle_save)

    def handle_save(self):
        # Collect Tutor data filled in the form
        client_data = (
            self.main_ui.first_name_input.text(),
            self.main_ui.last_name_input.text(),
            self.main_ui.zip_code_input.text(),
            self.main_ui.address_input.text(),
            self.main_ui.number_input.text(),
            self.main_ui.complement_input.text(),
            self.main_ui.phone_input.text(),
            self.main_ui.email_input.text(),
            self.main_ui.emergency_name_input.text(),
            self.main_ui.emergency_phone_input.text(),
            self.main_ui.cpf_input.text(),
            self.main_ui.rg_input.text()
        )

        # Collect Pet data filled in the form
        weight_text = self.main_ui.weight_input.text().lower().replace("kg", "").replace("g", "").strip()
        weight_converted = float(weight_text) if weight_text else 0.0

        pet_data = (
            self.main_ui.pet_name_input.text(),
            self.main_ui.gender_input.currentText(),
            self.main_ui.neutered_input.currentText(),
            self.main_ui.species_input.currentText(),
            self.main_ui.breed_input.text(),
            self.main_ui.birth_date_input.text(),
            self.main_ui.age_input.text(),
            weight_converted,
            self.main_ui.microchip_input.text()
        )

        try:
            # Save to the SQLite database using our function
            self.db.insert_client_and_pet(client_data, pet_data)
            
            # Update the other tab's table and switch to it automatically
            self.client_list_ui.load_data()
            self.tabs.setCurrentIndex(1)
            
        except Exception as e:
            print("Error saving registration:", e)

    def closeEvent(self, event):
        self.db.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())