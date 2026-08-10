from agent.llm_client import LLMClient

MODEL = 'LLM-Research/Meta-Llama-3.1-8B-Instruct'


class JobRecommendationAgent:
    def __init__(self, client):
        self.llm = LLMClient(client)

    def generate_recommendation(self, user_profile_evaluation, market_analysis):
        prompt = f"""请基于以下信息生成求职建议，并以JSON格式返回结果：

用户资料评价：{user_profile_evaluation}
市场分析：{market_analysis}

请使用以下JSON格式返回结果，只能返回符合格式的JSON结果，不要其他任何的内容，不要有任何解释：
{{
    "career_path": "职业发展方向分析",
    "job_advice": "具体的求职建议",
    "skills_to_improve": "需要提升的能力",
    "recommended_positions": ["推荐职位1", "推荐职位2", "推荐职位3"]
}}"""
        return self.llm.chat(
            MODEL,
            '你是一个专业的职业规划顾问。',
            prompt
        )
