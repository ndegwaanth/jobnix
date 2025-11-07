# MySQL Database Setup for JobNix

## Database Configuration

The project is now configured to use MySQL instead of PostgreSQL.

## Setup Instructions

### 1. Install MySQL

Make sure MySQL is installed and running on your system.

### 2. Create Database and User

Log into MySQL as root:
```bash
mysql -u root -p
```

Then run these SQL commands:
```sql
CREATE DATABASE jobnix CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'jobnix'@'localhost' IDENTIFIED BY 'sucess';
GRANT ALL PRIVILEGES ON jobnix.* TO 'jobnix'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Install Python Dependencies

Install the required Python packages:
```bash
pip install -r requirements.txt
```

**Note for Windows Users:**
If `mysqlclient` installation fails on Windows, you can use `pymysql` as an alternative:

```bash
pip install pymysql
```

Then add this to the top of your `settings.py` (before database configuration):
```python
import pymysql
pymysql.install_as_MySQLdb()
```

### 4. Environment Variables

Your `.env` file should have:
```
DB_NAME=jobnix
DB_USER=jobnix
DB_PASSWORD=sucess
DB_HOST=localhost
DB_PORT=3306
```
```bash
installing psycopg2
pip install psycopg2-binary
```

### 5. Run Migrations

After setting up the database, run:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser

Create an admin user:
```bash
python manage.py createsuperuser
```

Use the credentials from `.env`:
- Email: ndegwaanthony300@gmail.com
- Password: Sucess@123

### 7. Test the Connection

Run the development server:
```bash
python manage.py runserver
```

## Troubleshooting

### Issue: `mysqlclient` installation fails on Windows

**Solution:** Use `pymysql` instead:
```bash
pip uninstall mysqlclient
pip install pymysql
```

And ensure `settings.py` has:
```python
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
```

### Issue: Access denied for user

**Solution:** Make sure the user has proper permissions:
```sql
GRANT ALL PRIVILEGES ON jobnix.* TO 'jobnix'@'localhost';
FLUSH PRIVILEGES;
```

### Issue: Character set errors

**Solution:** Ensure your database uses utf8mb4:
```sql
ALTER DATABASE jobnix CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## Database Features

- UTF8MB4 encoding for full Unicode support
- Strict SQL mode for data integrity
- Automatic fallback to SQLite if MySQL is unavailable

