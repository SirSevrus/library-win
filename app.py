from flask import Flask, request, render_template, redirect, url_for, flash, send_file, send_from_directory
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
from flask_talisman import Talisman
import mysql.connector as mysql
import hashlib
import shutil
import json
import os
import pickle
import tempfile
import random
import string

app = Flask(__name__)

# Content Security Policy
csp = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net"],
    'style-src': ["'self'", "https://fonts.googleapis.com"],
    'img-src': ["'self'", "data:", "https://cdn.wallpapersafari.com"],
    'font-src': ["'self'", "https://fonts.gstatic.com"],
}
Talisman(app, content_security_policy=csp, force_https=False)

app.secret_key = os.environ.get('SECRET_KEY', 'myappsSecretKey129489585675964872568423572896fycbmdfhdjgfk')
allowed_ips = ['172.31.192.1']
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB

key, data = None, []
config = {}

# Path for storing sensitive files
BASE_DIR = '/etc/library'  # Change as needed
fileDir = '/opt/library/files'
KEY_FILE_PATH = os.path.join(BASE_DIR, 'key.dat')
CONFIG_FILE_PATH = os.path.join(BASE_DIR, 'config.json')

def __init__(dirs: list):
    for dir in dirs:
        try:
            print(f"[+] Creating Directory : {dir}")
            os.makedirs(dir)
        except FileExistsError:
            print(f"[+] Directory Exists Already : {dir}")
            pass

__init__([BASE_DIR, '/opt/library', '/opt/library/files'])

def generate_key_file():
    """Generate encryption key and save encrypted password to key.dat if not exists."""
    if not os.path.exists(KEY_FILE_PATH):
        print("Encryption key file not found. Creating a new one.")
        password = input("Enter a password for the database encryption: ").encode()
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        encrypted_password = cipher_suite.encrypt(password)
        
        # Save key and encrypted password to key.dat
        with open(KEY_FILE_PATH, "wb") as file:
            pickle.dump((key, [encrypted_password]), file)
        print("Encryption key and password saved to key.dat")

def generate_config_file():
    """Generate config.json if it does not exist by prompting user input."""
    if not os.path.exists(CONFIG_FILE_PATH):
        print("Configuration file not found. Creating a new one.")
        config['host'] = input("Enter MySQL host (e.g., 'localhost'): ")
        config['user'] = input("Enter MySQL username: ")
        config['database'] = input("Enter MySQL database name: ")
        
        # Save config without password first, will add encrypted password next
        with open(CONFIG_FILE_PATH, "w") as file:
            json.dump(config, file)
        print("Configuration saved to config.json")

def load_key():
    """Load encryption key and decrypt password."""
    global key, data
    try:
        with open(KEY_FILE_PATH, "rb") as file:
            key, data = pickle.load(file)
            cipher_suite = Fernet(key)
            return cipher_suite.decrypt(data[0]).decode()
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def load_config():
    """Load configuration from file and include decrypted password."""
    global config
    try:
        with open(CONFIG_FILE_PATH) as file:
            config = json.load(file)
            config["password"] = load_key()
    except Exception as e:
        print(f"[ERROR] {e}")

# Generate key and config files if they don't exist
generate_key_file()
generate_config_file()
# Load configuration on startup
load_config()

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

@app.route('/')
def home():
    search_query = request.args.get('search', '').strip()
    client_ip = request.remote_addr
    connection = mysql.connect(**config)
    cursor = connection.cursor(dictionary=True)
    
    if search_query:
        cursor.execute("""SELECT * FROM books WHERE title LIKE %s OR author LIKE %s""", 
                       (f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("SELECT * FROM books")
    
    books = cursor.fetchall()
    cursor.close()
    connection.close()
    can_add_book = client_ip in allowed_ips

    return render_template('home.html', books=books, can_add_book=can_add_book)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

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
                target_directory = fileDir
                os.makedirs(target_directory, exist_ok=True)
                final_file_path = os.path.join(target_directory, f"{checksum}.pdf")
                
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

@app.route('/DocumentNotFound')
def docNotFound():
    return render_template('docNotFound.html')

@app.errorhandler(413)
def request_entity_too_large(error):
    flash("File is too large. Please upload a file smaller than 500 MB.")
    return redirect(url_for('add_book'))

if __name__ == '__main__':
    if check_connection():
        print("[INFO] MySQL connection successful.")
        app.run(host="0.0.0.0", port=80, debug=False)
    else:
        print("[ERROR] Could not establish MySQL connection.")
