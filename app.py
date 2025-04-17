from flask import Flask, render_template, request, jsonify
from career_model import CareerAnalyzer
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-2025'

# 简化的表单字段
FORM_FIELDS = ['education', 'major', 'skills', 'experience', 'career_goals']

# 创建CareerAnalyzer实例
career_analyzer = CareerAnalyzer()

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)

@app.route('/search_jobs', methods=['POST'])
def search_jobs():
    keyword = request.form.get('keyword', '')
    location = request.form.get('location', '')
    
    # 基于关键词和位置搜索职位
    # Integrate JobMatchingAgent
    agent = JobMatchingAgent(client)
    user_input = {'keyword': keyword, 'location': location}
    job_search_criteria = {'location': location}
    available_jobs = recommend_jobs(None, location)
    recommended_job = agent.match_job(user_input, job_search_criteria, available_jobs)
    return jsonify(recommended_job)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
