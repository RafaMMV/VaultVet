import os
import sqlite3

class Database:
    def __init__(self, db_name="vaultvet.db"):
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        os.makedirs(data_dir, exist_ok=True)

        self.db_path = os.path.join(data_dir, db_name)
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            print(f"Connected to database at {self.db_path}")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")

    def create_tables(self):
        """Create essential system tables with detailed fields."""
        try:
            # Clients (Tutors) table with number and complement
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT,
                    zip_code TEXT,
                    address TEXT,
                    number TEXT,
                    complement TEXT,
                    phone TEXT,
                    email TEXT,
                    emergency_contact TEXT,
                    emergency_phone TEXT,
                    cpf TEXT,
                    rg TEXT
                )
            """)

            # Patients (Pets) table with flexible age/birthdate support
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    pet_name TEXT NOT NULL,
                    gender TEXT,
                    neutered TEXT,
                    species TEXT,
                    breed TEXT,
                    birth_date TEXT,
                    age TEXT,
                    weight REAL,
                    microchip TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients (id)
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,        -- Formato "YYYY-MM-DD"
                    time TEXT NOT NULL,        -- Formato "HH:MM"
                    client_name TEXT NOT NULL,  -- Nome do Tutor
                    pet_name TEXT NOT NULL,     -- Nome do Pet
                    service_type TEXT NOT NULL  -- Ex: Consulta, Vacina, Retorno
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS consultation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pet_id INTEGER,
                    client_id INTEGER,
                    date TEXT NOT NULL,
                    notes TEXT,
                    FOREIGN KEY (pet_id) REFERENCES patients (id),
                    FOREIGN KEY (client_id) REFERENCES clients (id)
                )
            """)
                        
            self.conn.commit()
            print("Tables verified/created successfully with full attributes.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

    def salvar_historico(self, pet_id, client_id, date, notes):
        """Salva um novo registro no histórico do pet."""
        try:
            self.cursor.execute("""
                INSERT INTO consultation_history (pet_id, client_id, date, notes)
                VALUES (?, ?, ?, ?)
            """, (pet_id, client_id, date, notes))
            self.conn.commit()
            print("Histórico salvo com sucesso!")
        except sqlite3.Error as e:
            print(f"Erro ao salvar histórico: {e}")
            self.conn.rollback()

    def get_historico_by_pet_id(self, pet_id):
        """Busca todo o histórico de atendimentos de um pet específico."""
        try:
            self.cursor.execute("""
                SELECT date, notes FROM consultation_history 
                WHERE pet_id = ? 
                ORDER BY id DESC
            """, (pet_id,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro ao buscar histórico: {e}")
            return []

    def get_ultimo_historico_by_pet_id(self, pet_id):
        """Busca apenas o último atendimento anterior do pet."""
        try:
            self.cursor.execute("""
                SELECT date, notes FROM consultation_history 
                WHERE pet_id = ? 
                ORDER BY id DESC 
                LIMIT 1
            """, (pet_id,))
            return self.cursor.fetchone() 
        except sqlite3.Error as e:
            print(f"Erro ao buscar último histórico: {e}")
            return None

    def get_ultimo_historico_anterior(self, pet_id, data_referencia):
        """Busca o atendimento mais recente estritamente anterior à data selecionada no calendário."""
        try:
            self.cursor.execute("""
                SELECT id, date, notes FROM consultation_history 
                WHERE pet_id = ? AND date < ? 
                ORDER BY date DESC, id DESC 
                LIMIT 1
            """, (pet_id, data_referencia))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Erro ao buscar histórico anterior por data: {e}")
            return None

    def get_historico_do_dia(self, pet_id, data_atual):
        """Busca se já existe um atendimento salvo exatamente para o dia atual."""
        try:
            self.cursor.execute("""
                SELECT id, notes FROM consultation_history 
                WHERE pet_id = ? AND date = ?
                LIMIT 1
            """, (pet_id, data_atual))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Erro ao buscar histórico do dia: {e}")
            return None

    def atualizar_historico(self, historico_id, notes):
        """Atualiza o texto de um atendimento já salvo."""
        try:
            self.cursor.execute("""
                UPDATE consultation_history SET notes = ? WHERE id = ?
            """, (notes, historico_id))
            self.conn.commit()
            print("Histórico atualizado com sucesso!")
        except sqlite3.Error as e:
            print(f"Erro ao atualizar histórico: {e}")
            self.conn.rollback()

    def insert_client_and_pet(self, client_data, pet_data):
        """Insere um novo tutor e o pet vinculado a ele no banco de dados."""
        try:
            self.cursor.execute("""
                INSERT INTO clients (
                    first_name, last_name, zip_code, address, number, 
                    complement, phone, email, emergency_contact, 
                    emergency_phone, cpf, rg
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, client_data)
            
            client_id = self.cursor.lastrowid

            pet_data_with_client = [client_id] + list(pet_data)
            self.cursor.execute("""
                INSERT INTO patients (
                    client_id, pet_name, gender, neutered, species, 
                    breed, birth_date, age, weight, microchip
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, pet_data_with_client)
            
            self.conn.commit()
            print("Cadastro salvo com sucesso!")
        except sqlite3.Error as e:
            print(f"Erro ao inserir dados: {e}")
            self.conn.rollback()

    def insert_pet(self, client_id, pet_data):
        """Insere um novo pet vinculado a um tutor existente."""
        try:
            pet_data_with_client = [client_id] + list(pet_data)
            self.cursor.execute("""
                INSERT INTO patients (
                    client_id, pet_name, gender, neutered, species, 
                    breed, birth_date, age, weight, microchip
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, pet_data_with_client)
            self.conn.commit()
            print("Novo pet inserido com sucesso!")
        except sqlite3.Error as e:
            print(f"Erro ao inserir pet: {e}")
            self.conn.rollback()

    def update_pet(self, pet_id, pet_data):
        """Atualiza todos os dados de um paciente (pet) específico."""
        try:
            self.cursor.execute("""
                UPDATE patients 
                SET pet_name = ?, gender = ?, neutered = ?, species = ?, 
                    breed = ?, birth_date = ?, age = ?, weight = ?, microchip = ?
                WHERE id = ?
            """, list(pet_data) + [pet_id])
            self.conn.commit()
            print("Dados do pet atualizados com sucesso!")
        except sqlite3.Error as e:
            print(f"Erro ao atualizar dados do pet: {e}")
            self.conn.rollback()

    def get_all_records(self):
        """Busca a união dos dados de clientes e pacientes para a tabela."""
        try:
            self.cursor.execute("""
                SELECT c.id, c.first_name || ' ' || c.last_name, c.phone, p.pet_name, p.species
                FROM clients c
                LEFT JOIN patients p ON c.id = p.client_id
            """)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro ao buscar registros: {e}")
            return []

    def get_client_by_id(self, client_id):
        """Busca todos os campos do tutor pelo ID."""
        try:
            self.cursor.execute("""
                SELECT first_name, last_name, zip_code, address, number, 
                       complement, phone, email, emergency_contact, 
                       emergency_phone, cpf, rg
                FROM clients WHERE id = ?
            """, (client_id,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Erro ao buscar cliente por ID: {e}")
            return None

    def get_pets_by_client_id(self, client_id):
        """Busca todos os campos dos pets vinculados a um tutor."""
        try:
            self.cursor.execute("""
                SELECT id, client_id, pet_name, gender, neutered, 
                       species, breed, birth_date, age, weight, microchip 
                FROM patients WHERE client_id = ?
            """, (client_id,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro ao buscar pets do cliente: {e}")
            return []

    def delete_client(self, client_id):
        """Remove o cliente e todos os seus pets do banco de dados."""
        try:
            self.cursor.execute("DELETE FROM patients WHERE client_id = ?", (client_id,))
            self.cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            self.conn.commit()
            print("Cliente e pets removidos com sucesso!")
        except sqlite3.Error as e:
            print(f"Erro ao remover cliente: {e}")
            self.conn.rollback()

    def deletar_historico_por_id(self, historico_id):
        """Exclui um registro do histórico pelo ID."""
        try:
            self.cursor.execute("DELETE FROM consultation_history WHERE id = ?", (historico_id,))
            self.conn.commit()
            print("Histórico apagado do banco com sucesso!")
        except sqlite3.Error as e:
            print(f"Erro ao apagar histórico: {e}")
            self.conn.rollback()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    db = Database()
    db.close()