import sqlite3
from pathlib import Path

DB_PATH = Path("data/clients.db")

# --- DB Setup ---
def create_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_variables_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS client_variables (
            id INTEGER PRIMARY KEY,
            client_id INTEGER NOT NULL,
            var_name TEXT NOT NULL,
            var_value TEXT,
            UNIQUE(client_id, var_name),
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
    ''')
    conn.commit()
    conn.close()

# --- CRUD Operations ---
def add_client(name, email="", phone=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO clients (name, email, phone) VALUES (?, ?, ?)', (name, email, phone))
    conn.commit()
    conn.close()

def list_clients():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, email, phone FROM clients')
    rows = c.fetchall()
    conn.close()
    return rows

def get_client_variables(client_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT var_name, var_value FROM client_variables WHERE client_id=?', (client_id,))
    vars = dict(c.fetchall())
    conn.close()
    return vars

def set_client_variable(client_id, var_name, var_value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO client_variables (client_id, var_name, var_value)
        VALUES (?, ?, ?)
        ON CONFLICT(client_id, var_name) DO UPDATE SET var_value=excluded.var_value
    ''', (client_id, var_name, var_value))
    conn.commit()
    conn.close()
