import json
from agent.llm_client import LLMClient

MODEL = 'LLM-Research/Meta-Llama-3.1-8B-Instruct'


class JobMatchingAgent:
    def __init__(self, client):
        self.llm = LLMClient(client)

    def match_job(self, user_input, user_data, jobs):
        keyword = user_input.get('keyword', '')
        location = user_input.get('location', '')
        career_analysis = user_input.get('career_analysis', '')
        jobs_str = json.dumps(jobs, ensure_ascii=False, indent=2)

        prompt = f"""请根据用户个人能力和搜索偏好，从工作列表中找出最适合的工作。

用户搜索偏好：
- 关键词：{keyword}
- 期望工作地点：{location}
**用户个人能力**：
{json.dumps(user_data, ensure_ascii=False)}
职业分析结果：
{career_analysis}

可选工作列表：
{jobs_str}

请分析每个工作的要求和描述，结合用户的搜索偏好，选择最适合且能胜任的工作，其中每一个工作的格式如下：
{{
    "title": "职位名称",
    "company": "公司名称",
    "location": "工作地点",
    "salary": "薪资范围",
    "description": "职位描述",
    "requirements": ["要求1", "要求2", ...],
    "match_reason": "为什么这个职位最适合用户的详细解释"
}}

返回一个至两个最匹配的工作，必须是JSON格式，必须包裹在数组里面，不要包含其他任何内容。"""
        return self.llm.chat(
            MODEL,
            '你是一个专业的求职推荐助手。',
            prompt
        )
