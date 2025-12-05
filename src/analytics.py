import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "analytics.db"

def init_db():
    """Creates the analytics table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Create table to store logs
    c.execute('''CREATE TABLE IF NOT EXISTS interaction_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp DATETIME,
                  query TEXT,
                  top_ticket_id TEXT,
                  similarity_score REAL,
                  feedback INTEGER)''') # Feedback: 1 (Up), -1 (Down), 0 (None)
    conn.commit()
    conn.close()

def log_search(query, top_ticket_id, score):
    """Logs a new search query."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO interaction_logs (timestamp, query, top_ticket_id, similarity_score, feedback) VALUES (?, ?, ?, ?, ?)",
              (datetime.now(), query, top_ticket_id, score, 0))
    conn.commit()
    conn.close()

def log_feedback(query, ticket_id, feedback_value):
    """Updates the feedback for a specific query/ticket."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Find the most recent log for this ticket and query to update it
    c.execute("""UPDATE interaction_logs 
                 SET feedback = ? 
                 WHERE query = ? AND top_ticket_id = ? 
                 AND id = (SELECT MAX(id) FROM interaction_logs WHERE query = ? AND top_ticket_id = ?)""",
              (feedback_value, query, ticket_id, query, ticket_id))
    conn.commit()
    conn.close()

def get_metrics():
    """Returns a pandas DataFrame for the dashboard."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM interaction_logs", conn)
    conn.close()
    return df

# Initialize DB immediately when this script is imported
init_db()