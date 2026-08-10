import json
import os

DEFAULT_BASE_URL = 'https://api-inference.modelscope.cn/v1/'
DEFAULT_MODEL = 'LLM-Research/Meta-Llama-3.1-8B-Instruct'


def create_llm_client():
    """基于环境变量创建 OpenAI 兼容客户端。

    未配置 API Key 时允许客户端创建（使用占位符），
    实际调用会在运行时抛出清晰错误，保证应用其余功能可用。
    """
    from openai import OpenAI
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key:
        print('[warn] OPENAI_API_KEY 未配置，AI 分析功能将不可用')
        api_key = 'not-configured'
    return OpenAI(
        base_url=os.getenv('LLM_BASE_URL', DEFAULT_BASE_URL),
        api_key=api_key
    )


def get_model():
    return os.getenv('LLM_MODEL', DEFAULT_MODEL)


class LLMClient:
    """封装 OpenAI 兼容客户端与统一的流式响应处理。"""

    def __init__(self, client):
        self.client = client

    def chat(self, model, system, user):
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': user}
                ],
                stream=True
            )
        except Exception as e:
            raise ValueError(f'API request failed: {e}')

        full_response = ''
        for chunk in response:
            if chunk is None:
                continue
            choices = getattr(chunk, 'choices', None)
            if not choices:
                continue
            delta = getattr(choices[0], 'delta', None)
            content = getattr(delta, 'content', None)
            if content:
                full_response += content

        full_response = full_response.strip()
        if not full_response:
            raise ValueError('Empty response from API')
        return full_response

    @staticmethod
    def strip_code_fence(text):
        """去除模型输出中可能存在的 Markdown 代码块包裹。"""
        text = text.strip()
        if '```json' in text:
            start = text.find('```json') + 7
            end = text.find('```', start)
            if end != -1:
                return text[start:end].strip()
        elif '```' in text:
            start = text.find('```') + 3
            end = text.find('```', start)
            if end != -1:
                return text[start:end].strip()
        return text

    def parse_json(self, text):
        """解析模型输出的 JSON，自动剥离代码块；失败时抛出 ValueError。"""
        cleaned = self.strip_code_fence(text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            raise ValueError('Model returned invalid JSON')
