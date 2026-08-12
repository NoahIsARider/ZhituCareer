import os
import re
import threading
import time

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

from career_model import CareerAnalyzer
from career_plan import CareerPlanner
from course_matching import CourseMatcher
from job_matching import JobMatcher
from mock_interview import MockInterviewEngine
from data_store import JsonStore
from stats import compute_overview

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
if app.config['SECRET_KEY'] == 'dev-secret-key-change-me':
    print('[warn] SECRET_KEY 未设置，正在使用开发占位密钥。生产环境请务必通过环境变量配置。')
app.config['SESSION_PERMANENT'] = False
app.config['JSON_AS_ASCII'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
COURSES_FILE = os.path.join(DATA_DIR, 'course.json')
JOBS_FILE = os.path.join(DATA_DIR, 'jobs.json')
ANALYSES_FILE = os.path.join(DATA_DIR, 'analyses.json')
INTERVIEWS_FILE = os.path.join(DATA_DIR, 'interviews.json')
PLANS_FILE = os.path.join(DATA_DIR, 'plans.json')

FORM_FIELDS = ['education', 'major', 'skills', 'experience', 'career_goals']

# User-facing endpoints that return JSON and therefore must answer 401 as JSON.
JSON_API_ENDPOINTS = {
    'analyze_profile', 'search_jobs', 'search_course',
    'start_mock_interview', 'submit_interview_answer', 'get_interview_session',
    'generate_career_plan', 'get_latest_career_plan',
}

PHONE_RE = re.compile(r'^\d{11}$')

# ---------------------------------------------------------------------------
# Shared services
# ---------------------------------------------------------------------------

career_analyzer = CareerAnalyzer()
career_planner = CareerPlanner()
job_matcher = JobMatcher()
course_matcher = CourseMatcher()
mock_interview_engine = MockInterviewEngine()

_course_store = JsonStore(COURSES_FILE)
_jobs_store = JsonStore(JOBS_FILE)
_users_store = JsonStore(USERS_FILE)
_analyses_store = JsonStore(ANALYSES_FILE)
_interviews_store = JsonStore(INTERVIEWS_FILE)
_plans_store = JsonStore(PLANS_FILE)

HISTORY_LIMIT = 20


class RateLimiter:
    """Simple sliding-window rate limiter keyed by string."""

    def __init__(self, limit=10, window=300):
        self.limit = limit
        self.window = window
        self._hits = {}
        self._lock = threading.Lock()

    def hit(self, key):
        now = time.time()
        with self._lock:
            recent = [t for t in self._hits.get(key, []) if now - t < self.window]
            if len(recent) >= self.limit:
                self._hits[key] = recent
                return False
            recent.append(now)
            self._hits[key] = recent
            return True


login_limiter = RateLimiter(limit=10, window=300)
register_limiter = RateLimiter(limit=5, window=3600)


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def load_users():
    data = _users_store.load({}) or {}
    return data.get('users', [])


def save_users(users):
    _users_store.save({'users': users})


def current_user_data():
    return session.setdefault('user_data', {})


def load_analyses():
    return _analyses_store.load({}) or {}


def save_analyses(analyses):
    _analyses_store.save(analyses)


def load_interviews():
    return _interviews_store.load({}) or {}


def save_interviews(interviews):
    _interviews_store.save(interviews)


def load_plans():
    return _plans_store.load({}) or {}


def save_plans(plans):
    _plans_store.save(plans)


def is_admin():
    return session.get('user', {}).get('role') == 'admin'


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    if is_admin():
        return redirect(url_for('admin'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    data = request.get_json(silent=True) or {}
    phone = str(data.get('phone', '')).strip()
    password = str(data.get('password', ''))

    if not login_limiter.hit(f'login:{request.remote_addr}:{phone}'):
        return jsonify({'success': False,
                        'message': '尝试次数过多，请 5 分钟后再试'}), 429

    users = load_users()
    user = next((u for u in users if str(u.get('phone', '')) == phone), None)

    if user and check_password_hash(user.get('password', ''), password):
        session.clear()
        session['user'] = {k: v for k, v in user.items() if k != 'password'}
        return jsonify({
            'success': True,
            'redirect': '/admin' if user.get('role') == 'admin' else '/'
        })

    return jsonify({
        'success': False,
        'message': '手机号码或密码错误'
    }), 401


@app.route('/register', methods=['POST'])
def register():
    if not register_limiter.hit(f'register:{request.remote_addr}'):
        return jsonify({'success': False,
                        'message': '注册过于频繁，请稍后再试'}), 429

    data = request.get_json(silent=True) or {}
    phone = str(data.get('phone', '')).strip()
    password = str(data.get('password', ''))
    name = str(data.get('name', '')).strip()

    if not PHONE_RE.match(phone):
        return jsonify({'success': False, 'message': '手机号需为 11 位数字'}), 400
    if len(password) < 6:
        return jsonify({'success': False, 'message': '密码至少需要 6 位'}), 400
    if not name:
        return jsonify({'success': False, 'message': '请填写姓名'}), 400

    users = load_users()
    if any(str(u.get('phone', '')) == phone for u in users):
        return jsonify({'success': False, 'message': '该手机号已注册'}), 409

    users.append({
        'phone': phone,
        'password': generate_password_hash(password),
        'role': 'user',
        'name': name,
    })
    save_users(users)

    session.clear()
    session['user'] = {'phone': phone, 'role': 'user', 'name': name}
    return jsonify({'success': True, 'redirect': '/'})


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin')
def admin():
    if 'user' not in session:
        return redirect(url_for('login'))
    if not is_admin():
        return redirect(url_for('index'))
    return render_template('admin.html')


# ---------------------------------------------------------------------------
# Admin data APIs
# ---------------------------------------------------------------------------

def _require_admin():
    if 'user' not in session or not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    return None


def _paginate(items, search_fields=()):
    """Filter by ?search= and slice by ?page= / ?page_size=."""
    search = request.args.get('search', '').strip().lower()
    try:
        page = max(1, int(request.args.get('page', '1')))
    except ValueError:
        page = 1
    try:
        page_size = max(1, int(request.args.get('page_size', '50')))
    except ValueError:
        page_size = 50
    page_size = min(page_size, 200)

    if search:
        searchable = {}
        for idx, item in enumerate(items):
            text = ' '.join(str(item.get(f, '')) for f in search_fields).lower()
            if search in text:
                searchable[idx] = item
        items = list(searchable.values())

    total = len(items)
    start = (page - 1) * page_size
    return {
        'items': items[start:start + page_size],
        'total': total,
        'page': page,
        'page_size': page_size,
    }


def _handle_manage_request(store, key, schema_name, search_fields):
    guard = _require_admin()
    if guard:
        return guard

    if request.method == 'GET':
        data = store.load({}) or {}
        records = data.get(key, [])
        return jsonify(_paginate(records, search_fields=search_fields))

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict) or key not in payload:
        return jsonify({'error': f'请求体必须包含 {key} 字段'}), 400
    records = payload.get(key)
    if not isinstance(records, list):
        return jsonify({'error': f'{key} 必须是数组'}), 400

    ok, err = JsonStore.validate_records(records, schema_name)
    if not ok:
        return jsonify({'error': err}), 400

    normalized = JsonStore.normalize_records(records, schema_name)
    store.save({key: normalized})
    return jsonify({'success': True, 'total': len(normalized)})


@app.route('/api/courses', methods=['GET', 'POST'])
def manage_courses():
    return _handle_manage_request(_course_store, 'courses', 'course',
                                  ('title', 'provider', 'level', 'description',
                                   'skills', 'career_paths'))


@app.route('/api/courses/item', methods=['POST', 'DELETE'])
def manage_course_item():
    guard = _require_admin()
    if guard:
        return guard
    return _handle_item_request(_course_store, 'courses', 'course')


@app.route('/api/jobs', methods=['GET', 'POST'])
def manage_jobs():
    return _handle_manage_request(_jobs_store, 'jobs', 'job',
                                  ('title', 'company', 'location', 'description',
                                   'requirements', 'salary'))


@app.route('/api/jobs/item', methods=['POST', 'DELETE'])
def manage_job_item():
    guard = _require_admin()
    if guard:
        return guard
    return _handle_item_request(_jobs_store, 'jobs', 'job')


def _handle_item_request(store, key, schema_name):
    """Upsert / delete a single record by id — O(1) ops for large catalogs."""
    data = store.load({}) or {}
    records = data.get(key, [])

    if request.method == 'DELETE':
        item_id = request.args.get('id', '').strip()
        if not item_id:
            return jsonify({'error': '缺少 id 参数'}), 400
        kept = [r for r in records if str(r.get('id', '')) != str(item_id)]
        if len(kept) == len(records):
            return jsonify({'error': '记录不存在'}), 404
        store.save({key: kept})
        return jsonify({'success': True})

    payload = request.get_json(silent=True) or {}
    item = payload.get(key[:-1])  # 'course' / 'job'
    if not isinstance(item, dict):
        return jsonify({'error': f'请求体必须包含 {key[:-1]} 对象'}), 400
    ok, err = JsonStore.validate_records([item], schema_name)
    if not ok:
        return jsonify({'error': err}), 400
    item = JsonStore.normalize_records([item], schema_name)[0]

    item_id = item.get('id')
    if not item_id:
        item_id = f'{key[:-1][0]}{int(time.time() * 1000)}'
        item['id'] = item_id

    replaced = False
    for i, rec in enumerate(records):
        if str(rec.get('id', '')) == str(item_id):
            records[i] = item
            replaced = True
            break
    if not replaced:
        records.append(item)

    store.save({key: records})
    return jsonify({'success': True, 'id': item_id})


# ---------------------------------------------------------------------------
# User-facing APIs
# ---------------------------------------------------------------------------

@app.route('/api/me', methods=['GET'])
def me():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({
        'success': True,
        'user': session['user'],
        'profile': current_user_data()
    })


@app.route('/analyze_profile', methods=['POST'])
def analyze_profile():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        profile = current_user_data()
        for field in FORM_FIELDS:
            profile[field] = request.form.get(field, '').strip()
        # Re-assign to mark the session modified: mutating the nested dict in
        # place does NOT set Flask's session.modified, so the profile would
        # never be persisted when user_data was pre-seeded (e.g. by /api/me).
        session['user_data'] = profile

        if not all(profile.get(f) for f in FORM_FIELDS):
            return jsonify({'success': False, 'error': '请完整填写所有个人信息字段'}), 400

        analysis = career_analyzer.analyze_career(profile)

        analyses = load_analyses()
        phone = session['user']['phone']
        history = analyses.get(phone, [])
        history.append({
            'id': f'h{int(time.time() * 1000)}',
            'ts': int(time.time()),
            'profile': profile,
            'analysis': analysis,
        })
        analyses[phone] = history[-HISTORY_LIMIT:]
        save_analyses(analyses)

        return jsonify({'success': True, 'analysis': analysis})
    except Exception as e:
        print(f'[error] career analysis: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/search_jobs', methods=['POST'])
def search_jobs():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        keyword = request.form.get('keyword', '').strip()
        location = request.form.get('location', '').strip()
        career_analysis = request.form.get('career_analysis', '')
        user_input = {
            'keyword': keyword,
            'location': location,
            'career_analysis': career_analysis
        }
        recommended_job = job_matcher.job_matching(user_input, current_user_data())
        return jsonify(recommended_job or [])
    except ValueError as e:
        print(f'[warn] job search: {e}')
        return jsonify([])
    except Exception as e:
        print(f'[error] job search: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/search_course', methods=['POST'])
def search_course():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        keyword = request.form.get('keyword', '').strip()
        career_analysis = request.form.get('career_analysis', '')
        user_input = {'keyword': keyword}
        recommended_courses = course_matcher.course_matching(user_input, career_analysis)
        return jsonify(recommended_courses or [])
    except ValueError as e:
        print(f'[warn] course search: {e}')
        return jsonify([])
    except Exception as e:
        print(f'[error] course search: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats/overview', methods=['GET'])
def stats_overview():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    courses = (_course_store.load({}) or {}).get('courses', [])
    jobs = (_jobs_store.load({}) or {}).get('jobs', [])
    return jsonify(compute_overview(courses, jobs))


@app.route('/api/history', methods=['GET'])
def list_history():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    analyses = load_analyses()
    history = analyses.get(session['user']['phone'], [])
    return jsonify({'success': True, 'items': list(reversed(history))})


@app.route('/api/history/<item_id>', methods=['DELETE'])
def delete_history(item_id):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    analyses = load_analyses()
    phone = session['user']['phone']
    history = [h for h in analyses.get(phone, [])
               if str(h.get('id')) != str(item_id)]
    analyses[phone] = history
    save_analyses(analyses)
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# AI mock interview
# ---------------------------------------------------------------------------

def _interview_session(phone, session_id):
    interviews = load_interviews()
    for rec in interviews.get(phone, []):
        if str(rec.get('id')) == str(session_id):
            return rec
    return None


def _parse_question_count(raw):
    try:
        n = int(raw)
    except (TypeError, ValueError):
        n = 5
    return max(3, min(8, n))


@app.route('/mock_interview/start', methods=['POST'])
def start_mock_interview():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        target_position = request.form.get('target_position', '').strip()
        if not target_position:
            return jsonify({'success': False, 'error': '请填写目标职位'}), 400
        num_questions = _parse_question_count(request.form.get('num_questions', '5'))
        profile = current_user_data()

        questions, source = mock_interview_engine.generate_questions(
            profile, target_position, num_questions)

        session_id = f'i{int(time.time() * 1000)}'
        record = {
            'id': session_id,
            'ts': int(time.time()),
            'profile': profile,
            'target_position': target_position,
            'source': source,
            'questions': questions['questions'],
            'answers': [],
            'status': 'in_progress',
            'summary': None,
        }
        interviews = load_interviews()
        phone = session['user']['phone']
        history = interviews.get(phone, [])
        history.append(record)
        interviews[phone] = history[-HISTORY_LIMIT:]
        save_interviews(interviews)

        return jsonify({
            'success': True,
            'session_id': session_id,
            'source': source,
            'questions': record['questions'],
        })
    except Exception as e:
        print(f'[error] mock interview start: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/mock_interview/answer', methods=['POST'])
def submit_interview_answer():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        session_id = request.form.get('session_id', '').strip()
        try:
            qid = int(request.form.get('question_index', ''))
        except ValueError:
            qid = -1
        answer = request.form.get('answer', '').strip()

        phone = session['user']['phone']
        rec = _interview_session(phone, session_id)
        if rec is None:
            return jsonify({'success': False, 'error': '面试会话不存在'}), 404
        if rec.get('status') == 'completed':
            return jsonify({'success': False, 'error': '该面试已完成'}), 400
        if not answer:
            return jsonify({'success': False, 'error': '回答不能为空'}), 400

        questions = rec.get('questions', [])
        question = next((q for q in questions if int(q.get('id', -1)) == qid), None)
        if question is None:
            return jsonify({'success': False, 'error': '题目索引无效'}), 400

        evaluation, source = mock_interview_engine.evaluate_answer(
            question.get('question', ''), question.get('focus', ''), answer)

        rec['answers'].append({
            'question_id': qid,
            'question': question.get('question', ''),
            'focus': question.get('focus', ''),
            'answer': answer,
            'evaluation': evaluation,
        })
        completed = len(rec['answers']) >= len(questions)
        summary = None
        if completed:
            rec['status'] = 'completed'
            summary = MockInterviewEngine.build_summary(
                [a['evaluation'] for a in rec['answers']])
            rec['summary'] = summary

        interviews = load_interviews()
        history = interviews.get(phone, [])
        for i, old in enumerate(history):
            if str(old.get('id')) == str(session_id):
                history[i] = rec
                break
        interviews[phone] = history[-HISTORY_LIMIT:]
        save_interviews(interviews)

        return jsonify({
            'success': True,
            'source': source,
            'evaluation': evaluation,
            'summary': summary,
            'completed': completed,
            'answered': len(rec['answers']),
            'total': len(questions),
        })
    except Exception as e:
        print(f'[error] mock interview answer: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/mock_interview/session', methods=['GET'])
def get_interview_session():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    session_id = request.args.get('session_id', '').strip()
    rec = _interview_session(session['user']['phone'], session_id)
    if rec is None:
        return jsonify({'success': False, 'error': '面试会话不存在'}), 404
    return jsonify({'success': True, 'session': rec})


@app.route('/api/interviews', methods=['GET'])
def list_interviews():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    interviews = load_interviews()
    items = interviews.get(session['user']['phone'], [])
    return jsonify({'success': True, 'items': list(reversed(items))})


@app.route('/api/interviews/<item_id>', methods=['DELETE'])
def delete_interview(item_id):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    interviews = load_interviews()
    phone = session['user']['phone']
    history = [h for h in interviews.get(phone, [])
               if str(h.get('id')) != str(item_id)]
    interviews[phone] = history
    save_interviews(interviews)
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# Long-term career planning
# ---------------------------------------------------------------------------

@app.route('/career_plan/generate', methods=['POST'])
def generate_career_plan():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        profile = current_user_data()
        career_analysis = request.form.get('career_analysis', '').strip()
        if not any(profile.get(f) for f in FORM_FIELDS):
            return jsonify({'success': False, 'error': '请先填写并保存个人信息'}), 400

        plan, source = career_planner.generate_plan(profile, career_analysis)

        plan_id = f'p{int(time.time() * 1000)}'
        record = {
            'id': plan_id,
            'ts': int(time.time()),
            'profile': profile,
            'career_analysis': career_analysis,
            'plan': plan,
        }
        plans = load_plans()
        phone = session['user']['phone']
        history = plans.get(phone, [])
        history.append(record)
        plans[phone] = history[-HISTORY_LIMIT:]
        save_plans(plans)

        return jsonify({'success': True, 'plan_id': plan_id, 'plan': plan})
    except Exception as e:
        print(f'[error] career plan generate: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/career_plan/latest', methods=['GET'])
def get_latest_career_plan():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    plans = load_plans()
    history = plans.get(session['user']['phone'], [])
    if not history:
        return jsonify({'success': True, 'plan': None})
    return jsonify({'success': True, 'plan': history[-1]})


@app.route('/api/plans', methods=['GET'])
def list_plans():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    plans = load_plans()
    items = plans.get(session['user']['phone'], [])
    return jsonify({'success': True, 'items': list(reversed(items))})


@app.route('/api/plans/<item_id>', methods=['DELETE'])
def delete_plan(item_id):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    plans = load_plans()
    phone = session['user']['phone']
    history = [h for h in plans.get(phone, [])
               if str(h.get('id')) != str(item_id)]
    plans[phone] = history
    save_plans(plans)
    return jsonify({'success': True})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'ZhituCareer+'})


