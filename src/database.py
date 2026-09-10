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
            
            self.conn.commit()
            print("Tables verified/created successfully with full attributes.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

    def insert_client_and_pet(self, client_data, pet_data):
        """Insere um novo tutor e o pet vinculado a ele no banco de dados."""
        try:
            # Insere os dados do tutor
            self.cursor.execute("""
                INSERT INTO clients (
                    first_name, last_name, zip_code, address, number, 
                    complement, phone, email, emergency_contact, 
                    emergency_phone, cpf, rg
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, client_data)
            
            # Pega o ID gerado automaticamente para o tutor
            client_id = self.cursor.lastrowid

            # Insere os dados do pet vinculando ao ID do tutor
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

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    db = Database()
    db.close()