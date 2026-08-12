"""End-to-end long-term career planning API tests (isolated temp data).

Covers LLM and fallback generation paths, auth, validation, persistence,
latest-plan lookup and history management.
"""

PROFILE = {
    'education': '本科',
    'major': '计算机科学与技术',
    'skills': 'Python, 机器学习',
    'experience': '2年',
    'career_goals': 'AI 工程师',
}


def _login_user(app_client):
    app_client.post('/login', json={'phone': '13900000000', 'password': 'user123'})


def _save_profile(app_client):
    """Persist the profile into the session (as analyze_profile does)."""
    r = app_client.post('/analyze_profile', data=PROFILE)
    assert r.status_code == 200


def _generate(app_client, analysis=''):
    return app_client.post('/career_plan/generate', data={'career_analysis': analysis})


class TestPlanAuth:
    def test_generate_requires_auth(self, app_client):
        assert app_client.post('/career_plan/generate', data={}).status_code == 401

    def test_latest_requires_auth(self, app_client):
        assert app_client.get('/career_plan/latest').status_code == 401

    def test_history_requires_auth(self, app_client):
        assert app_client.get('/api/plans').status_code == 401
        assert app_client.delete('/api/plans/x').status_code == 401


class TestPlanGenerate:
    def test_generate_llm(self, app_client, llm_success):
        _login_user(app_client)
        _save_profile(app_client)
        r = _generate(app_client)
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        plan = data['plan']
        assert plan['source'] == 'llm'
        assert plan['horizon_years'] == 5
        assert len(plan['phases']) == 3
        for p in plan['phases']:
            assert p['period'] and p['theme']
            assert p['goals'] and p['actions']
            assert p['milestones'] and p['kpis']
        assert plan['risks']

    def test_generate_fallback(self, app_client, llm_failure):
        _login_user(app_client)
        _save_profile(app_client)
        r = _generate(app_client)
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        plan = data['plan']
        assert plan['source'] == 'local'
        assert len(plan['phases']) == 3
        assert plan['summary']
        assert plan['risks']

    def test_generate_without_profile_rejected(self, user_client):
        r = _generate(user_client)
        assert r.status_code == 400

    def test_generate_with_analysis_text(self, app_client, llm_success):
        _login_user(app_client)
        _save_profile(app_client)
        r = _generate(app_client, analysis='推荐人工智能方向：算法工程师')
        assert r.status_code == 200
        assert r.get_json()['success'] is True

    def test_generate_saves_and_latest(self, app_client, llm_success):
        _login_user(app_client)
        _save_profile(app_client)
        pid = _generate(app_client).get_json()['plan_id']
        r = app_client.get('/career_plan/latest')
        assert r.status_code == 200
        latest = r.get_json()['plan']
        assert latest is not None
        assert latest['id'] == pid
        assert latest['plan']['source'] == 'llm'

    def test_latest_empty(self, user_client):
        r = user_client.get('/career_plan/latest')
        data = r.get_json()
        assert data['success'] is True
        assert data['plan'] is None


class TestPlanHistory:
    def test_list_and_delete(self, app_client, llm_success):
        _login_user(app_client)
        _save_profile(app_client)
        pid = _generate(app_client).get_json()['plan_id']
        items = app_client.get('/api/plans').get_json()['items']
        assert len(items) == 1
        assert items[0]['id'] == pid
        assert app_client.delete(f'/api/plans/{pid}').status_code == 200
        assert app_client.get('/api/plans').get_json()['items'] == []

    def test_history_capped(self, app_client, llm_failure):
        import app as appmod
        original = appmod.HISTORY_LIMIT
        appmod.HISTORY_LIMIT = 2
        try:
            _login_user(app_client)
            _save_profile(app_client)
            for _ in range(4):
                _generate(app_client)
            items = app_client.get('/api/plans').get_json()['items']
            assert len(items) == 2
        finally:
            appmod.HISTORY_LIMIT = original

    def test_history_user_isolation(self, app_client, llm_success):
        _login_user(app_client)
        _save_profile(app_client)
        _generate(app_client)
        app_client.get('/logout')
        app_client.post('/login', json={'phone': '13800000000', 'password': 'admin123'})
        assert app_client.get('/api/plans').get_json()['items'] == []


class TestPlanFallbackEngine:
    def test_unknown_profile_gets_generic_plan(self):
        from career_plan import FallbackCareerPlanner
        planner = FallbackCareerPlanner()
        plan = planner.generate_plan({'major': '哲学', 'skills': '', 'career_goals': ''})
        assert len(plan['phases']) == 3
        assert plan['summary']
        assert plan['risks']

    def test_domain_profile_gets_matched_plan(self):
        from career_plan import FallbackCareerPlanner
        planner = FallbackCareerPlanner()
        plan = planner.generate_plan(PROFILE)
        joined = ' '.join(' '.join(p['goals']) for p in plan['phases']) + plan['summary']
        assert '人工智能' in joined
