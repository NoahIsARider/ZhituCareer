from openai import OpenAI
import os
from agent.job_matching_agent import JobMatchingAgent
import pymysql
from dotenv import load_dotenv
import json

load_dotenv()

class JobMatcher:
    def __init__(self):
        self.client = OpenAI(
            base_url='https://api-inference.modelscope.cn/v1/',
            api_key=os.getenv('OPENAI_API_KEY')  # Load from environment variable
        )
        self.job_matching_agent = JobMatchingAgent(self.client)
        self.db = self._connect_db()

    def _connect_db(self):
        return pymysql.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database='zhitu_career'
        )

    def _load_jobs_from_db(self):
        try:
            with self.db.cursor() as cursor:
                # Get base job information
                cursor.execute("""
                    SELECT id, title, company, location, salary, description
                    FROM jobs
                """)
                jobs = cursor.fetchall()

                # Get requirements for each job
                cursor.execute("""
                    SELECT job_id, requirement
                    FROM job_requirements
                """)
                requirements = cursor.fetchall()

                # Convert to list of dictionaries
                jobs_list = []
                for job in jobs:
                    job_dict = {
                        'id': job[0],
                        'title': job[1],
                        'company': job[2],
                        'location': job[3],
                        'salary': job[4],
                        'description': job[5],
                        'requirements': [],
                        'skills': []
                    }

                    # Add requirements for this job
                    job_id = job[0]
                    job_requirements = [req[1] for req in requirements if req[0] == job_id]
                    job_dict['requirements'] = job_requirements

                    jobs_list.append(job_dict)
                
                return jobs_list
        except Exception as e:
            print(f'Error loading jobs from database: {str(e)}')
            return []

    def load_jobs(self):
        return self._load_jobs_from_db()

    def job_matching(self, user_input, user_data):
        try:
            # Load available jobs
            jobs = self.load_jobs()
            if not jobs:
                raise ValueError("No jobs available for matching")

            # Use job matching agent to find the best match
            matched_job = self.job_matching_agent.match_job(user_input, user_data, jobs)
            if not matched_job:
                raise ValueError("Failed to match jobs")


            return json.loads(matched_job)
        except Exception as e:
            print(f'Error in job matching: {str(e)}')
            raise ValueError(f"Job matching failed: {str(e)}")

    def __del__(self):
        try:
            if self.db:
                self.db.close()
        except:
            pass
