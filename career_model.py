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

