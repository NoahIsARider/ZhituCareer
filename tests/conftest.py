"""Shared pytest fixtures.

Every test that touches the Flask app runs against an isolated temporary
data directory so the repository's sample data is never modified. The LLM
client is either mocked (deterministic JSON responses) or forced to fail
(so the rule-based fallback path is exercised).
"""

import os
import shutil

import pytest
from werkzeug.security import generate_password_hash

# Force LLM to fail fast (no retry sleeps) before `app` is imported.
os.environ['LLM_MAX_RETRIES'] = '0'
os.environ['LLM_RETRY_BASE_DELAY'] = '0'
os.environ.setdefault('OPENAI_API_KEY', '')

import agent.llm_client as llm_mod  # noqa: E402
from data_store import JsonStore  # noqa: E402

REPO_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

CANNED_CAREER = {
    'career_path': '推荐人工智能方向：算法工程师',
    'job_advice': '多参与项目实践，构建作品集。',
    'skills_to_improve': '深度学习、模型部署。',
    'recommended_positions': ['AI 算法工程师', '机器学习工程师'],
}

CANNED_JOBS = [
    {'title': '推荐算法工程师', 'company': '音浪社交', 'location': '北京市朝阳区',
     'salary': '35k-60k', 'description': '短视频推荐算法', 'requirements': ['TensorFlow'],
     'match_reason': '技能匹配度高'},
]

CANNED_COURSES = [
    {'id': 'c1', 'title': 'Data Science Bootcamp', 'provider': 'DataCamp',
     'level': 'Advanced', 'duration': '12 weeks', 'price': '$899',
     'description': 'machine learning training', 'skills': ['Python'],
     'career_paths': ['Data Scientist'], 'match_reason': '契合职业方向'},
]


def _fake_chat_once_success(self, model, system, user):
    """Deterministic canned responses selected by the system prompt."""
    if '职业规划顾问' in system:
        return __import__('json').dumps(CANNED_CAREER, ensure_ascii=False)
    if '求职推荐助手' in system:
        return __import__('json').dumps(CANNED_JOBS, ensure_ascii=False)
    if 'course recommendation' in system.lower():
        return __import__('json').dumps(CANNED_COURSES, ensure_ascii=False)
    if '市场分析师' in system:
        return '互联网与人工智能领域人才需求旺盛。'
    raise ValueError('unexpected system prompt: ' + system[:40])


def _fake_chat_once_failure(self, model, system, user):
    raise ValueError('mocked LLM failure')


@pytest.fixture
def llm_success(monkeypatch):
    monkeypatch.setattr(llm_mod.LLMClient, '_chat_once', _fake_chat_once_success)


@pytest.fixture
def llm_failure(monkeypatch):
    monkeypatch.setattr(llm_mod.LLMClient, '_chat_once', _fake_chat_once_failure)


@pytest.fixture
def app_client(tmp_path, monkeypatch):
    """Flask test client isolated from the repository data files."""
    import app as appmod

    appmod.app.config['TESTING'] = True
    appmod.app.config['WTF_CSRF_ENABLED'] = False

    data_dir = tmp_path / 'data'
    data_dir.mkdir()

    users_path = data_dir / 'users.json'
    JsonStore(str(users_path)).save({
        'users': [
            {'phone': '13800000000',
             'password': generate_password_hash('admin123'),
             'role': 'admin', 'name': 'Admin'},
            {'phone': '13900000000',
             'password': generate_password_hash('user123'),
             'role': 'user', 'name': 'User'},
        ]
    })

    courses_path = data_dir / 'course.json'
    jobs_path = data_dir / 'jobs.json'
    shutil.copy(os.path.join(REPO_DATA, 'course.json'), str(courses_path))
    shutil.copy(os.path.join(REPO_DATA, 'jobs.json'), str(jobs_path))

    appmod._users_store = JsonStore(str(users_path))
    appmod._course_store = JsonStore(str(courses_path))
    appmod._jobs_store = JsonStore(str(jobs_path))
    appmod._analyses_store = JsonStore(str(data_dir / 'analyses.json'))
    appmod.job_matcher.jobs_path = str(jobs_path)
    appmod.course_matcher.courses_path = str(courses_path)
    appmod.job_matcher._retriever = None
    appmod.job_matcher._retriever_mtime = None
    appmod.course_matcher._retriever = None
    appmod.course_matcher._retriever_mtime = None
    appmod.career_analyzer._cache.clear()
    # Fresh rate limiters so the rate-limit tests don't leak into others.
    appmod.login_limiter = appmod.RateLimiter(limit=10, window=300)
    appmod.register_limiter = appmod.RateLimiter(limit=5, window=3600)

    with appmod.app.app_context():
        yield appmod.app.test_client()


@pytest.fixture
def admin_client(app_client):
    app_client.post('/login', json={
        'phone': '13800000000', 'password': 'admin123'})
    return app_client


@pytest.fixture
def user_client(app_client):
    app_client.post('/login', json={
        'phone': '13900000000', 'password': 'user123'})
    return app_client
