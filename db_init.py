import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def initialize_database():
    # Connect to MySQL server
    mydb = pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

    # Create cursor object
    mycursor = mydb.cursor()

    # Create database
    mycursor.execute("CREATE DATABASE IF NOT EXISTS zhitu_career")
    mycursor.execute("USE zhitu_career")

    # Create jobs table and related tables
    mycursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INT PRIMARY KEY,
        title VARCHAR(255),
        company VARCHAR(255),
        location VARCHAR(255),
        salary VARCHAR(100),
        description TEXT
    )
    """)

    mycursor.execute("""
    CREATE TABLE IF NOT EXISTS job_requirements (
        id INT AUTO_INCREMENT PRIMARY KEY,
        job_id INT,
        requirement TEXT,
        FOREIGN KEY (job_id) REFERENCES jobs(id)
    )
    """)

    # Create courses table and related tables
    mycursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id VARCHAR(50) PRIMARY KEY,
        title VARCHAR(255),
        provider VARCHAR(255),
        level VARCHAR(100),
        duration VARCHAR(100),
        price VARCHAR(100),
        description TEXT
    )
    """)

    mycursor.execute("""
    CREATE TABLE IF NOT EXISTS course_skills (
        id INT AUTO_INCREMENT PRIMARY KEY,
        course_id VARCHAR(50),
        skill VARCHAR(255),
        FOREIGN KEY (course_id) REFERENCES courses(id)
    )
    """)

    mycursor.execute("""
    CREATE TABLE IF NOT EXISTS course_career_paths (
        id INT AUTO_INCREMENT PRIMARY KEY,
        course_id VARCHAR(50),
        career_path VARCHAR(255),
        FOREIGN KEY (course_id) REFERENCES courses(id)
    )
    """)

    # Create users table
    mycursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        phone VARCHAR(20) PRIMARY KEY,
        password VARCHAR(255),
        role VARCHAR(50),
        name VARCHAR(255)
    )
    """)

    print("Database and tables created successfully!")

    # Close connection
    mycursor.close()
    mydb.close()

if __name__ == "__main__":
    initialize_database()
