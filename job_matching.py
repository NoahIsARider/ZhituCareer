import json
import os
from agent.llm_client import create_llm_client, LLMClient
from agent.job_matching_agent import JobMatchingAgent


class JobMatcher:
    def __init__(self):
        self.client = create_llm_client()
        self.job_matching_agent = JobMatchingAgent(self.client)
        self.llm = LLMClient(self.client)

    def load_jobs(self):
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'jobs.json')
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('jobs', [])
        except Exception as e:
            print(f'Error loading jobs: {e}')
            return []

    def job_matching(self, user_input, user_data):
        jobs = self.load_jobs()
        if not jobs:
            raise ValueError("No jobs available for matching")

        matched_job = self.job_matching_agent.match_job(user_input, user_data, jobs)
        if not matched_job:
            raise ValueError("Failed to match jobs")

        return self.llm.parse_json(matched_job)
