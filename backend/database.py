import sqlite3
from pathlib import Path
from contextlib import contextmanager
from backend.config import DB_PATH

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_connection():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initializes the SQLite database with required tables and indexes."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Goals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL NOT NULL DEFAULT 0.0,
                deadline TEXT NOT NULL,
                email_alerts INTEGER NOT NULL DEFAULT 1,
                user_email TEXT NOT NULL,
                purpose TEXT,
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)

        # Deposits / Savings Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                note TEXT,
                date TEXT NOT NULL,
                FOREIGN KEY (goal_id) REFERENCES goals (id) ON DELETE CASCADE
            );
        """)

        # AI Recommendations history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER,
                goal_name TEXT,
                recommendation TEXT NOT NULL,
                daily_saving_target REAL,
                feasibility_score INTEGER,
                created_at TEXT NOT NULL
            );
        """)

        # Audit Alerts / Notifications log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER,
                goal_name TEXT,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                recipient_email TEXT NOT NULL,
                sent_at TEXT NOT NULL,
                status TEXT DEFAULT 'Sent'
            );
        """)

        conn.commit()
