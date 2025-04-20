from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from career_model import CareerAnalyzer
from course_matching import CourseMatcher
from job_matching import JobMatcher
from dotenv import load_dotenv
import json
import os
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-2025'
app.config['SESSION_PERMANENT'] = False

# 简化的表单字段
FORM_FIELDS = ['education', 'major', 'skills', 'experience', 'career_goals']

# 创建实例
career_analyzer = CareerAnalyzer()
job_matcher = JobMatcher()
course_matcher = CourseMatcher()
def load_users():
    try:
        with open('data/users.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('users', [])
    except Exception as e:
        print(f'Error loading users: {str(e)}')
        return []

@app.route('/')
def index():
    # Always redirect to login page first
    # This ensures users always go through login page when accessing root URL
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Only after successful login, direct users based on their role
    if session.get('user', {}).get('role') == 'admin':
        return redirect(url_for('admin'))
    else:
        return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')
    
    users = load_users()
    user = next((u for u in users if u['phone'] == phone and u['password'] == password), None)
    
    if user:
        session['user'] = user
        return jsonify({
            'success': True,
            'redirect': '/admin' if user['role'] == 'admin' else '/'
        })
    
    return jsonify({
        'success': False,
        'message': '手机号码或密码错误'
    })

@app.route('/logout')
def logout():
    # Clear the entire session
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/api/courses', methods=['GET', 'POST'])
def manage_courses():
    if 'user' not in session or session['user']['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'GET':
        try:
            with open('data/course.json', 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            with open('data/course.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/jobs', methods=['GET', 'POST'])
def manage_jobs():

    
    if 'user' not in session or session['user']['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'GET':
        try:
            with open('data/jobs.json', 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            with open('data/jobs.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/analyze_profile', methods=['POST'])
def analyze_profile():
    try:
        # 获取表单数据
        user_data = {}
        for field in FORM_FIELDS:
            user_data[field] = request.form.get(field, '')
        
        # 打印用户输入的内容
        print('\n用户输入信息:')
        for field, value in user_data.items():
            print(f'{field}: {value}')
        print('-' * 50)
        
        # 使用CareerAnalyzer进行分析
        analysis = career_analyzer.analyze_career(user_data)
        
        # 返回结果
        return jsonify({
            'success': True,
            'analysis': analysis
        })
                
    except Exception as e:
        print(f'Error in career analysis: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/search_jobs', methods=['POST'])
def search_jobs():
    keyword = request.form.get('keyword', '')
    location = request.form.get('location', '')
    career_analysis = request.form.get('career_analysis', '')
    user_input = {
        'keyword': keyword,
        'location': location,
        'career_analysis': career_analysis
    }
    print('\n用户输入信息:')
    print(f"keyword: {keyword}, location: {location}")
    print(f"career analysis: {career_analysis}")
    recommended_job = job_matcher.job_matching(user_input)
    print(recommended_job)
    return jsonify(recommended_job)

@app.route('/search_course', methods=['POST'])
def search_course():
    try:
        keyword = request.form.get('keyword', '')
        career_analysis = request.form.get('career_analysis', '')
        user_input = {'keyword': keyword}
        
        print('\n用户课程搜索信息:')
        print(f"keyword: {keyword}")
        print(f"career analysis: {career_analysis}")
        
        recommended_courses = course_matcher.course_matching(user_input, career_analysis)
        print(recommended_courses)
        return jsonify(recommended_courses)
    except Exception as e:
        print(f'Error in course search: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.before_request
def check_session():
    # Ensure user is authenticated for all routes except login
    if request.endpoint != 'login' and request.endpoint != 'static':
        if 'user' not in session:
            return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
