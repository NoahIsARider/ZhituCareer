from agent.llm_client import create_llm_client, get_model
from agent.user_profile_agent import UserProfileAgent
from agent.market_analysis_agent import MarketAnalysisAgent
from agent.job_recommendation_agent import JobRecommendationAgent


class CareerAnalyzer:
    def __init__(self):
        self.client = create_llm_client()
        self.model = get_model()
        self.user_profile_agent = UserProfileAgent(self.client)
        self.market_analysis_agent = MarketAnalysisAgent(self.client)
        self.job_recommendation_agent = JobRecommendationAgent(self.client)

    def analyze_career(self, user_data):
        user_profile_evaluation = self.user_profile_agent.evaluate_user_profile(user_data)
        if not user_profile_evaluation:
            raise ValueError("Failed to evaluate user profile")

        market_analysis = self.market_analysis_agent.analyze_market()
        if not market_analysis:
            raise ValueError("Failed to analyze market")

        job_recommendation = self.job_recommendation_agent.generate_recommendation(
            user_profile_evaluation, market_analysis)
        if not job_recommendation:
            raise ValueError("Failed to generate job recommendation")

        return job_recommendation
