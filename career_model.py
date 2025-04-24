from openai import OpenAI
import os
from agent.user_profile_agent import UserProfileAgent
from agent.market_analysis_agent import MarketAnalysisAgent
from agent.job_recommendation_agent import JobRecommendationAgent
from agent.job_matching_agent import JobMatchingAgent
import pymysql
from dotenv import load_dotenv

load_dotenv()

class CareerAnalyzer:
    def __init__(self):
        self.client = OpenAI(
            base_url='https://api-inference.modelscope.cn/v1/',
            api_key=os.getenv('OPENAI_API_KEY')  # Load from environment variable
        )
        self.user_profile_agent = UserProfileAgent(self.client)
        self.market_analysis_agent = MarketAnalysisAgent(self.client)
        self.job_recommendation_agent = JobRecommendationAgent(self.client)
        self.job_matching_agent = JobMatchingAgent(self.client)
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

    def _load_career_paths_from_db(self):
        try:
            with self.db.cursor() as cursor:
                # Get career paths from course_career_paths (since they're already in the courses table)
                cursor.execute("""
                    SELECT DISTINCT career_path
                    FROM course_career_paths
                """)
                career_paths = cursor.fetchall()

                # Convert to list of dictionaries
                career_paths_list = []
                for path in career_paths:
                    path_dict = {
                        'name': path[0],
                        'description': '',
                        'requirements': [],
                        'development_path': '',
                        'skills': [],
                        'recommended_courses': []
                    }
                    career_paths_list.append(path_dict)
                
                return career_paths_list
        except Exception as e:
            print(f'Error loading career paths from database: {str(e)}')
            return []

    def analyze_career(self, user_data):
        try:
            # Load career paths and courses from database
            career_paths = self._load_career_paths_from_db()
            courses = self._load_courses_from_db()

            # Validate user profile evaluation
            user_profile_evaluation = self.user_profile_agent.evaluate_user_profile(user_data)
            if not user_profile_evaluation:
                raise ValueError("Failed to evaluate user profile")

            # Validate market analysis
            market_analysis = self.market_analysis_agent.analyze_market()
            if not market_analysis:
                raise ValueError("Failed to analyze market")

            # Generate and validate job recommendation
            job_recommendation = self.job_recommendation_agent.generate_recommendation(
                user_profile_evaluation, 
                market_analysis,
                career_paths,
                courses
            )
            if not job_recommendation:
                raise ValueError("Failed to generate job recommendation")

            return job_recommendation
        except Exception as e:
            print(f'Error in career analysis: {str(e)}')
            raise ValueError(f"Career analysis failed: {str(e)}")

    def __del__(self):
        try:
            if self.db:
                self.db.close()
        except:
            pass
