from flask import Flask, request, render_template, redirect, url_for, flash, send_file, send_from_directory
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
from flask_talisman import Talisman
import mysql.connector as mysql
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
KEY_FILE_PATH = os.path.join(BASE_DIR, 'key.dat')
CONFIG_FILE_PATH = os.path.join(BASE_DIR, 'config.json')

opened = False

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
            'host': input("Enter MySQL host (e.g., 'localhost'): "),
            'user': input("Enter MySQL username: "),
            'database': input("Enter MySQL database name: ")
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
            config["password"] = load_key()
            return config
    except Exception as e:
        print(f"[ERROR] Could not load config: {e}")
        return None

# Generate key and config files if they don't exist
generate_key_file()
generate_config_file()

# Load configuration on startup
config = load_config()

# Function to create required directories if they do not exist
def initialize_directories_and_tables(dirs):
    for dir in dirs:
        os.makedirs(dir, exist_ok=True)
        print(f"[INFO] Ensured directory exists: {dir}")
    connection = mysql.connect(**config)
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
    id VARCHAR(255) NOT NULL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    path VARCHAR(255) NOT NULL,
    description TEXT,
    author VARCHAR(255),
    checksum CHAR(64)
)
    """)
    connection.commit()
    connection.close()

def check_connection():
    """Check MySQL connection."""
    try:
        conn = mysql.connect(**config)
        conn.close()
        return True
    except mysql.Error as e:
        print(f"[ERROR] MySQL connection error: {e}")
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
    connection = mysql.connect(**config)
    cursor = connection.cursor(dictionary=True)
    
    if search_query:
        cursor.execute("SELECT * FROM books WHERE title LIKE %s OR author LIKE %s", 
                       (f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("SELECT * FROM books")
    
    books = cursor.fetchall()
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
                
                conn = mysql.connect(**config)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO books (id, title, path, description, author, checksum) VALUES (%s, %s, %s, %s, %s, %s)",
                    (checksum, title, final_file_path, description, author, checksum)
                )
                conn.commit()
                cursor.close()
                conn.close()
                
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
        conn = mysql.connect(**config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM books WHERE checksum = %s", (checksum,))
        book = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if book:
            return send_file(book['path'], as_attachment=False)
        else:
            flash("Book not found.")
            return redirect(url_for('docNotFound'))
    except Exception as e:
        flash(f"[ERROR] Could not open book: {e}")
        return redirect(url_for('docNotFound'))

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
    if check_connection():
        initialize_directories_and_tables([BASE_DIR, fileDir])
        logging.basicConfig(level=logging.INFO, filename=os.path.join(BASE_DIR, 'runtime.log'), filemode='a', 
                    format='%(asctime)s - %(levelname)s - %(message)s')
        print("[INFO] MySQL connection successful.")
        webbrowser.open_new_tab('http://localhost:9090/')
        if opened == False:
            app.run(host="127.0.0.1", port=9090, debug=False)
            opened = True
    else:
        print("[ERROR] Could not establish MySQL connection.")