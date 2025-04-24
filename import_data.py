import json
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def clear_database():
    # Connect to MySQL
    conn = pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database='zhitu_career'
    )
    cursor = conn.cursor()

    try:
        # Clear all tables
        tables = ['job_requirements', 'course_skills', 'course_career_paths', 'jobs', 'courses', 'users']
        for table in tables:
            cursor.execute(f"TRUNCATE TABLE {table}")
        conn.commit()
        print("Database cleared successfully!")
    except Exception as e:
        print(f"Error clearing database: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def import_jobs():
    # Connect to MySQL
    conn = pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database='zhitu_career'
    )
    cursor = conn.cursor()

    # Read jobs.json
    with open('data/jobs.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        jobs = data.get('jobs', [])

    # Insert jobs into database
    for job in jobs:
        try:
            # If job doesn't have an ID, generate one
            job_id = job.get('id')
            if job_id is None:
                # Generate a unique ID using title and company (hashing)
                job_id = hash(f"{job.get('title', '')}_{job.get('company', '')}") % 1000000
                job['id'] = job_id

            # Insert job
            cursor.execute("""
                INSERT INTO jobs (id, title, company, location, salary, description)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                job_id,
                job.get('title', ''),
                job.get('company', ''),
                job.get('location', ''),
                job.get('salary', ''),
                job.get('description', '')
            ))

            # Insert requirements
            requirements = job.get('requirements', [])
            for requirement in requirements:
                cursor.execute("""
                    INSERT INTO job_requirements (job_id, requirement)
                    VALUES (%s, %s)
                """, (job_id, requirement))

        except Exception as e:
            print(f"Error importing job {job.get('title', '')}: {str(e)}")

    conn.commit()
    cursor.close()
    conn.close()
    print("Jobs imported successfully!")

def import_courses():
    # Connect to MySQL
    conn = pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database='zhitu_career'
    )
    cursor = conn.cursor()

    # Read courses.json
    with open('data/course.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        courses = data.get('courses', [])

    # Insert courses into database
    for course in courses:
        try:
            # Insert course
            cursor.execute("""
                INSERT INTO courses (id, title, provider, level, duration, 
                               price, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                course.get('id', ''),
                course.get('title', ''),
                course.get('provider', ''),
                course.get('level', ''),
                course.get('duration', ''),
                course.get('price', ''),
                course.get('description', '')
            ))

            # Insert skills
            course_id = course.get('id')
            skills = course.get('skills', [])
            for skill in skills:
                cursor.execute("""
                    INSERT INTO course_skills (course_id, skill)
                    VALUES (%s, %s)
                """, (course_id, skill))

            # Insert career paths
            career_paths = course.get('career_paths', [])
            for path in career_paths:
                cursor.execute("""
                    INSERT INTO course_career_paths (course_id, career_path)
                    VALUES (%s, %s)
                """, (course_id, path))

        except Exception as e:
            print(f"Error importing course {course.get('title', '')}: {str(e)}")

    conn.commit()
    cursor.close()
    conn.close()
    print("Courses imported successfully!")

def import_users():
    # Connect to MySQL
    conn = pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database='zhitu_career'
    )
    cursor = conn.cursor()

    # Read users.json
    with open('data/users.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        users = data.get('users', [])

    # Insert users into database
    for user in users:
        try:
            cursor.execute("""
                INSERT INTO users (phone, password, role, name)
                VALUES (%s, %s, %s, %s)
            """, (
                user.get('phone', ''),
                user.get('password', ''),
                user.get('role', ''),
                user.get('name', '')
            ))
        except Exception as e:
            print(f"Error importing user {user.get('phone', '')}: {str(e)}")

    conn.commit()
    cursor.close()
    conn.close()
    print("Users imported successfully!")

def main():
    print("Starting data import...")
    clear_database()
    import_jobs()
    import_courses()
    import_users()
    print("Data import completed!")

if __name__ == "__main__":
    main()
