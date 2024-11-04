![](https://raw.githubusercontent.com/SirSevrus/library-win/refs/heads/main/static/favicon.ico)
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
- **Database**: SQLITE3
- **Encryption**: Fernet from the Cryptography library
- **Web Security**: Flask-Talisman for enhanced security
- **Frontend**: HTML, CSS (responsive design)
- **File Handling**: `werkzeug` for secure file uploads

## Getting Started

### Prerequisites

- Python 3.x
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
   
3. Run the application:

   ```bash
   python app.py
   ```
4. For windows:
   just run the executable directly.

### Configuration
- **Encryption Key**: The application will prompt you to set up an encryption password for securing sensitive data.

### Security Considerations

- Use a strong, unique password for the database encryption.
- Only localhost or 127.0.0.1 is allowed to add books.
- Regularly update your dependencies to patch security vulnerabilities.

## Usage

- **Adding a Book**: Click the "Add Book" link, fill out the form with the book title, author, description, and upload the PDF file.
- **Searching for Books**: Use the search bar to filter books by title or author.
- **Downloading Books**: Click on a book title to download the PDF file securely.
- **Managing Books**: **This feature is currently Unavailable, it will be added soon.**

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## Contact

For any inquiries, please contact sirsevrus@gmail.com.
