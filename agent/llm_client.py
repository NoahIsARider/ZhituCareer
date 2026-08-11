import json
import os
import re
import time

DEFAULT_BASE_URL = 'https://api-inference.modelscope.cn/v1/'
DEFAULT_MODEL = 'LLM-Research/Meta-Llama-3.1-8B-Instruct'

_MAX_RETRIES = int(os.getenv('LLM_MAX_RETRIES', '2'))
_RETRY_BASE_DELAY = float(os.getenv('LLM_RETRY_BASE_DELAY', '0.5'))


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


def strip_code_fence(text):
    """去除模型输出中可能存在的 Markdown 代码块包裹。"""
    text = (text or '').strip()
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


def extract_json(text):
    """Extract the first balanced JSON array / object from arbitrary text.

    LLMs frequently wrap JSON in prose or fenced code blocks; this finds the
    leftmost structurally complete JSON container by bracket matching while
    respecting string literals (the leftmost opener is the outermost one).
    """
    text = strip_code_fence(text)
    if not text:
        return None

    obj_start = text.find('{')
    arr_start = text.find('[')
    if obj_start == -1 and arr_start == -1:
        return None
    if obj_start == -1:
        start, open_ch, close_ch = arr_start, '[', ']'
    elif arr_start == -1:
        start, open_ch, close_ch = obj_start, '{', '}'
    elif obj_start < arr_start:
        start, open_ch, close_ch = obj_start, '{', '}'
    else:
        start, open_ch, close_ch = arr_start, '[', ']'

    depth = 0
    in_str = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def _fix_trailing_commas(text):
    """Remove trailing commas before ']' / '}' — a common LLM JSON mistake."""
    return re.sub(r',\s*([\]}])', r'\1', text)


class LLMClient:
    """封装 OpenAI 兼容客户端与统一的流式响应处理。"""

    def __init__(self, client, max_retries=_MAX_RETRIES):
        self.client = client
        self.max_retries = max_retries

    def chat(self, model, system, user):
        """Send a chat request with automatic retries on transient errors."""
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return self._chat_once(model, system, user)
            except ValueError as e:
                last_error = e
                if attempt < self.max_retries:
                    time.sleep(_RETRY_BASE_DELAY * (2 ** attempt))
        raise ValueError(f'API request failed after {self.max_retries + 1} '
                         f'attempts: {last_error}')

    def _chat_once(self, model, system, user):
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

    def parse_json(self, text):
        """Parse model output JSON, stripping fences and fixing common issues.

        Returns the parsed object, or ``None`` when the text does not contain
        valid JSON (instead of raising, so callers can fall back gracefully).
        """
        candidate = extract_json(text)
        if candidate is None:
            return None
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            try:
                return json.loads(_fix_trailing_commas(candidate))
            except json.JSONDecodeError:
                return None
