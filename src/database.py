import os
import sqlite3
from datetime import datetime, timedelta
import re
import math
import calendar

VACCINES = {
    'V8': 'V8', 'V10': 'V10', 'V4': 'V4 (Gatos)', 'V5': 'V5 (Gatos)',
    'Antirrábica': 'Antirrábica (Raiva)', 'Giárdia': 'Giárdia',
    'Gripe Canina': 'Gripe Canina', 'FeLV': 'FeLV (Gatos)',
}

class Database:
    def __init__(self, db_name="vaultvet.db"):
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        os.makedirs(data_dir, exist_ok=True)

        self.db_path = os.path.join(data_dir, db_name)
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
        self.initialize_inventory()

    def connect(self):
        """Connect to the SQLite database and enable foreign keys."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            # 🔴 ATIVA O SUPORTE A CHAVES ESTRANGEIRAS AQUI
            self.conn.execute("PRAGMA foreign_keys = ON;")
            self.cursor = self.conn.cursor()
            print(f"Connected to database at {self.db_path} (Foreign Keys ON)")
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

            # Patients (Pets) table with ON DELETE CASCADE added
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
                    photo_path TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,      -- Formato "YYYY-MM-DD"
                    time TEXT NOT NULL,      -- Formato "HH:MM"
                    client_name TEXT NOT NULL,  -- Nome do Tutor
                    pet_name TEXT NOT NULL,    -- Nome do Pet
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
                    appointment_id INTEGER,
                    FOREIGN KEY (pet_id) REFERENCES patients (id) ON DELETE CASCADE,
                    FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS pet_vaccines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pet_id INTEGER,
                    vaccine_name TEXT,
                    application_date TEXT,
                    next_due_date TEXT,
                    FOREIGN KEY (pet_id) REFERENCES patients (id) ON DELETE CASCADE
                )
            """)

            # Tabela de Resultados de Exames dos Pets
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS pet_exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pet_id INTEGER,
                    file_name TEXT,
                    file_path TEXT,
                    FOREIGN KEY(pet_id) REFERENCES patients(id) ON DELETE CASCADE
                )
            """)

            # Nova tabela para pagamentos divididos e valores pendentes
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS consultation_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    consultation_id INTEGER,
                    payment_method TEXT NOT NULL,
                    amount REAL NOT NULL,
                    installments INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'Pago', -- 'Pago' ou 'Pendente'
                    FOREIGN KEY (consultation_id) REFERENCES consultation_history (id) ON DELETE CASCADE
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
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Erro ao salvar histórico: {e}")
            self.conn.rollback()
            return None

    def salvar_pagamentos(self, consultation_id, pagamentos):
        """Salva a lista de pagamentos (ou divisão) de um atendimento, limpando anteriores para evitar duplicidade."""
        try:
            # Remove pagamentos anteriores da mesma consulta para evitar duplicidade ao atualizar
            self.cursor.execute("DELETE FROM consultation_payments WHERE consultation_id = ?", (consultation_id,))
            
            for pag in pagamentos:
                self.cursor.execute("""
                    INSERT INTO consultation_payments (consultation_id, payment_method, amount, installments, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (consultation_id, pag[0], pag[1], pag[2], pag[3]))
            self.conn.commit()
            print("Pagamentos salvos com sucesso!")
        except sqlite3.Error as e:
            print(f"Erro ao salvar pagamentos: {e}")
            self.conn.rollback()

    def get_valores_pendentes(self):
        """Busca todos os valores pendentes (a receber) com dados do cliente e pet."""
        try:
            self.cursor.execute("""
                SELECT p.id, c.first_name || ' ' || IFNULL(c.last_name, ''), pt.pet_name, h.date, p.amount
                FROM consultation_payments p
                JOIN consultation_history h ON p.consultation_id = h.id
                JOIN clients c ON h.client_id = c.id
                JOIN patients pt ON h.pet_id = pt.id
                WHERE p.status = 'Pendente'
            """)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro ao buscar valores pendentes: {e}")
            return []

    def quitar_pendencia(self, payment_id, novo_metodo):
        """Atualiza o status de um valor pendente para Pago."""
        try:
            self.cursor.execute("""
                UPDATE consultation_payments 
                SET status = 'Pago', payment_method = ? 
                WHERE id = ?
            """, (novo_metodo, payment_id))
            self.conn.commit()
            print("Pendência quitada com sucesso!")
        except sqlite3.Error as e:
            print(f"Erro ao quitar pendência: {e}")
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

    def get_historico_do_dia(self, pet_id, data_atual, appointment_id=None):
        """Busca se já existe um atendimento salvo exatamente para o agendamento do dia."""
        try:
            if appointment_id:
                self.cursor.execute("""
                    SELECT id, notes FROM consultation_history 
                    WHERE pet_id = ? AND date = ? AND appointment_id = ?
                    LIMIT 1
                """, (pet_id, data_atual, appointment_id))
            else:
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
        """Remove o cliente e deixa o SQLite apagar os pets e dados em cascata."""
        try:
            self.cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            self.conn.commit()
            print("Cliente e dados vinculados removidos com sucesso!")
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

    def initialize_inventory(self):
        schema = self.conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='inventory_vaccines'").fetchone()
        definition = """(code TEXT PRIMARY KEY, name TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0, expiry_date TEXT, unit_cost REAL)"""
        if schema and 'CHECK' in schema[0].upper():
            # Rebuild the old table to allow negative stock, keeping existing rows.
            if self.conn.in_transaction:
                raise RuntimeError('Finalize a transação atual antes de atualizar o estoque.')
            fk = self.conn.execute('PRAGMA foreign_keys').fetchone()[0]
            columns = {row[1] for row in self.conn.execute('PRAGMA table_info(inventory_vaccines)')}
            self.conn.execute('PRAGMA foreign_keys=OFF')
            try:
                with self.conn:
                    self.conn.execute('CREATE TABLE inventory_vaccines_update ' + definition)
                    expiry = 'expiry_date' if 'expiry_date' in columns else 'NULL'
                    cost = 'unit_cost' if 'unit_cost' in columns else 'NULL'
                    self.conn.execute('INSERT INTO inventory_vaccines_update SELECT code,name,quantity,' + expiry + ',' + cost + ' FROM inventory_vaccines')
                    self.conn.execute('DROP TABLE inventory_vaccines')
                    self.conn.execute('ALTER TABLE inventory_vaccines_update RENAME TO inventory_vaccines')
            finally:
                self.conn.execute('PRAGMA foreign_keys=' + str(fk))
        with self.conn:
            self.conn.execute('CREATE TABLE IF NOT EXISTS inventory_vaccines ' + definition)
            columns = {row[1] for row in self.conn.execute('PRAGMA table_info(inventory_vaccines)')}
            for name, kind in [('expiry_date','TEXT'),('unit_cost','REAL')]:
                if name not in columns:
                    self.conn.execute('ALTER TABLE inventory_vaccines ADD COLUMN ' + name + ' ' + kind)
            self.conn.execute('''CREATE TABLE IF NOT EXISTS consultation_vaccine_stock (
                consultation_id INTEGER NOT NULL REFERENCES consultation_history(id) ON DELETE CASCADE,
                code TEXT NOT NULL REFERENCES inventory_vaccines(code),
                vaccine_record_id INTEGER REFERENCES pet_vaccines(id) ON DELETE SET NULL,
                consumed INTEGER NOT NULL CHECK(consumed IN (0,1)),
                PRIMARY KEY(consultation_id, code))''')
            for code, name in VACCINES.items():
                self.conn.execute('INSERT OR IGNORE INTO inventory_vaccines(code,name) VALUES (?,?)', (code,name))

    def list_stock(self):
        return [(c,n,q) for c,n,q,e,p in self.list_stock_details()]

    def list_stock_details(self):
        rows = self.conn.execute('SELECT code,name,quantity,expiry_date,unit_cost FROM inventory_vaccines').fetchall()
        by_code = {row[0]:row for row in rows}
        return [by_code[code] for code in VACCINES]

    def set_stock(self, quantities):
        previous = {c:(e,p) for c,n,q,e,p in self.list_stock_details()}
        self.set_stock_details({c:(q,*previous[c]) for c,q in quantities.items()})

    def set_stock_details(self, details):
        if set(details) != set(VACCINES):
            raise ValueError('Informe as quantidades das oito vacinas.')
        for code,(quantity,expiry,cost) in details.items():
            if type(quantity) is not int or not -2147483647 <= quantity <= 2147483647:
                raise ValueError(code + ': informe uma quantidade inteira válida.')
            if expiry:
                datetime.strptime(expiry, '%Y-%m-%d')
            if cost is not None and (not math.isfinite(cost) or cost < 0):
                raise ValueError(code + ': o custo deve ser positivo ou ficar em branco.')
        with self.conn:
            self.conn.executemany('UPDATE inventory_vaccines SET quantity=?,expiry_date=?,unit_cost=? WHERE code=?',
                [(q,e,None if p is None else round(p,2),c) for c,(q,e,p) in details.items()])

    def vaccine_expiry_alerts(self, today=None):
        today = today or datetime.now().date()
        alerts = []
        for code,name,quantity,expiry,cost in self.list_stock_details():
            if not expiry:
                continue
            due = datetime.strptime(expiry, '%Y-%m-%d').date()
            month_number = due.year * 12 + due.month - 1 - 2
            year, month_zero = divmod(month_number, 12)
            month = month_zero + 1
            start = due.replace(year=year,month=month,
                day=min(due.day,calendar.monthrange(year,month)[1]))
            if start <= today <= due:
                alerts.append(name + ' — vencimento: ' + due.strftime('%d/%m/%Y'))
        return alerts

    def consultation_vaccines(self, consultation_id):
        return [r[0] for r in self.conn.execute(
            'SELECT code FROM consultation_vaccine_stock WHERE consultation_id=?', (consultation_id,))]

    def _adopt_old_vaccines(self, consultation_id, pet_id, day, notes):
        # Existing records predate stock tracking: never deduct past doses retroactively.
        lines = re.findall(r'• Vacinas Aplicadas: ([^\n]+)', notes or '')
        for code in set(c.strip() for line in lines for c in line.split(',')) & set(VACCINES):
            record = self.conn.execute('''SELECT id FROM pet_vaccines WHERE pet_id=?
                AND vaccine_name=? AND application_date=? ORDER BY id LIMIT 1''', (pet_id,code,day)).fetchone()
            self.conn.execute('''INSERT OR IGNORE INTO consultation_vaccine_stock
                (consultation_id,code,vaccine_record_id,consumed) VALUES (?,?,?,0)''',
                (consultation_id,code,record[0] if record else None))

    def save_consultation_with_stock(self, consultation_id, pet_id, client_id, day, notes, vaccines, payments):
        selected = set(vaccines)
        if not selected <= set(VACCINES):
            raise ValueError('Vacina desconhecida.')
        with self.conn:
            if consultation_id:
                old = self.conn.execute('SELECT pet_id,client_id,date,notes FROM consultation_history WHERE id=?',
                                        (consultation_id,)).fetchone()
                if not old or old[:3] != (pet_id,client_id,day):
                    raise ValueError('Atendimento não encontrado para este paciente e data.')
                self._adopt_old_vaccines(consultation_id,pet_id,day,old[3])
            else:
                # The current UI uses one attendance per patient/date. Guard repeated saves.
                old = self.conn.execute('SELECT id,notes FROM consultation_history WHERE pet_id=? AND date=?',
                                        (pet_id,day)).fetchone()
                if old:
                    consultation_id = old[0]
                    self._adopt_old_vaccines(consultation_id,pet_id,day,old[1])
                else:
                    consultation_id = self.conn.execute('''INSERT INTO consultation_history
                        (pet_id,client_id,date,notes) VALUES (?,?,?,?)''', (pet_id,client_id,day,notes)).lastrowid
            previous = {code:(record,consumed) for code,record,consumed in self.conn.execute(
                'SELECT code,vaccine_record_id,consumed FROM consultation_vaccine_stock WHERE consultation_id=?',
                (consultation_id,))}
            for code in previous.keys() - selected:
                record,consumed = previous[code]
                if consumed:
                    self.conn.execute('UPDATE inventory_vaccines SET quantity=quantity+1 WHERE code=?', (code,))
                if record:
                    self.conn.execute('DELETE FROM pet_vaccines WHERE id=?', (record,))
                self.conn.execute('DELETE FROM consultation_vaccine_stock WHERE consultation_id=? AND code=?',
                                  (consultation_id,code))
            for code in selected - previous.keys():
                changed = self.conn.execute('''UPDATE inventory_vaccines SET quantity=quantity-1
                    WHERE code=?''', (code,)).rowcount
                if not changed:
                    raise ValueError(f'Vacina não cadastrada: {VACCINES[code]}.')
                birth = self.conn.execute('SELECT birth_date FROM patients WHERE id=?',(pet_id,)).fetchone()
                puppy = False
                if birth and birth[0]:
                    try: puppy = 0 <= (datetime.now()-datetime.strptime(birth[0],'%d/%m/%Y')).days < 365
                    except ValueError: pass
                count = self.conn.execute('SELECT COUNT(*) FROM pet_vaccines WHERE pet_id=? AND vaccine_name=?',
                                          (pet_id,code)).fetchone()[0]
                applied = datetime.strptime(day,'%Y-%m-%d')
                if code != 'Antirrábica' and puppy and count < 2:
                    due = applied + timedelta(days=21)
                else:
                    try: due = applied.replace(year=applied.year+1)
                    except ValueError: due = applied.replace(year=applied.year+1,day=28)
                record = self.conn.execute('''INSERT INTO pet_vaccines
                    (pet_id,vaccine_name,application_date,next_due_date) VALUES (?,?,?,?)''',
                    (pet_id,code,day,due.strftime('%Y-%m-%d'))).lastrowid
                self.conn.execute('''INSERT INTO consultation_vaccine_stock
                    (consultation_id,code,vaccine_record_id,consumed) VALUES (?,?,?,1)''',
                    (consultation_id,code,record))
            self.conn.execute('UPDATE consultation_history SET notes=? WHERE id=?', (notes,consultation_id))
            self.conn.execute('DELETE FROM consultation_payments WHERE consultation_id=?',(consultation_id,))
            self.conn.executemany('''INSERT INTO consultation_payments
                (consultation_id,payment_method,amount,installments,status) VALUES (?,?,?,?,?)''',
                [(consultation_id,*p) for p in payments])
        return consultation_id

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    db = Database()
    db.close()