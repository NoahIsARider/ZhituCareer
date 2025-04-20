import json

class CourseMatchingAgent:
    def __init__(self, client):
        self.client = client

    def match_courses(self, user_input, career_analysis):
        # Format user preferences and course list for the prompt
        keyword = user_input.get('keyword', '')
        
        # Load courses from JSON file
        try:
            with open('data/course.json', 'r', encoding='utf-8') as f:
                courses_data = json.load(f)
                courses = courses_data.get('courses', [])
        except Exception as e:
            print(f'Error loading courses: {str(e)}')
            return []
        
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

        try:
            response = self.client.chat.completions.create(
                model='LLM-Research/Meta-Llama-3.1-8B-Instruct',
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a helpful course recommendation assistant.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                stream=True
            )
            print('Received response from API')
            
            full_response = ''
            for chunk in response:
                if chunk is None:
                    continue
                if hasattr(chunk, 'choices') and chunk.choices and len(chunk.choices) > 0:
                    if hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta and hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        if content is not None:
                            full_response += content
                            print(content, end='', flush=True)

            if not full_response:
                raise ValueError("Empty response from API")

            # Process potential Markdown code blocks
            if '```json' in full_response:
                start = full_response.find('```json') + 7
                end = full_response.find('```', start)
                if end != -1:
                    full_response = full_response[start:end].strip()
            elif '```' in full_response:
                start = full_response.find('```') + 3
                end = full_response.find('```', start)
                if end != -1:
                    full_response = full_response[start:end].strip()

            print("\nCourse Recommendation Result:", full_response)
            return full_response

        except Exception as e:
            print(f'Error processing API response: {str(e)}')
            raise ValueError(f"Failed to process API response: {str(e)}")