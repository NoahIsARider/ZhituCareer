import json
import os
from agent.llm_client import create_llm_client, LLMClient
from agent.course_matching_agent import CourseMatchingAgent


class CourseMatcher:
    def __init__(self):
        self.client = create_llm_client()
        self.course_matching_agent = CourseMatchingAgent(self.client)
        self.llm = LLMClient(self.client)

    def load_courses(self):
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'course.json')
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f).get('courses', [])
        except Exception as e:
            print(f'Error loading courses: {e}')
            return []

    def course_matching(self, user_data, career_analysis):
        courses = self.load_courses()
        matched_courses = self.course_matching_agent.match_courses(
            user_data, career_analysis, courses)
        if not matched_courses:
            raise ValueError("Failed to match courses")
        return self.llm.parse_json(matched_courses)
