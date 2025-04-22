from openai import OpenAI
import json

class JobMatchingAgent:
    def __init__(self, client):
        self.client = client

    def match_job(self, user_input, user_data,jobs):
        # Format user preferences and job list for the prompt
        keyword = user_input.get('keyword', '')
        location = user_input.get('location', '')
        career_analysis = user_input.get('career_analysis', '')
        jobs_str = json.dumps(jobs, ensure_ascii=False, indent=2)
        
        prompt = f"""请根据用户个人能力和搜索偏好，从工作列表中找出最适合的工作。

用户搜索偏好：
- 关键词：{keyword}
- 期望工作地点：{location}
**用户个人能力**：
{user_data}
职业分析结果：
{career_analysis}

可选工作列表：
{jobs_str}

请分析每个工作的要求和描述，结合用户的搜索偏好，选择最适合的工作。返回一个JSON对象，格式如下：
{{
    "title": "职位名称",
    "company": "公司名称",
    "location": "工作地点",
    "salary": "薪资范围",
    "description": "职位描述",
    "requirements": ["要求1", "要求2", ...],
    "match_reason": "为什么这个职位最适合用户的详细解释"
}}

注意：只返回一个最匹配的工作，必须是JSON格式，不要包含其他任何内容。"""
        try:
            response = self.client.chat.completions.create(
                model='LLM-Research/Meta-Llama-3.1-8B-Instruct',
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a helpful assistant.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                stream=True
            )
            print('Received response from API')
            
            full_response = ''
            for chunk in response:
                if chunk is None:
                    continue
                if hasattr(chunk, 'choices') and chunk.choices and len(chunk.choices) > 0:
                    if hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta and hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        if content is not None:
                            full_response += content
                            print(content, end='', flush=True)

            if not full_response:
                raise ValueError("Empty response from API")

            # 处理可能的Markdown代码块
            if '```json' in full_response:
                start = full_response.find('```json') + 7
                end = full_response.find('```', start)
                if end != -1:
                    full_response = full_response[start:end].strip()
            elif '```' in full_response:
                start = full_response.find('```') + 3
                end = full_response.find('```', start)
                if end != -1:
                    full_response = full_response[start:end].strip()

            print("\nJob Recommendation Result:", full_response)
            return full_response
        except Exception as e:
            print(f'Error processing API response: {str(e)}')
            raise ValueError(f"Failed to process API response: {str(e)}")
