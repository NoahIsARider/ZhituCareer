import json
from agent.llm_client import LLMClient

MODEL = 'LLM-Research/Meta-Llama-3.1-8B-Instruct'


class CourseMatchingAgent:
    def __init__(self, client):
        self.llm = LLMClient(client)

    def match_courses(self, user_input, career_analysis, courses):
        keyword = user_input.get('keyword', '')
        courses_str = json.dumps(courses, ensure_ascii=False, indent=2)

        prompt = f"""Based on the user's career analysis and course search preferences, recommend the most suitable courses.

User Search Preference:
- Keyword: {keyword}

Career Analysis:
{career_analysis}

Available Courses:
{courses_str}

Please analyze each course's content, requirements, and career paths, then select the most suitable courses based on the user's career analysis and search preference. Return a JSON array with the following format for each recommended course:
{{
    "id": "course_id",
    "title": "course_title",
    "provider": "course_provider",
    "level": "course_level",
    "duration": "course_duration",
    "price": "course_price",
    "description": "course_description",
    "skills": ["skill1", "skill2", ...],
    "career_paths": ["path1", "path2", ...],
    "match_reason": "detailed explanation of why this course is recommended"
}}

Return only the JSON array, no other content."""
        return self.llm.chat(
            MODEL,
            'You are a helpful course recommendation assistant.',
            prompt
        )
