"""End-to-end AI mock interview API tests (isolated temp data, mocked LLM).

Covers both LLM and deterministic-fallback paths, auth, validation,
persistence and history management.
"""

PROFILE = {
    'education': '本科',
    'major': '计算机科学与技术',
    'skills': 'Python, 机器学习',
    'experience': '2年',
    'career_goals': 'AI 工程师',
}

ANSWER_TEXT = ('我对这个问题有一些自己的思考。结合我过去的项目经验，我在项目中主要负责'
               '核心模块的设计与实现，遇到困难时我会先拆解问题再逐步解决。')


def _login_user(app_client):
    app_client.post('/login', json={'phone': '13900000000', 'password': 'user123'})


def _start(app_client, **kw):
    data = {'target_position': 'AI 算法工程师'}
    data.update(kw)
    return app_client.post('/mock_interview/start', data=data)


def _answer(app_client, session_id, qid, answer):
    return app_client.post('/mock_interview/answer', data={
        'session_id': session_id, 'question_index': qid, 'answer': answer})


class TestInterviewAuth:
    def test_start_requires_auth(self, app_client):
        assert app_client.post('/mock_interview/start', data={}).status_code == 401

    def test_answer_requires_auth(self, app_client):
        assert app_client.post('/mock_interview/answer', data={}).status_code == 401

    def test_session_requires_auth(self, app_client):
        assert app_client.get('/mock_interview/session').status_code == 401

    def test_history_requires_auth(self, app_client):
        assert app_client.get('/api/interviews').status_code == 401
        assert app_client.delete('/api/interviews/x').status_code == 401


class TestInterviewStart:
    def test_start_llm(self, app_client, llm_success):
        _login_user(app_client)
        r = _start(app_client)
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        assert data['source'] == 'llm'
        assert len(data['questions']) == 5
        assert data['questions'][0]['question']
        assert data['questions'][0]['focus']

    def test_start_fallback(self, app_client, llm_failure):
        _login_user(app_client)
        r = _start(app_client)
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        assert data['source'] == 'local'
        assert len(data['questions']) == 5
        assert all(q.get('question') for q in data['questions'])

    def test_start_missing_target(self, user_client):
        r = user_client.post('/mock_interview/start', data={'num_questions': '5'})
        assert r.status_code == 400

    def test_start_custom_count(self, app_client, llm_success):
        _login_user(app_client)
        data = _start(app_client, num_questions='3').get_json()
        assert len(data['questions']) == 3

    def test_start_clamps_count_high(self, app_client, llm_failure):
        _login_user(app_client)
        data = _start(app_client, num_questions='99').get_json()
        assert len(data['questions']) == 8

    def test_start_clamps_count_low(self, app_client, llm_failure):
        _login_user(app_client)
        data = _start(app_client, num_questions='1').get_json()
        assert len(data['questions']) == 3

    def test_start_saves_session(self, app_client, llm_success):
        _login_user(app_client)
        sid = _start(app_client).get_json()['session_id']
        r = app_client.get(f'/mock_interview/session?session_id={sid}')
        assert r.status_code == 200
        s = r.get_json()['session']
        assert s['status'] == 'in_progress'
        assert s['target_position'] == 'AI 算法工程师'
        assert s['answers'] == []


class TestInterviewAnswer:
    def test_answer_llm(self, app_client, llm_success):
        _login_user(app_client)
        sid = _start(app_client).get_json()['session_id']
        r = _answer(app_client, sid, 1, ANSWER_TEXT)
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        assert data['source'] == 'llm'
        assert data['evaluation']['score'] == 88
        assert data['evaluation']['feedback']
        assert data['answered'] == 1
        assert data['completed'] is False

    def test_answer_fallback(self, app_client, llm_failure):
        _login_user(app_client)
        sid = _start(app_client).get_json()['session_id']
        r = _answer(app_client, sid, 1, ANSWER_TEXT)
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        ev = data['evaluation']
        assert ev['source'] == 'local'
        assert 0 <= ev['score'] <= 100
        assert ev['feedback']

    def test_answer_empty_rejected(self, app_client, llm_success):
        _login_user(app_client)
        sid = _start(app_client).get_json()['session_id']
        assert _answer(app_client, sid, 1, '').status_code == 400
        assert _answer(app_client, sid, 1, '   ').status_code == 400

    def test_answer_unknown_session(self, user_client):
        r = _answer(user_client, 'i-not-exist', 1, '回答')
        assert r.status_code == 404

    def test_answer_bad_index(self, app_client, llm_success):
        _login_user(app_client)
        sid = _start(app_client).get_json()['session_id']
        assert _answer(app_client, sid, 999, '回答').status_code == 400
        assert _answer(app_client, sid, 'x', '回答').status_code == 400

    def test_complete_interview_summary(self, app_client, llm_success):
        _login_user(app_client)
        sid = _start(app_client).get_json()['session_id']
        summary = None
        for qid in range(1, 6):
            r = _answer(app_client, sid, qid, ANSWER_TEXT)
            data = r.get_json()
            assert data['success'] is True
            if data['completed']:
                summary = data['summary']
        assert summary is not None
        assert 0 <= summary['avg_score'] <= 100
        assert summary['verdict']
        assert summary['strengths']
        # persisted as completed with all 5 answers
        s = app_client.get(f'/mock_interview/session?session_id={sid}').get_json()['session']
        assert s['status'] == 'completed'
        assert len(s['answers']) == 5
        assert s['summary'] == summary

    def test_answer_after_completed_rejected(self, app_client, llm_success):
        _login_user(app_client)
        sid = _start(app_client).get_json()['session_id']
        for qid in range(1, 6):
            _answer(app_client, sid, qid, ANSWER_TEXT)
        assert _answer(app_client, sid, 1, '再回答一次').status_code == 400

    def test_build_summary_helpers(self):
        from mock_interview import MockInterviewEngine
        s = MockInterviewEngine.build_summary([])
        assert s['avg_score'] == 0
        s2 = MockInterviewEngine.build_summary([
            {'score': 90, 'strengths': ['a'], 'weaknesses': []},
            {'score': 70, 'strengths': ['a'], 'weaknesses': ['b']},
        ])
        assert s2['avg_score'] == 80
        assert s2['strengths'] == ['a']  # deduped


class TestInterviewHistory:
    def test_history_list_and_delete(self, app_client, llm_success):
        _login_user(app_client)
        sid = _start(app_client).get_json()['session_id']
        items = app_client.get('/api/interviews').get_json()['items']
        assert len(items) == 1
        assert items[0]['id'] == sid
        assert app_client.delete(f'/api/interviews/{sid}').status_code == 200
        assert app_client.get('/api/interviews').get_json()['items'] == []

    def test_history_capped(self, app_client, llm_failure):
        import app as appmod
        original = appmod.HISTORY_LIMIT
        appmod.HISTORY_LIMIT = 3
        try:
            _login_user(app_client)
            for _ in range(5):
                _start(app_client, target_position='职位')
            items = app_client.get('/api/interviews').get_json()['items']
            assert len(items) == 3
        finally:
            appmod.HISTORY_LIMIT = original

    def test_history_user_isolation(self, app_client, llm_success):
        _login_user(app_client)
        _start(app_client)
        # admin cannot see the user's interviews
        app_client.get('/logout')
        app_client.post('/login', json={'phone': '13800000000', 'password': 'admin123'})
        assert app_client.get('/api/interviews').get_json()['items'] == []
