from openai import OpenAI

class UserProfileAgent:
    def __init__(self, client):
        self.client = client
    def evaluate_user_profile(self, user_data):
        prompt = f"""请基于以下求职者信息进行评价：

学历：{user_data['education']}
专业：{user_data['major']}
技能特长：{user_data['skills']}
工作经验：{user_data['experience']}
职业目标：{user_data['career_goals']}
"""
        try:
            response = self.client.chat.completions.create(
                model="LLM-Research/Meta-Llama-3.1-8B-Instruct",
                messages=[
                    {'role': 'system', 'content': '你是一个专业的职业规划顾问。'},
                    {'role': 'user', 'content': prompt}
                ],
                stream=True
            )
            


            print('Received response from user_profile API')
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

            print("\nUser Profile Evaluation Result:", full_response)
            return full_response
        except Exception as e:
            print(f'Error processing API response: {str(e)}')
            raise ValueError(f"Failed to process API response: {str(e)}")