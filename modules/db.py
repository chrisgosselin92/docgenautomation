# modules/db.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data/clients.db")


# ---------------------------
# Database setup
# ---------------------------
def create_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            birthday TEXT,
            matterid TEXT UNIQUE
        );
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS variables (
            id INTEGER PRIMARY KEY,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            var_name TEXT NOT NULL,
            var_value TEXT,
            UNIQUE(entity_type, entity_id, var_name)
        );
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS variables_meta (
            id INTEGER PRIMARY KEY,
            var_name TEXT NOT NULL UNIQUE,
            var_type TEXT DEFAULT 'string',
            description TEXT,
            category TEXT DEFAULT 'General',
            display_order INTEGER DEFAULT 0,
            is_derived INTEGER DEFAULT 0,
            derived_expression TEXT
        );
    ''')

    conn.commit()
    conn.close()


def ensure_variable_meta_columns():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("PRAGMA table_info(variables_meta)")
    cols = [r[1] for r in c.fetchall()]

    if "category" not in cols:
        c.execute("ALTER TABLE variables_meta ADD COLUMN category TEXT DEFAULT 'General'")
    if "display_order" not in cols:
        c.execute("ALTER TABLE variables_meta ADD COLUMN display_order INTEGER DEFAULT 0")
    if "is_derived" not in cols:
        c.execute("ALTER TABLE variables_meta ADD COLUMN is_derived INTEGER DEFAULT 0")
    if "derived_expression" not in cols:
        c.execute("ALTER TABLE variables_meta ADD COLUMN derived_expression TEXT")

    conn.commit()
    conn.close()


# ---------------------------
# Client CRUD
# ---------------------------
def create_client(matterid, first_name=None, last_name=None, birthday=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        '''
        INSERT INTO clients (first_name, last_name, birthday, matterid)
        VALUES (?, ?, ?, ?)
        ''',
        (first_name, last_name, birthday, matterid)
    )
    client_id = c.lastrowid
    conn.commit()
    conn.close()
    return client_id


def list_clients():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        'SELECT id, first_name, last_name, birthday, matterid FROM clients ORDER BY id'
    )
    rows = c.fetchall()
    conn.close()
    return rows


def get_client(client_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        'SELECT id, first_name, last_name, birthday, matterid FROM clients WHERE id=?',
        (client_id,)
    )
    row = c.fetchone()
    conn.close()
    return row


def delete_client(client_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM variables WHERE entity_type='client' AND entity_id=?", (client_id,))
    c.execute("DELETE FROM clients WHERE id=?", (client_id,))
    conn.commit()
    conn.close()


# ---------------------------
# Variable CRUD (values)
# ---------------------------
def set_variable(entity_type, entity_id, var_name, var_value):
    """
    Always store raw string value.
    If a dict is passed (legacy), extract the inner 'value'.
    """
    if isinstance(var_value, dict) and "value" in var_value:
        var_value = var_value["value"]

    if var_value is None:
        var_value = ""

    # Ensure it's a string for storage
    if not isinstance(var_value, str):
        var_value = str(var_value)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO variables (entity_type, entity_id, var_name, var_value)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(entity_type, entity_id, var_name)
        DO UPDATE SET var_value=excluded.var_value
    ''', (entity_type, entity_id, var_name, var_value))
    conn.commit()
    conn.close()


