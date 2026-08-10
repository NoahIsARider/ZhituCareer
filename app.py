from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from career_model import CareerAnalyzer
from course_matching import CourseMatcher
from job_matching import JobMatcher
from dotenv import load_dotenv
import json
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
app.config['SESSION_PERMANENT'] = False
app.config['JSON_AS_ASCII'] = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
COURSES_FILE = os.path.join(DATA_DIR, 'course.json')
JOBS_FILE = os.path.join(DATA_DIR, 'jobs.json')

FORM_FIELDS = ['education', 'major', 'skills', 'experience', 'career_goals']

career_analyzer = CareerAnalyzer()
job_matcher = JobMatcher()
course_matcher = CourseMatcher()


def _read_json(path, default=None):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f'[error] loading {path}: {e}')
        return default


def _write_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_users():
    data = _read_json(USERS_FILE, {}) or {}
    return data.get('users', [])


def save_users(users):
    _write_json(USERS_FILE, {'users': users})


def current_user_data():
    return session.setdefault('user_data', {})


def is_admin():
    return session.get('user', {}).get('role') == 'admin'


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


def _require_admin():
    if 'user' not in session or not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    return None


@app.route('/api/courses', methods=['GET', 'POST'])
def manage_courses():
    guard = _require_admin()
    if guard:
        return guard

    if request.method == 'GET':
        data = _read_json(COURSES_FILE, {}) or {}
        return jsonify(data)

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict) or 'courses' not in data:
        return jsonify({'error': '请求体必须包含 courses 字段'}), 400
    _write_json(COURSES_FILE, data)
    return jsonify({'success': True})


@app.route('/api/jobs', methods=['GET', 'POST'])
def manage_jobs():
    guard = _require_admin()
    if guard:
        return guard

    if request.method == 'GET':
        data = _read_json(JOBS_FILE, {}) or {}
        return jsonify(data)

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict) or 'jobs' not in data:
        return jsonify({'error': '请求体必须包含 jobs 字段'}), 400
    _write_json(JOBS_FILE, data)
    return jsonify({'success': True})


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

        if not all(profile.get(f) for f in FORM_FIELDS):
            return jsonify({'success': False, 'error': '请完整填写所有个人信息字段'}), 400

        analysis = career_analyzer.analyze_career(profile)
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
        return jsonify(recommended_job)
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
        return jsonify(recommended_courses)
    except Exception as e:
        print(f'[error] course search: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'ZhituCareer+'})


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


@app.before_request
def check_session():
    public_endpoints = {'login', 'static', 'health'}
    if request.endpoint not in public_endpoints and 'user' not in session:
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Unauthorized'}), 401
        return redirect(url_for('login'))


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
