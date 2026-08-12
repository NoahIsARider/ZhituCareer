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

CANNED_INTERVIEW_QUESTIONS = {
    'questions': [
        {'id': 1, 'question': '请做一下自我介绍，并说明求职动机。',
         'focus': '自我介绍与动机', 'expected_points': ['结构清晰', '表达动机']},
        {'id': 2, 'question': '介绍一个你最有成就感的项目。',
         'focus': '项目经验', 'expected_points': ['个人贡献', '复盘思考']},
        {'id': 3, 'question': '与同事意见不一致时你会怎么办？',
         'focus': '团队协作', 'expected_points': ['沟通方式', '尊重他人']},
        {'id': 4, 'question': '交付期临近但工作量超出预期，如何应对？',
         'focus': '抗压能力', 'expected_points': ['优先级管理', '主动沟通']},
        {'id': 5, 'question': '未来三到五年的职业目标是什么？',
         'focus': '职业规划', 'expected_points': ['目标明确', '路径可行']},
    ]
}

CANNED_INTERVIEW_EVAL = {
    'score': 88,
    'feedback': '回答清晰，逻辑完整，展现了良好的专业素养。',
    'suggestion': '建议用 STAR 法则补充更多数据细节。',
    'strengths': ['逻辑清晰', '表达流畅'],
    'weaknesses': ['量化不足'],
}

CANNED_PLAN = {
    'horizon_years': 5,
    'summary': '按筑基、深耕、跃迁三阶段推进，5 年实现从入门到独当一面。',
    'phases': [
        {'period': '0-1年', 'theme': '筑基：补齐核心能力',
         'goals': ['掌握核心知识'], 'actions': ['制定学习计划'],
         'milestones': ['完成项目'], 'kpis': ['周学 10 小时']},
        {'period': '1-3年', 'theme': '深耕：成为团队骨干',
         'goals': ['独立承担模块'], 'actions': ['参与核心项目'],
         'milestones': ['主导项目'], 'kpis': ['绩效前 30%']},
        {'period': '3-5年', 'theme': '跃迁：专家或管理',
         'goals': ['成为专家'], 'actions': ['承担选型决策'],
         'milestones': ['高级职级'], 'kpis': ['输出方法论']},
    ],
    'risks': [{'risk': '技术迭代快', 'mitigation': '持续学习'}],
}


def _fake_chat_once_success(self, model, system, user):
    """Deterministic canned responses selected by the system prompt."""
    if '生成面试题目' in system:
        return __import__('json').dumps(CANNED_INTERVIEW_QUESTIONS, ensure_ascii=False)
    if '评估求职者的面试回答' in system:
        return __import__('json').dumps(CANNED_INTERVIEW_EVAL, ensure_ascii=False)
    if '长期职业规划顾问' in system:
        return __import__('json').dumps(CANNED_PLAN, ensure_ascii=False)
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
    appmod._interviews_store = JsonStore(str(data_dir / 'interviews.json'))
    appmod._plans_store = JsonStore(str(data_dir / 'plans.json'))
    appmod.job_matcher.jobs_path = str(jobs_path)
    appmod.course_matcher.courses_path = str(courses_path)
    appmod.job_matcher._retriever = None
    appmod.job_matcher._retriever_mtime = None
    appmod.course_matcher._retriever = None
    appmod.course_matcher._retriever_mtime = None
    appmod.career_analyzer._cache.clear()
    appmod.career_planner._cache.clear()
    appmod.mock_interview_engine._cache.clear()
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
