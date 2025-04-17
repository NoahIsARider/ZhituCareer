from openai import OpenAI
import os
from agent.user_profile_agent import UserProfileAgent
from agent.market_analysis_agent import MarketAnalysisAgent
from agent.job_recommendation_agent import JobRecommendationAgent
from agent.job_matching_agent import JobMatchingAgent

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

    def analyze_career(self, user_data):
        try:
            # Validate user profile evaluation
            user_profile_evaluation = self.user_profile_agent.evaluate_user_profile(user_data)
            if not user_profile_evaluation:
                raise ValueError("Failed to evaluate user profile")

            # Validate market analysis
            market_analysis = self.market_analysis_agent.analyze_market()
            if not market_analysis:
                raise ValueError("Failed to analyze market")

            # Generate and validate job recommendation
            job_recommendation = self.job_recommendation_agent.generate_recommendation(user_profile_evaluation, market_analysis)
            if not job_recommendation:
                raise ValueError("Failed to generate job recommendation")

            return job_recommendation
        except Exception as e:
            print(f'Error in career analysis: {str(e)}')
            raise ValueError(f"Career analysis failed: {str(e)}")

    def recommend_jobs(self, analysis, location=''):
        # 基于分析结果推荐职位
        jobs = [
            {
                'title': 'Python开发工程师',
                'company': '智图科技',
                'location': '北京市海淀区',
                'salary': '25k-35k',
                'description': '负责公司核心产品开发',
                'match_score': 95
            },
            {
                'title': '前端开发工程师',
                'company': '智图科技',
                'location': '上海市浦东新区',
                'salary': '20k-30k',
                'description': '负责公司前端开发工作',
                'match_score': 85
            }
        ]
        matched_jobs = self.job_matching_agent.match_job(user_input, job_search_criteria, jobs)
        return matched_jobs