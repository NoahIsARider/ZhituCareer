from agent.llm_client import LLMClient

MODEL = 'LLM-Research/Meta-Llama-3.1-8B-Instruct'


class UserProfileAgent:
    def __init__(self, client):
        self.llm = LLMClient(client)

    def evaluate_user_profile(self, user_data):
        prompt = f"""请基于以下求职者信息进行评价：

学历：{user_data['education']}
专业：{user_data['major']}
技能特长：{user_data['skills']}
工作经验：{user_data['experience']}
职业目标：{user_data['career_goals']}
"""
        return self.llm.chat(
            MODEL,
            '你是一个专业的职业规划顾问。',
            prompt
        )