def get_variables(entity_type, entity_id):
    """
    Returns a dict of {var_name: value}, evaluating derived fields.
    Handles legacy dicts in var_value.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        SELECT v.var_name,
               COALESCE(v.var_value, ''),
               m.is_derived,
               m.derived_expression
        FROM variables v
        JOIN variables_meta m ON v.var_name = m.var_name
        WHERE v.entity_type=? AND v.entity_id=?
        ORDER BY m.category, m.display_order, m.var_name
    ''', (entity_type, entity_id))

    rows = c.fetchall()
    conn.close()

    values = {}
    derived = []

    for name, value, is_derived, expr in rows:
        # Fix legacy dict values
        if isinstance(value, str):
            try:
                import ast
                parsed = ast.literal_eval(value)
                if isinstance(parsed, dict) and "value" in parsed:
                    value = parsed["value"]
            except:
                pass
        if is_derived:
            derived.append((name, expr))
        else:
            values[name] = value

    # Evaluate derived fields
    for name, expr in derived:
        try:
            values[name] = str(eval(expr, {"__builtins__": {}}, values))
        except Exception:
            values[name] = ""

    return values


def get_all_variables_for_client(entity_type, entity_id):
    """
    Returns all variables defined in variables_meta, with the client's
    current value if present, otherwise an empty string.
    Fixes legacy dicts stored in var_value.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT
            m.var_name,
            m.var_type,
            m.description,
            m.category,
            m.display_order,
            m.is_derived,
            m.derived_expression,
            COALESCE(v.var_value, '') AS var_value
        FROM variables_meta m
        LEFT JOIN variables v
            ON v.var_name = m.var_name
           AND v.entity_type = ?
           AND v.entity_id = ?
        ORDER BY m.category, m.display_order, m.var_name
    """, (entity_type, entity_id))

    rows = c.fetchall()
    conn.close()

    result = {}
    for var_name, var_type, description, category, display_order, is_derived, derived_expression, var_value in rows:
        # Handle legacy dicts
        raw_val = var_value
        if isinstance(raw_val, str):
            try:
                import ast
                parsed = ast.literal_eval(raw_val)
                if isinstance(parsed, dict) and "value" in parsed:
                    raw_val = parsed["value"]
            except:
                pass

        result[var_name] = {
            "var_type": var_type,
            "description": description,
            "category": category,
            "display_order": display_order,
            "is_derived": is_derived,
            "derived_expression": derived_expression,
            "value": raw_val or ""
        }

    # Evaluate derived fields
    for var_name, data in result.items():
        if data["is_derived"] and data["derived_expression"]:
            try:
                context = {k: v["value"] for k, v in result.items()}
                data["value"] = str(eval(data["derived_expression"], {"__builtins__": {}}, context))
            except Exception:
                data["value"] = ""

    return result


# ---------------------------
# Variable metadata CRUD (connection-safe)
# ---------------------------
def set_variable_meta(
    var_name,
    var_type='string',
    description=None,
    category='General',
    display_order=0,
    is_derived=0,
    derived_expression=None,
    conn=None  # <-- optional external connection
):
    own_conn = False
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
        own_conn = True

    c = conn.cursor()
    c.execute('''
        INSERT INTO variables_meta
        (var_name, var_type, description, category, display_order, is_derived, derived_expression)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(var_name)
        DO UPDATE SET
            var_type=excluded.var_type,
            description=excluded.description,
            category=excluded.category,
            display_order=excluded.display_order,
            is_derived=excluded.is_derived,
            derived_expression=excluded.derived_expression
    ''', (
        var_name,
        var_type,
        description,
        category,
        display_order,
        is_derived,
        derived_expression
    ))

    if own_conn:
        conn.commit()
        conn.close()



def variable_exists(var_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        'SELECT 1 FROM variables_meta WHERE var_name=?',
        (var_name,)
    )
    exists = c.fetchone() is not None
    conn.close()
    return exists


def get_variable_meta(var_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT var_name, var_type, description, category,
               display_order, is_derived, derived_expression
        FROM variables_meta
        WHERE var_name=?
    ''', (var_name,))
    row = c.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "var_name": row[0],
        "var_type": row[1],
        "description": row[2],
        "category": row[3],
        "display_order": row[4],
        "is_derived": row[5],
        "derived_expression": row[6],
    }


def list_all_variable_meta():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT var_name, var_type, description, category,
               display_order, is_derived, derived_expression
        FROM variables_meta
        ORDER BY category, display_order, var_name
    ''')
    rows = c.fetchall()
    conn.close()

    return [
        {
            "var_name": r[0],
            "var_type": r[1],
            "description": r[2],
            "category": r[3],
            "display_order": r[4],
            "is_derived": r[5],
            "derived_expression": r[6],
        }
        for r in rows
    ]
