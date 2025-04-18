from openai import OpenAI

class JobMatchingAgent:
    def __init__(self, client):
        self.client = client

    def match_job(self, user_input, job_search_criteria, available_jobs):
        # Combine user input and job search criteria
        # The available_jobs parameter should be populated with jobs from the recommend_jobs function in career_model.py
        # This ensures that the job matching process uses the recommended jobs for comparison
        combined_input = f"用户输入：{user_input}\n职位搜索条件：{job_search_criteria}"

        # Prepare prompt for job matching
        prompt = f"请基于以下用户输入和职位搜索条件，从已有职位中选择最合适的职位：\n\n{combined_input}\n\n已有职位：{available_jobs}"

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
            print('Received response from job matching API')
            
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

            if not full_response.strip():
                raise ValueError("Empty response from API")

            # Process the response to extract the best job match
            print("\nBest Job Match Result:", full_response)
            return full_response
        except Exception as e:
            print(f'Error processing API response: {str(e)}')
            raise ValueError(f"Failed to process API response: {str(e)}")