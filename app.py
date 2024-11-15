from flask import Flask, request, render_template, redirect, url_for, flash, send_file, send_from_directory
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
from flask_talisman import Talisman
import sqlite3
import hashlib
import logging
import signal
import shutil
import json
import webbrowser
import os
import pickle
import tempfile
import random
import string

app = Flask(__name__)

# Content Security Policy
csp = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net", "'unsafe-inline'"],
    'style-src': ["'self'", "https://fonts.googleapis.com", "'unsafe-inline'"],
    'img-src': ["'self'", "data:", "https://cdn.wallpapersafari.com"],
    'font-src': ["'self'", "https://fonts.gstatic.com"],
}

Talisman(app, content_security_policy=csp, force_https=False)

app.secret_key = os.environ.get('SECRET_KEY', 'myappsSecretKey129489585675964872568423572896fycbmdfhdjgfk')
allowed_ips = ['127.0.0.1']  # Adjust IP for local testing
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB

# Define base directories for the application
BASE_DIR = os.path.join(os.getenv("APPDATA"), 'library')
fileDir = os.path.join(BASE_DIR, 'files')
DB_FILE_PATH = os.path.join(BASE_DIR, 'db', 'library.db')
KEY_FILE_PATH = os.path.join(BASE_DIR, 'key.dat')
CONFIG_FILE_PATH = os.path.join(BASE_DIR, 'config.json')

def generate_key_file():
    """Generate encryption key and save encrypted password to key.dat if not exists."""
    if not os.path.exists(KEY_FILE_PATH):
        print("Encryption key file not found. Creating a new one.")
        password = input("Enter a password for the database encryption: ").encode()
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        encrypted_password = cipher_suite.encrypt(password)
        
        with open(KEY_FILE_PATH, "wb") as file:
            pickle.dump((key, [encrypted_password]), file)
        print("[INFO] Encryption key and password saved to key.dat")

def generate_config_file():
    """Generate config.json if it does not exist by prompting user input."""
    if not os.path.exists(CONFIG_FILE_PATH):
        print("Configuration file not found. Creating a new one.")
        config = {
            'database': DB_FILE_PATH  # SQLite database path
        }
        with open(CONFIG_FILE_PATH, "w") as file:
            json.dump(config, file)
        print("[INFO] Configuration saved to config.json")

def load_key():
    """Load encryption key and decrypt password."""
    try:
        with open(KEY_FILE_PATH, "rb") as file:
            key, data = pickle.load(file)
            cipher_suite = Fernet(key)
            return cipher_suite.decrypt(data[0]).decode()
    except Exception as e:
        print(f"[ERROR] Could not load key: {e}")
        return None

def load_config():
    """Load configuration from file and include decrypted password."""
    try:
        with open(CONFIG_FILE_PATH) as file:
            config = json.load(file)
            config["password"] = load_key()  # Password is not used in SQLite
            return config
    except Exception as e:
        print(f"[ERROR] Could not load config: {e}")
        return None

# Function to create required directories if they do not exist
def initialize_directories(dirs):
    for dir in dirs:
        os.makedirs(dir, exist_ok=True)
        print(f"[INFO] Ensured directory exists: {dir}")

