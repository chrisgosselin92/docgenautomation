# modules/db.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data/clients.db")

# ---------------------------
# Opposing Counsel Table
# ---------------------------
def ensure_opposing_counsel_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS opposing_counsel (
            id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            service_email TEXT,
            address_street TEXT,
            address_city TEXT,
            address_state TEXT,
            address_zip TEXT,
            phone TEXT,
            fax TEXT,
            firm_name TEXT,
            bar_number TEXT,
            notes TEXT,
            UNIQUE(first_name, last_name, firm_name)
        )
    ''')
    conn.commit()
    conn.close()


def list_opposing_counsel():
    ensure_opposing_counsel_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, first_name, last_name, email, service_email, address_street, address_city, address_state, address_zip, phone, fax, firm_name, bar_number, notes FROM opposing_counsel ORDER BY last_name, first_name')
    rows = c.fetchall()
    conn.close()
    return rows


def get_opposing_counsel(counsel_id):
    ensure_opposing_counsel_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, first_name, last_name, email, service_email, address_street, address_city, address_state, address_zip, phone, fax, firm_name, bar_number, notes FROM opposing_counsel WHERE id=?', (counsel_id,))
    row = c.fetchone()
    conn.close()
    return row


def create_opposing_counsel(first_name, last_name, email=None, service_email=None, address_street=None, address_city=None, address_state=None, address_zip=None, phone=None, fax=None, firm_name=None, bar_number=None, notes=None):
    ensure_opposing_counsel_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO opposing_counsel (first_name, last_name, email, service_email, address_street, address_city, address_state, address_zip, phone, fax, firm_name, bar_number, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, service_email, address_street, address_city, address_state, address_zip, phone, fax, firm_name, bar_number, notes))
        counsel_id = c.lastrowid
        conn.commit()
        conn.close()
        return counsel_id
    except sqlite3.IntegrityError:
        conn.close()
        return None


def update_opposing_counsel(counsel_id, first_name, last_name, email=None, service_email=None, address_street=None, address_city=None, address_state=None, address_zip=None, phone=None, fax=None, firm_name=None, bar_number=None, notes=None):
    ensure_opposing_counsel_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE opposing_counsel
        SET first_name=?, last_name=?, email=?, service_email=?, address_street=?, address_city=?, address_state=?, address_zip=?, phone=?, fax=?, firm_name=?, bar_number=?, notes=?
        WHERE id=?
    ''', (first_name, last_name, email, service_email, address_street, address_city, address_state, address_zip, phone, fax, firm_name, bar_number, notes, counsel_id))
    conn.commit()
    conn.close()


def delete_opposing_counsel(counsel_id):
    ensure_opposing_counsel_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM opposing_counsel WHERE id=?", (counsel_id,))
    conn.commit()
    conn.close()


def get_opposing_counsel_by_name(first_name, last_name, firm_name=None):
    """Get opposing counsel by name"""
    ensure_opposing_counsel_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if firm_name:
        c.execute('SELECT id, first_name, last_name, email, service_email, address_street, address_city, address_state, address_zip, phone, fax, firm_name, bar_number, notes FROM opposing_counsel WHERE first_name=? AND last_name=? AND firm_name=?', (first_name, last_name, firm_name))
    else:
        c.execute('SELECT id, first_name, last_name, email, service_email, address_street, address_city, address_state, address_zip, phone, fax, firm_name, bar_number, notes FROM opposing_counsel WHERE first_name=? AND last_name=?', (first_name, last_name))
    
    row = c.fetchone()
    conn.close()
    return row


def get_opposing_counsel_variables(counsel_id):
    """Get all variables for an opposing counsel by ID - returns lowercase keys"""
    ensure_opposing_counsel_table()
    row = get_opposing_counsel(counsel_id)
    
    if not row:
        return {}
    
    # Build full name and full address
    full_name = f"{row[1]} {row[2]}".strip()  # first_name + last_name
    full_address = row[5] or ""  # address_street
    city_state_zip = f"{row[6] or ''}, {row[7] or ''} {row[8] or ''}".strip().strip(',')
    
    # Return with LOWERCASE keys for normalization
    return {
        "plaintiffattorneyfirstname".lower(): row[1] or "",
        "plaintiffattorneylastname".lower(): row[2] or "",
        "plaintiffattorneyfullname".lower(): full_name,
        "plaintiffattorneyemail".lower(): row[3] or "",
        "plaintiffattorneyeserviceemail".lower(): row[4] or "",
        "plaintifffirmaddress".lower(): full_address,
        "plaintifffirmcity".lower(): row[6] or "",
        "plaintifffirmst".lower(): row[7] or "",  # Lowercase!
        "plaintifffirmzip".lower(): row[8] or "",
        "plaintiffbusphone".lower(): row[9] or "",
        "plaintifffaxphone".lower(): row[10] or "",
        "plaintifffirmname".lower(): row[11] or "",
        "plaintiffbarnumber".lower(): row[12] or "",
        "plaintiffnotes".lower(): row[13] or "",
        "plaintifffulladdress".lower(): f"{full_address}\n{city_state_zip}".strip(),
    }












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
        matterid TEXT UNIQUE,
        opposing_counsel_id INTEGER,
        gender TEXT,
        defendant_count INTEGER DEFAULT 1,
        FOREIGN KEY (opposing_counsel_id) REFERENCES opposing_counsel(id)
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

    conn.commit()  # ADD THIS
    conn.close()   # ADD THIS
    
    ensure_concat_table()
    ensure_opposing_counsel_table()  
    ensure_variable_meta_columns()


    

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
    c.execute('SELECT id, first_name, last_name, birthday, matterid FROM clients ORDER BY id')
    rows = c.fetchall()
    conn.close()
    return rows


