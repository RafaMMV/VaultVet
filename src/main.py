import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from database import Database
from ui_main import MainUI
from ui_client_list import ClientListUI

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VaultVet - Sistema de Gestão Veterinária")
        self.setMinimumSize(1000, 650)

        self.db = Database()
        
        # Sistema de abas para alternar entre Cadastro e Listagem
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Instancia as telas passando o banco de dados
        self.main_ui = MainUI(self)
        self.client_list_ui = ClientListUI(self, self.db)

        # Adiciona as abas na janela principal
        self.tabs.addTab(self.main_ui, "Novo Cadastro")
        self.tabs.addTab(self.client_list_ui, "Lista de Clientes e Pets")

        # Carrega os dados salvos anteriormente na tabela ao abrir o app
        self.client_list_ui.load_data()

        # Conecta o botão de salvar do formulário
        self.main_ui.save_button.clicked.connect(self.handle_save)

    def handle_save(self):
        # Coleta os dados do Tutor preenchidos no formulário
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

        # Coleta os dados do Pet preenchidos no formulário
        pet_data = (
            self.main_ui.pet_name_input.text(),
            self.main_ui.gender_input.currentText(),
            self.main_ui.neutered_input.currentText(),
            self.main_ui.species_input.currentText(),
            self.main_ui.breed_input.text(),
            self.main_ui.birth_date_input.text(),
            self.main_ui.age_input.text(),
            float(self.main_ui.weight_input.text()) if self.main_ui.weight_input.text().strip() else 0.0,
            self.main_ui.microchip_input.text()
        )

        try:
            # Salva no banco de dados SQLite usando a função que criamos
            self.db.insert_client_and_pet(client_data, pet_data)
            
            # Atualiza a tabela da outra aba e muda para ela automaticamente
            self.client_list_ui.load_data()
            self.tabs.setCurrentIndex(1)
            
        except Exception as e:
            print("Erro ao salvar cadastro:", e)

    def closeEvent(self, event):
        self.db.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())