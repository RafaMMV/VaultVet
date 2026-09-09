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
            # Clients (Tutors) table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT,
                    zip_code TEXT,
                    address TEXT,
                    phone TEXT,
                    email TEXT,
                    emergency_contact TEXT,
                    cpf TEXT,
                    rg TEXT
                )
            """)

            # Patients (Pets) table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    pet_name TEXT NOT NULL,
                    gender TEXT,
                    neutered TEXT,
                    species TEXT,
                    breed TEXT,
                    age INTEGER,
                    weight REAL,
                    microchip TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients (id)
                )
            """)
            
            self.conn.commit()
            print("Tables verified/created successfully with full attributes.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    db = Database()
    db.close()