import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "ride_hailing.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    # enable foreign key constraint
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


conn = get_connection()
cursor = conn.cursor()
