# Library Management System

A web-based library management system built with Flask, designed to facilitate the management and distribution of e-books. This application allows users to add, search, and download books securely.

## Features

- **User Authentication**: Basic IP whitelisting for access control.
- **Book Management**: Add, search, and view e-books (PDF format).
- **File Encryption**: Secure storage of database credentials and sensitive information using encryption.
- **Content Security Policy**: Ensures secure loading of resources.
- **Responsive Design**: The user interface is mobile-friendly and adapts to various screen sizes.
- **Error Handling**: Custom error pages for user-friendly feedback.
- **Configuration Management**: Store configuration settings in a JSON file for easy management.
- **Checksum Verification**: Ensure the integrity of uploaded files using SHA-256 checksums.

## Technologies Used

- **Backend**: Python, Flask
- **Database**: MySQL
- **Encryption**: Fernet from the Cryptography library
- **Web Security**: Flask-Talisman for enhanced security
- **Frontend**: HTML, CSS (responsive design)
- **File Handling**: `werkzeug` for secure file uploads

## Getting Started

### Prerequisites

- Python 3.x
- MySQL Server
- Required Python packages (listed in requirements.txt)

### Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/SirSevrus/library-win.git
   cd library-management-system
   ```

2. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up the MySQL database:
   - Create a new database and user in MySQL.
   - Configure the database settings in the `config.json` file based on your MySQL setup.

4. Run the application:

   ```bash
   python app.py
   ```

5. Open your browser and navigate to `http://localhost:9090/`.

### Configuration

- **Configuration File**: Update `config.json` to include your MySQL host, user, and database name.
- **Encryption Key**: The application will prompt you to set up an encryption password for securing sensitive data.

### Security Considerations

- Use a strong, unique password for the database encryption.
- Ensure that the `allowed_ips` list in the application only includes trusted IPs.
- Regularly update your dependencies to patch security vulnerabilities.

## Usage

- **Adding a Book**: Click the "Add Book" link, fill out the form with the book title, author, description, and upload the PDF file.
- **Searching for Books**: Use the search bar to filter books by title or author.
- **Downloading Books**: Click on a book title to download the PDF file securely.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## Contact

For any inquiries, please contact sirsevrus@gmail.com.