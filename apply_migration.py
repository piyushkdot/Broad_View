import sqlite3


def apply_migration():
    conn = sqlite3.connect('blogs.db')
    cursor = conn.cursor()

    with open('migrations/create_user_table.sql', 'r') as f:
        cursor.executescript(f.read())

    conn.commit()
    conn.close()
    print("Migration Applied Successfully!")


if __name__ == '__main__':
    apply_migration()
