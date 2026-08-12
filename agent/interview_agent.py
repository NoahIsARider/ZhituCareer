"""AI mock-interview agent: generates interview questions and evaluates answers.

Follows the project's two-path design: the LLM path is wrapped by
:class:`mock_interview.MockInterviewEngine`, which falls back to a
deterministic local engine when the API is unavailable.
"""

from agent.llm_client import LLMClient

MODEL = 'LLM-Research/Meta-Llama-3.1-8B-Instruct'


class InterviewAgent:
    """Generates interview questions and evaluates candidate answers."""

    def __init__(self, client):
        self.llm = LLMClient(client)

    def generate_questions(self, profile, target_position, num_questions=5):
        prompt = f"""请根据以下求职者信息，为「{target_position}」岗位生成 {num_questions} 道模拟面试题。

求职者信息：
学历：{profile.get('education', '')}
专业：{profile.get('major', '')}
技能特长：{profile.get('skills', '')}
工作经验：{profile.get('experience', '')}
职业目标：{profile.get('career_goals', '')}

要求：
1. 覆盖自我介绍、专业知识、项目经历、行为问题等维度
2. 题目难度循序渐进，贴合目标岗位
3. 只返回 JSON 结果，不要任何解释，格式如下：
{{
    "questions": [
        {{"id": 1, "question": "题目", "focus": "考察点", "expected_points": ["要点1", "要点2"]}},
        {{"id": 2, "question": "题目", "focus": "考察点", "expected_points": ["要点1", "要点2"]}}
    ]
}}"""
        return self.llm.chat(
            MODEL,
            '你是一位资深面试官，负责为求职者生成面试题目。',
            prompt
        )

    def evaluate_answer(self, question, focus, answer):
        prompt = f"""请评估求职者对下面这道面试题的回答。

面试题目：{question}
考察点：{focus}

求职者回答：
{answer}

请从专业能力、逻辑表达、岗位匹配度三个维度评估，只返回 JSON 结果，不要任何解释，格式如下：
{{
    "score": 85,
    "feedback": "对回答的总体评价（优点与亮点）",
    "suggestion": "具体的改进建议",
    "strengths": ["亮点1", "亮点2"],
    "weaknesses": ["不足1", "不足2"]
}}
其中 score 为 0-100 的整数。"""
        return self.llm.chat(
            MODEL,
            '你是一位资深面试官，负责评估求职者的面试回答。',
            prompt
        )
