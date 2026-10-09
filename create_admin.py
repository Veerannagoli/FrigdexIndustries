"""Create the first admin account interactively. Run from the backend folder."""
import getpass
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")
import mysql.connector
from werkzeug.security import generate_password_hash

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "frigdex"),
)
username = input("Admin username: ").strip()
password = getpass.getpass("Admin password (minimum 12 characters): ")
if len(password) < 12:
    raise SystemExit("Use at least 12 characters for the admin password.")
cur = conn.cursor()
cur.execute(
    "INSERT INTO admin_users (username, password_hash, is_active) VALUES (%s,%s,1) "
    "ON DUPLICATE KEY UPDATE password_hash=VALUES(password_hash), is_active=1",
    (username, generate_password_hash(password))
)
conn.commit()
cur.close()
conn.close()
print("Admin account created/updated. Keep the credentials private.")
