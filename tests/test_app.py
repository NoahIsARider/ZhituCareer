"""End-to-end Flask API tests (isolated temp data, mocked / failing LLM)."""

PROFILE_FORM = {
    'education': '本科',
    'major': '计算机科学与技术',
    'skills': 'Python, 机器学习',
    'experience': '2年',
    'career_goals': 'AI 工程师',
}


class TestHealthAndAuth:
    def test_health(self, app_client):
        r = app_client.get('/health')
        assert r.status_code == 200
        assert r.get_json()['status'] == 'ok'

    def test_root_redirects_to_login(self, app_client):
        r = app_client.get('/')
        assert r.status_code == 302

    def test_api_requires_auth(self, app_client):
        assert app_client.get('/api/me').status_code == 401
        assert app_client.post('/search_jobs', data={}).status_code == 401
        assert app_client.post('/search_course', data={}).status_code == 401
        assert app_client.post('/analyze_profile', data={}).status_code == 401

    def test_admin_api_requires_admin(self, app_client):
        assert app_client.get('/api/courses').status_code == 401

    def test_login_success_admin(self, app_client):
        r = app_client.post('/login', json={'phone': '13800000000', 'password': 'admin123'})
        assert r.status_code == 200
        assert r.get_json()['redirect'] == '/admin'

    def test_login_success_user(self, app_client):
        r = app_client.post('/login', json={'phone': '13900000000', 'password': 'user123'})
        assert r.status_code == 200
        assert r.get_json()['redirect'] == '/'

    def test_login_wrong_password(self, app_client):
        r = app_client.post('/login', json={'phone': '13800000000', 'password': 'nope'})
        assert r.status_code == 401

    def test_login_unknown_user(self, app_client):
        r = app_client.post('/login', json={'phone': '13811112222', 'password': 'x'})
        assert r.status_code == 401

    def test_login_rate_limit(self, app_client):
        for i in range(10):
            app_client.post('/login', json={'phone': '13800000000', 'password': 'bad'})
        r = app_client.post('/login', json={'phone': '13800000000', 'password': 'bad'})
        assert r.status_code == 429

    def test_logout(self, app_client):
        app_client.post('/login', json={'phone': '13800000000', 'password': 'admin123'})
        assert app_client.get('/api/me').status_code == 200
        app_client.get('/logout')
        assert app_client.get('/api/me').status_code == 401

    def test_admin_page_redirects_non_admin(self, user_client):
        r = user_client.get('/admin')
        assert r.status_code == 302
        assert '/api/' not in r.headers.get('Location', '')


class TestRegister:
    def test_register_success(self, app_client):
        r = app_client.post('/register', json={
            'phone': '13612345678', 'password': 'pass123', 'name': '新用户'})
        assert r.status_code == 200
        assert r.get_json()['success'] is True
        # auto-logged-in and can access user APIs
        assert app_client.get('/api/me').status_code == 200

    def test_register_invalid_phone(self, app_client):
        r = app_client.post('/register', json={
            'phone': '123', 'password': 'pass123', 'name': 'x'})
        assert r.status_code == 400

    def test_register_short_password(self, app_client):
        r = app_client.post('/register', json={
            'phone': '13612345678', 'password': '123', 'name': 'x'})
        assert r.status_code == 400

    def test_register_missing_name(self, app_client):
        r = app_client.post('/register', json={
            'phone': '13612345678', 'password': 'pass123', 'name': ''})
        assert r.status_code == 400

    def test_register_duplicate_phone(self, app_client):
        r = app_client.post('/register', json={
            'phone': '13900000000', 'password': 'pass123', 'name': 'x'})
        assert r.status_code == 409

    def test_register_rate_limit(self, app_client):
        for i in range(5):
            app_client.post('/register', json={
                'phone': f'1360000000{i}', 'password': 'pass123', 'name': 'x'})
        r = app_client.post('/register', json={
            'phone': '13600000009', 'password': 'pass123', 'name': 'x'})
        assert r.status_code == 429


