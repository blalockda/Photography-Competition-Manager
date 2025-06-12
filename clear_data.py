import sqlite3

DB_PATH = 'data/competition.db'

def clear_competition_data():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Delete scores first to avoid foreign key issues
        c.execute("DELETE FROM scores")
        c.execute("DELETE FROM photos")
        c.execute("DELETE FROM categories")
        conn.commit()
        print("All competition data deleted.")

if __name__ == '__main__':
    clear_competition_data()

