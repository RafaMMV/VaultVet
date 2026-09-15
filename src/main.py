import sys
from PyQt6.QtWidgets import QApplication
from database import Database
from ui_main import MainUI

class AppController:
    def __init__(self):
        self.db = Database()
        
        # Inicializa a janela principal unificada (MainUI)
        self.window = MainUI(db=self.db)
        
        # Conecta o botão de salvar que está dentro da aba de cadastro
        self.window.register_topic_or_button = getattr(self.window, 'register_tab', None)
        if hasattr(self.window, 'register_tab') and hasattr(self.window.register_tab, 'save_button'):
            self.window.register_tab.save_button.clicked.connect(self.handle_save)

        self.window.show()

    def handle_save(self):
        # Coleta os dados do Tutor
        client_data = (
            self.window.register_tab.first_name_input.text(),
            self.window.register_tab.last_name_input.text(),
            self.window.register_tab.zip_code_input.text(),
            self.window.register_tab.address_input.text(),
            self.window.register_tab.number_input.text(),
            self.window.register_tab.complement_input.text(),
            self.window.register_tab.phone_input.text(),
            self.window.register_tab.email_input.text(),
            self.window.register_tab.emergency_name_input.text(),
            self.window.register_tab.emergency_phone_input.text(),
            self.window.register_tab.cpf_input.text(),
            self.window.register_tab.rg_input.text()
        )

        # Coleta os dados do Pet
        weight_text = self.window.register_tab.weight_input.text().lower().replace("kg", "").replace("g", "").strip()
        weight_converted = float(weight_text) if weight_text else 0.0

        pet_data = (
            self.window.register_tab.pet_name_input.text(),
            self.window.register_tab.gender_input.currentText(),
            self.window.register_tab.neutered_input.currentText(),
            self.window.register_tab.species_input.currentText(),
            self.window.register_tab.breed_input.currentText(),
            self.window.register_tab.birth_date_input.text(),
            self.window.register_tab.age_input.text(),
            weight_converted,
            self.window.register_tab.microchip_input.text()
        )

        try:
            self.db.insert_client_and_pet(client_data, pet_data)
            
            # Atualiza a lista e muda para a aba de listagem automaticamente
            if hasattr(self.window, "client_list_ui"):
                self.window.client_list_ui.load_data()
                self.window.tabs.setCurrentWidget(self.window.client_list_ui)
                
        except Exception as e:
            print("Error saving registration:", e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = AppController()
    sys.exit(app.exec())