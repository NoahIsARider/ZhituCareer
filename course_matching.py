from openai import OpenAI
import os
from agent.course_matching_agent import CourseMatchingAgent
import json

class CourseMatcher:
    def __init__(self):
        self.client = OpenAI(
            base_url='https://api-inference.modelscope.cn/v1/',
            api_key=os.getenv('OPENAI_API_KEY')  # Load from environment variable
        )
        self.course_matching_agent = CourseMatchingAgent(self.client)

    def course_matching(self, user_data, career_analysis):
        try:
            # Use course matching agent to find suitable courses
            matched_courses = self.course_matching_agent.match_courses(user_data, career_analysis)
            if not matched_courses:
                raise ValueError("Failed to match courses")

            return matched_courses
        except Exception as e:
            print(f'Error in course matching: {str(e)}')
            raise ValueError(f"Course matching failed: {str(e)}")