# ---------------------------------------------------------------------------
# Error handlers & session guard
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not Found'}), 404
    return redirect(url_for('login'))


@app.errorhandler(500)
def server_error(e):
    print(f'[error] 500: {e}')
    if request.path.startswith('/api/'):
        return jsonify({'error': '服务器内部错误，请稍后重试'}), 500
    return render_template('index.html'), 500


@app.errorhandler(413)
def too_large(_):
    return jsonify({'error': '请求体过大，请减小提交内容'}), 413


@app.before_request
def check_session():
    public_endpoints = {'login', 'register', 'static', 'health'}
    if request.endpoint not in public_endpoints and 'user' not in session:
        # JSON endpoints must answer with JSON, not a redirect the client
        # cannot consume.
        if request.path.startswith('/api/') or request.endpoint in JSON_API_ENDPOINTS:
            return jsonify({'error': 'Unauthorized'}), 401
        return redirect(url_for('login'))


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

def seed_default_users():
    users = load_users()
    if not users:
        save_users([
            {'phone': '13800000000', 'password': generate_password_hash('admin123'),
             'role': 'admin', 'name': 'Admin User'},
            {'phone': '13900000000', 'password': generate_password_hash('user123'),
             'role': 'user', 'name': 'Regular User'}
        ])
        print('[init] seeded default users to data/users.json')


if __name__ == '__main__':
    seed_default_users()
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    print(f'[start] ZhituCareer+ listening on http://{host}:{port}')
    app.run(host=host, port=port, debug=debug)
