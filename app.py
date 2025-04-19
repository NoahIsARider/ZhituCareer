from flask import Flask, render_template, request, jsonify
from career_model import CareerAnalyzer
from job_matching import JobMatcher
from course_matching import CourseMatcher
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-2025'

# 简化的表单字段
FORM_FIELDS = ['education', 'major', 'skills', 'experience', 'career_goals']

# 创建实例
career_analyzer = CareerAnalyzer()
job_matcher = JobMatcher()
course_matcher = CourseMatcher()

@app.route('/')
def index():
    return render_template('index.html')

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
        return jsonify(recommended_courses)
    except Exception as e:
        print(f'Error in course search: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
