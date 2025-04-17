from openai import OpenAI

class JobRecommendationAgent:
    def __init__(self, client):
        self.client = client

    def generate_recommendation(self, user_profile_evaluation, market_analysis):
        prompt = f"""请基于以下信息生成求职建议，并以JSON格式返回结果：

用户资料评价：{user_profile_evaluation}
市场分析：{market_analysis}

请使用以下JSON格式返回结果，**注意：只能返回符合格式的JSON结果，不要其他任何的内容，不要有任何解释：
{{
    "career_path": "职业发展方向分析",
    "job_advice": "具体的求职建议",
    "skills_to_improve": "需要提升的能力",
    "recommended_positions": ["推荐职位1", "推荐职位2", "推荐职位3"]
}}"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3-0324",
                messages=[
                    {'role': 'system', 'content': '你是一个专业的职业规划顾问。'},
                    {'role': 'user', 'content': prompt}
                ],
                stream=True
            )
            print('Received response from API')
        except Exception as api_error:
            print(f'API call error: {str(api_error)}')
            raise ValueError(f"API call failed: {str(api_error)}")

        try:
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

            print("Job Recommendation Result:", full_response)
            return full_response
        except Exception as e:
            print(f'Error processing API response: {str(e)}')
            raise ValueError(f"Failed to process API response: {str(e)}")
