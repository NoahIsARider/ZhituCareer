"""Tests for the LLM client: robust JSON extraction and retry logic."""

import pytest

from agent.llm_client import LLMClient, extract_json, strip_code_fence


class TestStripCodeFence:
    def test_plain(self):
        assert strip_code_fence('hello') == 'hello'

    def test_json_fence(self):
        assert strip_code_fence('```json\n{"a":1}\n```') == '{"a":1}'

    def test_generic_fence(self):
        assert strip_code_fence('```\n[1,2]\n```') == '[1,2]'

    def test_fence_with_prose(self):
        assert strip_code_fence('Here is the result:\n```json\n{"a":1}\n```\ndone') == '{"a":1}'


class TestExtractJson:
    def test_prose_wrapped(self):
        text = '根据分析，结果如下：{"career_path": "后端"}，请查收'
        assert extract_json(text) == '{"career_path": "后端"}'

    def test_array_wrapped(self):
        assert extract_json('以下是结果 [{"title": "A"}] 结束') == '[{"title": "A"}]'

    def test_nested_braces(self):
        text = '{"a": {"b": [1, 2, {"c": "x"}]}}'
        assert extract_json(text) == text

    def test_string_containing_braces(self):
        text = '{"a": "text {with} braces", "b": 1}'
        assert extract_json(text) == text

    def test_no_json(self):
        assert extract_json('no json here') is None

    def test_empty(self):
        assert extract_json('') is None
        assert extract_json('```json\n```') is None


class TestParseJson:
    def test_valid(self):
        assert LLMClient(None).parse_json('{"a": 1}') == {'a': 1}

    def test_trailing_commas(self):
        assert LLMClient(None).parse_json('{"a": 1,}') == {'a': 1}
        assert LLMClient(None).parse_json('[1, 2,]') == [1, 2]

    def test_invalid_returns_none(self):
        assert LLMClient(None).parse_json('{not json}') is None
        assert LLMClient(None).parse_json('just words') is None
        assert LLMClient(None).parse_json(None) is None

    def test_with_prose(self):
        assert LLMClient(None).parse_json('结果：{"ok": true} 完') == {'ok': True}


class _Chunk:
    def __init__(self, content):
        self.choices = [_Choice(content)]


class _Choice:
    def __init__(self, content):
        self.delta = _Delta(content)


class _Delta:
    def __init__(self, content):
        self.content = content


class _Completions:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def create(self, **kwargs):
        response = self.responses.pop(0)
        self.calls += 1
        if callable(response):
            response()
        return response


class _FakeClient:
    def __init__(self, responses):
        self.chat = _Chat(_Completions(responses))

    @property
    def completions(self):
        return self.chat.completions


class _Chat:
    def __init__(self, completions):
        self.completions = completions


def _stream(*chunks):
    return iter([_Chunk(c) for c in chunks])


class TestChatRetry:
    def test_success_first_try(self):
        client = _FakeClient([_stream('hello', ' world')])
        llm = LLMClient(client, max_retries=2)
        assert llm.chat('m', 's', 'u') == 'hello world'
        assert client.completions.calls == 1

    def test_retry_then_success(self):
        def fail():
            raise RuntimeError('boom')

        client = _FakeClient([fail, _stream('ok')])
        llm = LLMClient(client, max_retries=2)
        assert llm.chat('m', 's', 'u') == 'ok'
        assert client.completions.calls == 2

    def test_exhausts_retries(self):
        def fail():
            raise RuntimeError('boom')

        client = _FakeClient([fail, fail, fail])
        llm = LLMClient(client, max_retries=1)
        with pytest.raises(ValueError, match='after 2 attempts'):
            llm.chat('m', 's', 'u')

    def test_empty_response_raises(self):
        client = _FakeClient([_stream()])
        llm = LLMClient(client, max_retries=0)
        with pytest.raises(ValueError, match='Empty response'):
            llm.chat('m', 's', 'u')
