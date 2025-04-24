from openai import OpenAI
import os
from agent.course_matching_agent import CourseMatchingAgent
import pymysql
from dotenv import load_dotenv

load_dotenv()

class CourseMatcher:
    def __init__(self):
        self.client = OpenAI(
            base_url='https://api-inference.modelscope.cn/v1/',
            api_key=os.getenv('OPENAI_API_KEY')  # Load from environment variable
        )
        self.course_matching_agent = CourseMatchingAgent(self.client)
        self.db = self._connect_db()

    def _connect_db(self):
        return pymysql.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database='zhitu_career'
        )

    def _load_courses_from_db(self):
        try:
            with self.db.cursor() as cursor:
                # Get base course information
                cursor.execute("""
                    SELECT id, title, provider, level, duration, 
                           price, description
                    FROM courses
                """)
                courses = cursor.fetchall()

                # Get skills for each course
                cursor.execute("""
                    SELECT course_id, skill
                    FROM course_skills
                """)
                skills = cursor.fetchall()

                # Get career paths for each course
                cursor.execute("""
                    SELECT course_id, career_path
                    FROM course_career_paths
                """)
                career_paths = cursor.fetchall()

                # Convert to list of dictionaries
                courses_list = []
                for course in courses:
                    course_dict = {
                        'id': course[0],
                        'title': course[1],
                        'provider': course[2],
                        'level': course[3],
                        'duration': course[4],
                        'price': course[5],
                        'description': course[6],
                        'skills': [],
                        'career_paths': []
                    }

                    # Add skills for this course
                    course_id = course[0]
                    course_skills = [skill[1] for skill in skills if skill[0] == course_id]
                    course_dict['skills'] = course_skills

                    # Add career paths for this course
                    course_career_paths = [path[1] for path in career_paths if path[0] == course_id]
                    course_dict['career_paths'] = course_career_paths

                    courses_list.append(course_dict)
                
                return courses_list
        except Exception as e:
            print(f'Error loading courses from database: {str(e)}')
            return []

    def load_courses(self):
        return self._load_courses_from_db()

    def course_matching(self, user_data, career_analysis):
        try:
            # Use course matching agent to find suitable courses
            matched_courses = self.course_matching_agent.match_courses(user_data, career_analysis, self.load_courses())
            if not matched_courses:
                raise ValueError("Failed to match courses")

            return matched_courses
        except Exception as e:
            print(f'Error in course matching: {str(e)}')
            raise ValueError(f"Course matching failed: {str(e)}")

    def __del__(self):
        try:
            if self.db:
                self.db.close()
        except:
            pass