class TestAdminCourses:
    def test_list_paginated(self, admin_client):
        r = admin_client.get('/api/courses?page=1&page_size=10')
        data = r.get_json()
        assert r.status_code == 200
        assert len(data['items']) <= 10
        assert data['total'] >= 30
        assert data['page'] == 1

    def test_search(self, admin_client):
        data = admin_client.get('/api/courses?search=python').get_json()
        assert data['total'] >= 1
        # every returned item matches
        for item in data['items']:
            haystack = ' '.join(str(item.get(k, '')) for k in
                                ('title', 'provider', 'level', 'description', 'skills'))
            assert 'python' in haystack.lower()

    def test_search_no_match(self, admin_client):
        data = admin_client.get('/api/courses?search=zzzzz_not_exists').get_json()
        assert data['total'] == 0
        assert data['items'] == []

    def test_invalid_page_defaults(self, admin_client):
        data = admin_client.get('/api/courses?page=abc&page_size=xyz').get_json()
        assert data['page'] == 1

    def test_add_item(self, admin_client):
        r = admin_client.post('/api/courses/item', json={
            'course': {'title': '新增课程', 'description': '描述', 'skills': ['Python']}})
        assert r.status_code == 200
        cid = r.get_json()['id']
        # verify persisted via search
        found = admin_client.get('/api/courses?search=新增课程').get_json()
        assert found['total'] == 1
        assert found['items'][0]['id'] == cid

    def test_update_item(self, admin_client):
        r = admin_client.post('/api/courses/item', json={
            'course': {'title': '旧标题', 'description': 'd'}})
        cid = r.get_json()['id']
        r2 = admin_client.post('/api/courses/item', json={
            'course': {'id': cid, 'title': '新标题', 'description': 'd2'}})
        assert r2.status_code == 200
        found = admin_client.get('/api/courses?search=新标题').get_json()
        assert found['total'] == 1
        assert admin_client.get('/api/courses?search=旧标题').get_json()['total'] == 0

    def test_delete_item(self, admin_client):
        r = admin_client.post('/api/courses/item', json={
            'course': {'title': '待删除', 'description': 'd'}})
        cid = r.get_json()['id']
        assert admin_client.delete(f'/api/courses/item?id={cid}').status_code == 200
        assert admin_client.get('/api/courses?search=待删除').get_json()['total'] == 0

    def test_delete_missing_returns_404(self, admin_client):
        assert admin_client.delete('/api/courses/item?id=nothere').status_code == 404

    def test_delete_missing_id(self, admin_client):
        assert admin_client.delete('/api/courses/item').status_code == 400

    def test_post_invalid_payload(self, admin_client):
        assert admin_client.post('/api/courses', json={'nope': []}).status_code == 400
        assert admin_client.post('/api/courses', json={'courses': 'nope'}).status_code == 400

    def test_post_invalid_record(self, admin_client):
        r = admin_client.post('/api/courses', json={'courses': [{'title': ''}]})
        assert r.status_code == 400

    def test_post_valid_normalizes(self, admin_client):
        r = admin_client.post('/api/courses', json={
            'courses': [{'title': '合法课程', 'description': '描述', 'hack': 'drop',
                         'skills': ['Python']}]})
        assert r.status_code == 200
        data = admin_client.get('/api/courses?search=合法课程&page_size=50').get_json()
        assert data['total'] == 1
        item = data['items'][0]
        assert item['title'] == '合法课程'
        assert 'hack' not in item  # unknown fields are stripped

    def test_whole_replace(self, admin_client):
        admin_client.post('/api/courses', json={'courses': [
            {'title': 'A', 'description': 'd'}, {'title': 'B', 'description': 'd'}]})
        data = admin_client.get('/api/courses').get_json()
        assert data['total'] == 2


class TestAdminJobs:
    def test_list(self, admin_client):
        data = admin_client.get('/api/jobs?page=1&page_size=10').get_json()
        assert data['total'] >= 30
        assert len(data['items']) == 10

    def test_add_update_delete(self, admin_client):
        r = admin_client.post('/api/jobs/item', json={
            'job': {'title': '测试职位', 'company': '测试公司', 'location': '杭州',
                    'salary': '10k-20k', 'description': 'desc',
                    'requirements': ['Python']}})
        cid = r.get_json()['id']
        assert admin_client.get('/api/jobs?search=测试职位').get_json()['total'] == 1
        assert admin_client.post('/api/jobs/item', json={
            'job': {'id': cid, 'title': '测试职位2', 'company': '测试公司'}}).status_code == 200
        assert admin_client.delete(f'/api/jobs/item?id={cid}').status_code == 200

    def test_non_admin_forbidden(self, user_client):
        assert user_client.get('/api/jobs').status_code == 401
        assert user_client.post('/api/jobs/item', json={'job': {}}).status_code == 401


