from openai import OpenAI
import os
from agent.job_matching_agent import JobMatchingAgent

import json

class JobMatcher:
    def __init__(self):
        self.client = OpenAI(
            base_url='https://api-inference.modelscope.cn/v1/',
            api_key=os.getenv('OPENAI_API_KEY')  # Load from environment variable
        )
        self.job_matching_agent = JobMatchingAgent(self.client)

    def load_jobs(self):
        try:
            with open('data/jobs.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('jobs', [])
        except Exception as e:
            print(f'Error loading jobs: {str(e)}')
            return []

    def job_matching(self, user_input,user_data):
        try:
            # Load available jobs
            jobs = self.load_jobs()
            if not jobs:
                raise ValueError("No jobs available for matching")

            # Use job matching agent to find the best match
            matched_job = self.job_matching_agent.match_job(user_input, user_data,jobs)
            if not matched_job:
                raise ValueError("Failed to match jobs")


            return json.loads(matched_job)
        except Exception as e:
            print(f'Error in job matching: {str(e)}')
            raise ValueError(f"Job matching failed: {str(e)}")