def get_client(client_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, first_name, last_name, birthday, matterid FROM clients WHERE id=?', (client_id,))
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
    if isinstance(var_value, dict) and "value" in var_value:
        var_value = var_value["value"]

    if var_value is None:
        var_value = ""
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
    import ast
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT var_name, is_derived, derived_expression FROM variables_meta")
    meta_rows = c.fetchall()
    meta = {name: {"is_derived": bool(is_derived), "expr": expr} for name, is_derived, expr in meta_rows}

    c.execute("SELECT var_name, COALESCE(var_value, '') FROM variables WHERE entity_type=? AND entity_id=?", (entity_type, entity_id))
    rows = c.fetchall()
    conn.close()

    values = {}
    derived = []

    for name, value in rows:
        if name not in meta:
            continue
        if isinstance(value, str):
            try:
                parsed = ast.literal_eval(value)
                if isinstance(parsed, dict) and "value" in parsed:
                    value = parsed["value"]
            except Exception:
                pass
        if meta[name]["is_derived"]:
            derived.append((name, meta[name]["expr"]))
        else:
            values[name] = value

    for name, expr in derived:
        try:
            values[name] = str(eval(expr, {"__builtins__": {}}, values))
        except Exception:
            values[name] = ""

    return values


def get_all_variables_for_client(entity_type, entity_id):
    import ast
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
        raw_val = var_value
        if isinstance(raw_val, str):
            try:
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

    for var_name, data in result.items():
        if data["is_derived"] and data["derived_expression"]:
            try:
                context = {k: v["value"] for k, v in result.items()}
                data["value"] = str(eval(data["derived_expression"], {"__builtins__": {}}, context))
            except Exception:
                data["value"] = ""

    return result


# ---------------------------
# Variable metadata CRUD
# ---------------------------
def set_variable_meta(var_name, var_type='string', description=None, category='General',
                      display_order=0, is_derived=0, derived_expression=None, conn=None):
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
    ''', (var_name, var_type, description, category, display_order, is_derived, derived_expression))
    if own_conn:
        conn.commit()
        conn.close()


def variable_exists(var_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT 1 FROM variables_meta WHERE var_name=?', (var_name,))
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


# ---------------------------
# Combo Variable support
# ---------------------------
CONCAT_TABLE = "concat_variables"

def ensure_concat_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS {CONCAT_TABLE} (
            var_name TEXT PRIMARY KEY,
            components TEXT,
            description TEXT,
            var_type TEXT,
            category TEXT,
            separator TEXT DEFAULT ' '
        )
    """)
    # Ensure column exists for old DBs
    c.execute(f"PRAGMA table_info({CONCAT_TABLE})")
    cols = [r[1] for r in c.fetchall()]
    if "separator" not in cols:
        c.execute(f"ALTER TABLE {CONCAT_TABLE} ADD COLUMN separator TEXT DEFAULT ' '")
    conn.commit()
    conn.close()


def list_all_concats():
    ensure_concat_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"SELECT var_name, components, description, var_type, category, separator FROM {CONCAT_TABLE}")
    rows = c.fetchall()
    conn.close()
    concats = []
    for r in rows:
        concats.append({
            "var_name": r[0],
            "components": r[1].split(",") if r[1] else [],
            "description": r[2],
            "var_type": r[3],
            "category": r[4],
            "separator": r[5] or " "
        })
    return concats


def set_concat_variable(var_name, components, description="", var_type="string",
                        category="Derived", separator=" "):
    ensure_concat_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"""
        INSERT INTO {CONCAT_TABLE} (var_name, components, description, var_type, category, separator)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(var_name) DO UPDATE SET
            components=excluded.components,
            description=excluded.description,
            var_type=excluded.var_type,
            category=excluded.category,
            separator=excluded.separator
    """, (var_name, ",".join(components), description, var_type, category, separator))
    conn.commit()
    conn.close()


def delete_concat_variable(var_name):
    ensure_concat_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"DELETE FROM {CONCAT_TABLE} WHERE var_name=?", (var_name,))
    conn.commit()
    conn.close()


# ---------------------------
# Convenience helpers
# ---------------------------
def get_variable_value_for_client(var_name, client_id):
    return get_variables("client", client_id).get(var_name)


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