class TestAnalysisAndMatching:
    def test_analyze_with_llm(self, app_client, llm_success):
        app_client.post('/login', json={'phone': '13900000000', 'password': 'user123'})
        r = app_client.post('/analyze_profile', data=PROFILE_FORM)
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        assert data['analysis']['source'] == 'llm'
        assert data['analysis']['career_path']

    def test_analyze_falls_back(self, app_client, llm_failure):
        app_client.post('/login', json={'phone': '13900000000', 'password': 'user123'})
        r = app_client.post('/analyze_profile', data=PROFILE_FORM)
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        assert data['analysis']['source'] == 'local'
        assert data['analysis']['career_path']

    def test_analyze_missing_fields(self, user_client):
        r = user_client.post('/analyze_profile', data={'education': '本科'})
        assert r.status_code == 400

    def test_search_jobs_with_llm(self, app_client, llm_success):
        app_client.post('/login', json={'phone': '13900000000', 'password': 'user123'})
        r = app_client.post('/search_jobs', data={'keyword': '算法', 'location': ''})
        assert r.status_code == 200
        jobs = r.get_json()
        assert isinstance(jobs, list) and len(jobs) >= 1
        assert jobs[0]['title']

    def test_search_jobs_fallback(self, app_client, llm_failure):
        app_client.post('/login', json={'phone': '13900000000', 'password': 'user123'})
        r = app_client.post('/search_jobs', data={'keyword': '算法', 'location': ''})
        assert r.status_code == 200
        jobs = r.get_json()
        assert isinstance(jobs, list) and len(jobs) >= 1
        assert all(j.get('match_reason') for j in jobs)

    def test_search_course_with_llm(self, app_client, llm_success):
        app_client.post('/login', json={'phone': '13900000000', 'password': 'user123'})
        r = app_client.post('/search_course', data={'keyword': '机器学习'})
        assert r.status_code == 200
        courses = r.get_json()
        assert isinstance(courses, list) and len(courses) >= 1
        assert courses[0]['title']

    def test_search_course_fallback(self, app_client, llm_failure):
        app_client.post('/login', json={'phone': '13900000000', 'password': 'user123'})
        r = app_client.post('/search_course', data={'keyword': '机器学习'})
        assert r.status_code == 200
        courses = r.get_json()
        assert isinstance(courses, list) and len(courses) >= 1
        assert all(c.get('match_reason') for c in courses)


class TestErrors:
    def test_api_404(self, admin_client):
        r = admin_client.get('/api/does-not-exist')
        assert r.status_code == 404
        assert r.get_json()['error']

    def test_page_404_redirects(self, app_client):
        r = app_client.get('/some-missing-page')
        assert r.status_code == 302

    def test_me_returns_profile(self, user_client):
        data = user_client.get('/api/me').get_json()
        assert data['success'] is True
        assert data['user']['role'] == 'user'
        assert 'password' not in data['user']

    def test_session_persists(self, app_client):
        app_client.post('/login', json={'phone': '13900000000', 'password': 'user123'})
        assert app_client.get('/api/me').status_code == 200
        r = app_client.get('/api/me')
        assert r.get_json()['user']['phone'] == '13900000000'


class TestJsonBodySafety:
    def test_invalid_json_body(self, admin_client):
        r = admin_client.post('/api/courses', data='{bad json',
                             content_type='application/json')
        # Flask treats unparseable JSON as no data -> our 400 message
        assert r.status_code == 400

    def test_form_body_on_json_endpoint(self, admin_client):
        r = admin_client.post('/api/courses', data={'courses': '[]'})
        assert r.status_code == 400


class TestStatsOverview:
    def test_stats_require_auth(self, app_client):
        assert app_client.get('/api/stats/overview').status_code == 401

    def test_stats_overview_shape(self, user_client):
        data = user_client.get('/api/stats/overview').get_json()
        assert data['jobs']['total'] > 0
        assert data['courses']['total'] > 0
        assert len(data['jobs']['salary_distribution']) == 5
        assert sum(n for _, n in data['jobs']['salary_distribution']) > 0
        assert data['jobs']['by_location']
        assert data['courses']['by_level']
        assert data['market']['industry_trends']

    def test_stats_salary_bucketing(self):
        from stats import _parse_salary_k, salary_bucket
        assert _parse_salary_k('40k-70k') == 40
        assert _parse_salary_k('15-25K·13薪') == 15
        assert _parse_salary_k('面议') is None
        assert salary_bucket(15) == '10-20k'
        assert salary_bucket(55) == '50k 以上'


class TestAnalysisHistory:
    def test_analyze_saves_history(self, user_client, llm_failure):
        user_client.post('/analyze_profile', data=PROFILE_FORM)
        items = user_client.get('/api/history').get_json()['items']
        assert len(items) == 1
        assert items[0]['analysis']['source'] == 'local'
        assert items[0]['profile']['major'] == '计算机科学与技术'

    def test_history_reversed_order(self, user_client, llm_failure):
        for _ in range(2):
            user_client.post('/analyze_profile', data=PROFILE_FORM)
        items = user_client.get('/api/history').get_json()['items']
        assert len(items) == 2
        assert items[0]['ts'] >= items[1]['ts']

    def test_history_delete(self, user_client, llm_failure):
        user_client.post('/analyze_profile', data=PROFILE_FORM)
        item_id = user_client.get('/api/history').get_json()['items'][0]['id']
        r = user_client.delete(f'/api/history/{item_id}')
        assert r.status_code == 200
        assert user_client.get('/api/history').get_json()['items'] == []

    def test_history_capped(self, user_client, llm_failure):
        import app as appmod
        original = appmod.HISTORY_LIMIT
        appmod.HISTORY_LIMIT = 3
        try:
            for _ in range(5):
                user_client.post('/analyze_profile', data=PROFILE_FORM)
            items = user_client.get('/api/history').get_json()['items']
            assert len(items) == 3
        finally:
            appmod.HISTORY_LIMIT = original

    def test_history_requires_auth(self, app_client):
        assert app_client.get('/api/history').status_code == 401
        assert app_client.delete('/api/history/x').status_code == 401
