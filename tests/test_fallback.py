"""Tests for the deterministic rule-based fallback matchers."""

import json
import os

import pytest

from fallback_matcher import (FallbackCareerAnalyzer, FallbackCourseMatcher,
                              FallbackJobMatcher)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

PROFILE = {
    'education': '本科',
    'major': '计算机科学与技术',
    'skills': 'Python, 机器学习, TensorFlow, 数据分析',
    'experience': '2年算法实习',
    'career_goals': '成为一名资深 AI 工程师',
}


@pytest.fixture
def jobs():
    with open(os.path.join(DATA_DIR, 'jobs.json'), encoding='utf-8') as f:
        return json.load(f)['jobs']


@pytest.fixture
def courses():
    with open(os.path.join(DATA_DIR, 'course.json'), encoding='utf-8') as f:
        return json.load(f)['courses']


class TestCareerFallback:
    def test_detects_ai_domain(self):
        result = FallbackCareerAnalyzer().analyze_career(PROFILE)
        assert '人工智能' in result['career_path']
        assert isinstance(result['recommended_positions'], list)
        assert len(result['recommended_positions']) > 0

    def test_unknown_profile_returns_default(self):
        result = FallbackCareerAnalyzer().analyze_career(
            {'major': 'xzy', 'skills': '', 'career_goals': '', 'experience': ''})
        assert result['career_path']
        assert result['job_advice']
        assert result['skills_to_improve']

    def test_result_shape(self):
        result = FallbackCareerAnalyzer().analyze_career(PROFILE)
        for key in ('career_path', 'job_advice', 'skills_to_improve', 'recommended_positions'):
            assert key in result

    def test_all_missing_fields_no_crash(self):
        result = FallbackCareerAnalyzer().analyze_career({})
        assert result['career_path']


class TestJobFallback:
    def test_keyword_and_location(self, jobs):
        out = FallbackJobMatcher().match_jobs(
            {'keyword': 'AI', 'location': '北京', 'career_analysis': ''},
            {'skills': ''}, jobs, top_k=3)
        assert out, 'expected at least one match'
        assert all(j.get('match_reason') for j in out)
        assert all(j.get('title') for j in out)

    def test_skill_overlap_ranks_higher(self):
        docs = [
            {'title': '无关职位', 'company': 'A', 'location': '杭州', 'description': '机械',
             'requirements': ['焊接']},
            {'title': 'Python 后端', 'company': 'B', 'location': '杭州', 'description': 'web',
             'requirements': ['Python', '机器学习']},
        ]
        out = FallbackJobMatcher().match_jobs(
            {'keyword': '', 'location': '', 'career_analysis': ''},
            {'skills': 'Python, 机器学习'}, docs, top_k=2)
        assert out[0]['title'] == 'Python 后端'

    def test_empty_input_returns_empty(self):
        assert FallbackJobMatcher().match_jobs(
            {'keyword': '', 'location': '', 'career_analysis': ''},
            {'skills': ''}, [{'title': 'x', 'company': 'c'}], top_k=3) == []

    def test_deterministic(self, jobs):
        a = FallbackJobMatcher().match_jobs(
            {'keyword': '工程师', 'location': '', 'career_analysis': ''},
            {'skills': 'Java'}, jobs, top_k=3)
        b = FallbackJobMatcher().match_jobs(
            {'keyword': '工程师', 'location': '', 'career_analysis': ''},
            {'skills': 'Java'}, jobs, top_k=3)
        assert a == b


class TestCourseFallback:
    def test_chinese_keyword_matches_english_catalog(self, courses):
        out = FallbackCourseMatcher().match_courses(
            {'keyword': '机器学习'}, '', courses, top_k=3)
        assert out, 'cross-language matching should find courses'

    def test_career_analysis_boost(self, courses):
        out = FallbackCourseMatcher().match_courses(
            {'keyword': ''}, '机器学习工程师方向，需掌握 Python、深度学习', courses, top_k=3)
        assert out
        assert all(c.get('match_reason') for c in out)

    def test_empty_results(self):
        assert FallbackCourseMatcher().match_courses(
            {'keyword': ''}, '', [{'title': 'x'}], top_k=3) == []

    def test_deterministic(self, courses):
        kw = {'keyword': '数据'}
        a = FallbackCourseMatcher().match_courses(kw, '', courses, top_k=3)
        b = FallbackCourseMatcher().match_courses(kw, '', courses, top_k=3)
        assert a == b
