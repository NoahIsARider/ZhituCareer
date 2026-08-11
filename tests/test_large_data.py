"""Large-scale data tests: thousands of jobs / courses must stay fast and correct.

Verifies the "retrieve then re-rank" behavior: the LLM only ever sees a small
bounded candidate set, and the rule-based fallback returns good results quickly
even with 5,000+ records.
"""

import json
import time

import pytest

from data_store import JsonStore
from job_matching import RETRIEVE_TOP_K, JobMatcher
from course_matching import CourseMatcher


def _gen_jobs(n):
    jobs = []
    for i in range(n):
        if i == 1234:
            jobs.append({'id': i, 'title': '机器学习算法工程师', 'company': '智能科技',
                         'location': '杭州市', 'salary': '40k-70k',
                         'description': 'Python 深度学习 推荐系统 大模型',
                         'requirements': ['Python', 'TensorFlow', 'PyTorch']})
        else:
            jobs.append({'id': i, 'title': f'普通岗位 {i}', 'company': f'公司{i}',
                         'location': '上海市', 'salary': '10k-20k',
                         'description': '业务开发与维护', 'requirements': ['Java']})
    return jobs


def _gen_courses(n):
    courses = []
    for i in range(n):
        if i == 777:
            courses.append({'id': i, 'title': '机器学习与深度学习实战', 'provider': 'DataCamp',
                            'level': 'Advanced', 'duration': '12 weeks', 'price': '$899',
                            'description': 'machine learning and deep learning',
                            'skills': ['Python', 'TensorFlow'], 'career_paths': ['ML Engineer']})
        else:
            courses.append({'id': i, 'title': f'基础课程 {i}', 'provider': 'School',
                            'level': 'Beginner', 'description': '通识课程',
                            'skills': ['Office'], 'career_paths': ['General']})
    return courses


@pytest.fixture
def big_jobs(tmp_path):
    path = tmp_path / 'jobs.json'
    JsonStore(str(path)).save({'jobs': _gen_jobs(5000)})
    return str(path)


@pytest.fixture
def big_courses(tmp_path):
    path = tmp_path / 'course.json'
    JsonStore(str(path)).save({'courses': _gen_courses(5000)})
    return str(path)


class TestLargeJobMatching:
    def test_fallback_fast_and_accurate(self, big_jobs, llm_failure):
        matcher = JobMatcher()
        matcher.jobs_path = big_jobs
        matcher._retriever = None

        user_input = {'keyword': '机器学习', 'location': '杭州', 'career_analysis': ''}
        user_data = {'skills': 'Python, TensorFlow'}

        start = time.time()
        results = matcher.job_matching(user_input, user_data)
        elapsed = time.time() - start

        assert results, 'must find matches in a 5000-job catalog'
        assert results[0]['title'] == '机器学习算法工程师'
        assert elapsed < 5.0, f'fallback matching too slow: {elapsed:.2f}s'

    def test_llm_only_sees_bounded_candidates(self, big_jobs, monkeypatch):
        matcher = JobMatcher()
        matcher.jobs_path = big_jobs
        matcher._retriever = None

        seen = {}

        def fake_match_job(agent_self, user_input, user_data, jobs):
            seen['count'] = len(jobs)
            return json.dumps([{'title': j['title'], 'company': j['company'],
                                'location': j['location'], 'salary': j.get('salary', ''),
                                'description': j['description'],
                                'requirements': j['requirements'],
                                'match_reason': 'test'} for j in jobs[:2]],
                              ensure_ascii=False)

        import agent.job_matching_agent as jma
        monkeypatch.setattr(jma.JobMatchingAgent, 'match_job', fake_match_job)

        results = matcher.job_matching(
            {'keyword': '机器学习', 'location': '杭州', 'career_analysis': ''},
            {'skills': 'Python'})

        assert 0 < seen['count'] <= RETRIEVE_TOP_K
        assert results
        assert results[0]['title'] == '机器学习算法工程师'


class TestLargeCourseMatching:
    def test_fallback_fast_and_accurate(self, big_courses, llm_failure):
        matcher = CourseMatcher()
        matcher.courses_path = big_courses
        matcher._retriever = None

        start = time.time()
        results = matcher.course_matching(
            {'keyword': '机器学习'}, '机器学习工程师方向，需掌握 Python、深度学习')
        elapsed = time.time() - start

        assert results, 'must find matches in a 5000-course catalog'
        assert results[0]['title'] == '机器学习与深度学习实战'
        assert elapsed < 5.0, f'fallback matching too slow: {elapsed:.2f}s'

    def test_llm_only_sees_bounded_candidates(self, big_courses, monkeypatch):
        matcher = CourseMatcher()
        matcher.courses_path = big_courses
        matcher._retriever = None

        seen = {}

        def fake_match_courses(agent_self, user_input, career_analysis, courses):
            seen['count'] = len(courses)
            return json.dumps([{'id': c['id'], 'title': c['title'],
                                'provider': c.get('provider', ''),
                                'level': c.get('level', ''),
                                'description': c['description'],
                                'skills': c['skills'], 'career_paths': c['career_paths'],
                                'match_reason': 'test'} for c in courses[:2]],
                              ensure_ascii=False)

        import agent.course_matching_agent as cma
        monkeypatch.setattr(cma.CourseMatchingAgent, 'match_courses', fake_match_courses)

        results = matcher.course_matching(
            {'keyword': '机器学习'}, '机器学习工程师方向')

        assert 0 < seen['count'] <= RETRIEVE_TOP_K
        assert results
        assert results[0]['title'] == '机器学习与深度学习实战'


class TestRetrievalIndexScale:
    def test_index_time_for_5000_jobs(self, big_jobs):
        from retrieval import HybridRetriever
        jobs = JsonStore(big_jobs).load()['jobs']
        start = time.time()
        r = HybridRetriever(
            text_fields=['title', 'company', 'description', 'requirements', 'location'],
            filter_fields=['location'], boost_fields=['title', 'company'])
        r.index(jobs)
        elapsed = time.time() - start
        assert elapsed < 10.0, f'index too slow: {elapsed:.2f}s'

        start = time.time()
        hits = r.search('机器学习 python 深度学习', top_k=10,
                        filters=[('location', '杭州')])
        query_time = time.time() - start
        assert hits and hits[0][0] == 1234
        assert query_time < 2.0, f'query too slow: {query_time:.2f}s'