def create_tables():
    """Create the books table in SQLite database."""
    connection = sqlite3.connect(DB_FILE_PATH)
    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS books (
        id TEXT NOT NULL PRIMARY KEY,
        title TEXT NOT NULL,
        path TEXT NOT NULL,
        description TEXT,
        author TEXT,
        checksum TEXT
    )""")
    connection.commit()
    connection.close()

def check_connection():
    """Check SQLite connection."""
    try:
        conn = sqlite3.connect(DB_FILE_PATH)
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"[ERROR] SQLite connection error: {e}")
        return False

# Calculate SHA-256 checksum for file
def calculate_checksum(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as file:
        while chunk := file.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('unknown_request.html'), 404

@app.route('/home')
def index():
    return redirect(url_for('home'))

@app.route('/')
def home():
    search_query = request.args.get('search', '').strip()
    client_ip = request.remote_addr
    connection = sqlite3.connect(DB_FILE_PATH)
    cursor = connection.cursor()
    
    if search_query:
        cursor.execute("SELECT * FROM books WHERE title LIKE ? OR author LIKE ?", 
                       (f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("SELECT * FROM books")
    
    raw_books = cursor.fetchall()
    books = []
    for row in raw_books:
        book_dict = {
            'id': row[0],
            'title': row[1],
            'path': row[2],
            'description': row[3],
            'author': row[4],
            'checksum': row[5]
        }
        books.append(book_dict)
        
    cursor.close()
    connection.close()
    can_add_book = client_ip in allowed_ips
    return render_template('home.html', books=books, can_add_book=can_add_book)

@app.route('/add', methods=['GET', 'POST'])
def add_book():
    client_ip = request.remote_addr
    if client_ip not in allowed_ips:
        flash("You are not authorized to access this page.")
        return render_template('notallowed.html')

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        author = request.form['author']
        file = request.files['file']
        
        if file and file.filename.endswith('.pdf'):
            try:
                temp_dir = tempfile.mkdtemp(suffix='_' + ''.join(random.choices(string.ascii_letters + string.digits, k=10)))
                temp_file_path = os.path.join(temp_dir, secure_filename(file.filename))
                file.save(temp_file_path)
                
                checksum = calculate_checksum(temp_file_path)
                final_file_path = os.path.join(fileDir, f"{checksum}.pdf")
                
                shutil.move(temp_file_path, final_file_path)
                shutil.rmtree(temp_dir)
                
                connection = sqlite3.connect(DB_FILE_PATH)
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO books (id, title, path, description, author, checksum) VALUES (?, ?, ?, ?, ?, ?)",
                    (checksum, title, final_file_path, description, author, checksum)
                )
                connection.commit()
                cursor.close()
                connection.close()
                
                flash("Book added successfully!")
                return redirect(url_for('home'))
            except Exception as e:
                flash(f"[ERROR] Could not add book: {e}")
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
        else:
            flash("Invalid file type. Please upload a PDF.")
    
    return render_template("add_book.html")

@app.route('/view/<checksum>')
def view_book_pdf(checksum):
    try:
        connection = sqlite3.connect(DB_FILE_PATH)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM books WHERE checksum = ?", (checksum,))
        book = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if book:
            return send_file(book[2], as_attachment=False)  # book[2] is the path
        else:
            flash("Book not found.")
            return redirect(url_for('docNotFound'))
    except Exception as e:
        flash(f"[ERROR] Could not open book: {e}")
        return redirect(url_for('docNotFound'))
    
@app.route('/manage', methods=['GET', 'POST'])
def manage_books():
    client_ip = request.remote_addr
    if client_ip not in allowed_ips:
        flash("You are not authorized to access this page.")
        return render_template('notallowed.html')

    connection = sqlite3.connect(DB_FILE_PATH)
    cursor = connection.cursor()

    # Delete book if delete request is made
    if request.method == 'POST':
        book_id = request.form.get("book_id")
        if book_id:
            cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
            book = cursor.fetchone()
            
            if book:
                # Delete book record from database
                cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
                connection.commit()

                # Delete associated PDF file from the filesystem
                pdf_path = book[2]  # book[2] contains the path to the PDF file
                print(pdf_path)
                try:
                    os.remove(pdf_path)
                    flash("Book and its PDF deleted successfully!")
                except:
                    print("[ERROR] Either the book wasn't found or any kind of permission error!")
                    flash("PDF file not found, but database record deleted.")

            else:
                flash("Book not found in database.")

        else:
            flash("Invalid book ID. Please try again.")

    # Fetch all books
    cursor.execute("SELECT * FROM books")
    raw_books = cursor.fetchall()
    books = [{
        'id': row[0],
        'title': row[1],
        'path': row[2],
        'description': row[3],
        'author': row[4],
        'checksum': row[5]
    } for row in raw_books]

    cursor.close()
    connection.close()

    return render_template("manage.html", books=books)

def terminate_self():
    pid = os.getpid()  # Get current process ID
    print(f"Terminating process with PID: {pid}")
    os.kill(pid, signal.SIGTERM)

@app.route('/settings')
def settings():
    return render_template('shutdown.html')

@app.route('/shutdown', methods=["POST"])
def shutdown():
    client_ip = request.remote_addr
    if client_ip in allowed_ips:
        terminate_self()
        return "<h1>Shutting Down</h1>"
    else:
        return "Unauthorized", 403

@app.route('/DocumentNotFound')
def docNotFound():
    return render_template('docNotFound.html')

@app.errorhandler(413)
def request_entity_too_large(error):
    flash("File is too large. Please upload a file smaller than 500 MB.")
    return redirect(url_for('add_book'))

if __name__ == '__main__':
    initialize_directories([BASE_DIR, fileDir, os.path.dirname(DB_FILE_PATH)])
    generate_key_file()
    generate_config_file()
    
    config = load_config()
    if not config:
        print("[ERROR] Failed to load configuration. Please check your config.json and key.dat files.")
        exit(1)
    
    create_tables()
    
    if check_connection():
        logging.basicConfig(
            level=logging.INFO,
            filename=os.path.join(BASE_DIR, 'runtime.log'),
            filemode='a',
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        print("[INFO] Starting server on http://localhost:9090")
        webbrowser.open_new_tab("http://localhost:9090")
        app.run(host="localhost", port=9090, debug=False)
    else:
        print("[ERROR] Could not establish database connection.")
