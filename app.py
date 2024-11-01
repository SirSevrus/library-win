from flask import Flask, request, render_template, redirect, url_for, flash, send_file, send_from_directory, make_response
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
from flask import send_file
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

# Initialize Flask app
app = Flask(__name__, static_url_path='/static', static_folder='static')
csp = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net"],
    'style-src': ["'self'", "https://fonts.googleapis.com"],
    'img-src': ["'self'", "data:", "https://cdn.wallpapersafari.com"],
    'font-src': ["'self'", "https://fonts.gstatic.com"],
}

@app.route('/<path:filename>')
def static_files(filename):
    response = make_response(send_from_directory(app.static_folder, filename))
    response.headers['Cache-Control'] = 'public, max-age=31536000'  # Cache for 1 year
    return response

# Initialize Flask-Talisman with the custom CSP
Talisman(app, content_security_policy=csp, force_https=False)
app.secret_key = 'myappsSecretKey129489585675964872568423572896fycbmdfhdjgfk'  # Replace with a strong secret key
allowed_ips = ['127.0.0.1']
# Set maximum upload size to 100 MB
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB

# Load the encryption key and database configuration
key, data = None, []
config = {}

def load_key():
    global key, data
    try:
        with open("key.dat", "rb") as file:
            key, data = pickle.load(file)
            cipher_suite = Fernet(key)
            return cipher_suite.decrypt(data[0]).decode()
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def load_config():
    global config
    try:
        with open("config.json") as file:
            config = json.load(file)
            config["password"] = load_key()
    except Exception as e:
        print(f"[ERROR] {e}")

# Load configuration on startup
load_config()

# MySQL connection checker
def check_connection():
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

# Route to display all books
@app.route('/')
def home():
    search_query = request.args.get('search', '').strip()  # Get the search query from the URL
    client_ip = request.remote_addr  # Get the client's IP address
    connection = mysql.connect(**config)
    cursor = connection.cursor(dictionary=True)
    
    # Check if there is a search term
    if search_query:
        # Use SQL LIKE for partial matches in title or author fields
        cursor.execute("""SELECT * FROM books WHERE title LIKE %s OR author LIKE %s""", 
                       (f"%{search_query}%", f"%{search_query}%"))
    else:
        # Retrieve all books if there's no search query
        cursor.execute("SELECT * FROM books")
    
    books = cursor.fetchall()
    cursor.close()
    connection.close()
    can_add_book = client_ip in allowed_ips  # Check if the client's IP is allowed

    return render_template('home.html', books=books, can_add_book=can_add_book)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/home')
def Home():
    return redirect(url_for('home'))

# Route to add a new book
@app.route('/add', methods=['GET', 'POST'])
def add_book():
    client_ip = request.remote_addr

    # Check if the client's IP is allowed
    if client_ip not in allowed_ips:
        flash("You are not authorized to access this page.")
        return render_template('notallowed.html')  # Redirect to home if unauthorized

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        author = request.form['author']
        file = request.files['file']
        
        if file and file.filename.endswith('.pdf'):
            try:
                # Step 1: Create a temporary directory with a random hash name
                temp_dir = tempfile.mkdtemp(suffix='_' + ''.join(random.choices(string.ascii_letters + string.digits, k=10)))
                
                # Step 2: Save the uploaded file to the temporary directory
                temp_file_path = os.path.join(temp_dir, secure_filename(file.filename))
                file.save(temp_file_path)
                
                # Step 3: Calculate the checksum of the saved file
                checksum = calculate_checksum(temp_file_path)
                
                # Step 4: Create the final path and move the file
                target_directory = 'files'
                os.makedirs(target_directory, exist_ok=True)
                final_file_path = os.path.join(target_directory, f"{checksum}.pdf")
                
                shutil.move(temp_file_path, final_file_path)
                
                # Step 5: Delete the temporary directory
                shutil.rmtree(temp_dir)
                
                # Step 6: Insert book record into MySQL
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
                    shutil.rmtree(temp_dir)  # Ensure temp directory is deleted in case of error
        else:
            flash("Invalid file type. Please upload a PDF.")
    
    return render_template("add_book.html")

# Route to view a book PDF
@app.route('/view/<checksum>')
def view_book_pdf(checksum):
    try:
        # Find file path from checksum
        conn = mysql.connect(**config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM books WHERE checksum = %s", (checksum,))
        book = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if book:
            # Serve the PDF file directly
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

# Error handler for large files
@app.errorhandler(413)
def request_entity_too_large(error):
    flash("File is too large. Please upload a file smaller than 100 MB.")
    return redirect(url_for('add_book'))

if __name__ == '__main__':
    # Ensure MySQL connection before starting the server
    if check_connection():
        print("[INFO] MySQL connection successful.")
        app.run(host="127.0.0.1", port=6060, debug=True)
    else:
        print("[ERROR] Could not establish MySQL connection.")
