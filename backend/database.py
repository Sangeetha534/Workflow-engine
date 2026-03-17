import sqlite3

DATABASE_URL = "workflow.db"

def get_db():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER,
            name TEXT,
            step_type TEXT,
            FOREIGN KEY(workflow_id) REFERENCES workflows(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_id INTEGER,
            condition TEXT,
            priority INTEGER,
            next_step_id INTEGER,
            FOREIGN KEY(step_id) REFERENCES steps(id),
            FOREIGN KEY(next_step_id) REFERENCES steps(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER,
            status TEXT,
            FOREIGN KEY(workflow_id) REFERENCES workflows(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id INTEGER,
            step_name TEXT,
            evaluated_rules TEXT,
            next_step TEXT,
            status TEXT,
            FOREIGN KEY(execution_id) REFERENCES executions(id)
        )
    ''')
    conn.commit()
    conn.close()
