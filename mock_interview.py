"""AI mock interview engine with a deterministic local fallback.

Mirrors the career-analysis architecture: the LLM path is preferred; when the
API is unavailable (no key, quota, network, invalid JSON) a rule-based local
engine takes over so the feature always works.
"""

import hashlib
import json
import os

from agent.llm_client import LLMClient, create_llm_client, get_model
from agent.interview_agent import InterviewAgent
from cache import TTLCache
from fallback_matcher import detect_career_domain

SESSION_CACHE_TTL = int(os.getenv('INTERVIEW_CACHE_TTL', '600'))

# ---------------------------------------------------------------------------
# Local question bank (fallback path), keyed by career domain name
# ---------------------------------------------------------------------------

_GENERIC_QUESTIONS = [
    {
        'focus': '自我介绍与动机',
        'question': '请做一个简单的自我介绍，并说明你为什么对这个岗位感兴趣？',
        'expected_points': ['结构清晰', '突出与岗位匹配的经历', '表达求职动机'],
    },
    {
        'focus': '项目经验',
        'question': '请介绍一个你最引以为傲的项目，你在其中承担了什么角色，遇到了什么困难？',
        'expected_points': ['项目背景清晰', '明确个人贡献', '有复盘与思考'],
    },
    {
        'focus': '团队协作',
        'question': '当你的想法和团队成员不一致时，你会怎么处理？请举例说明。',
        'expected_points': ['沟通方式', '以数据/事实说服', '尊重他人意见'],
    },
    {
        'focus': '抗压能力',
        'question': '如果交付期限非常紧张，而任务远超预期工作量，你会如何应对？',
        'expected_points': ['优先级管理', '主动沟通风险', '保证核心目标'],
    },
    {
        'focus': '职业规划',
        'question': '未来三到五年，你希望自己在职业上达到什么样的状态？',
        'expected_points': ['目标明确', '与岗位成长路径契合', '有可执行路径'],
    },
]

_DOMAIN_QUESTIONS = {
    '人工智能 / 机器学习工程师': [
        {'focus': '机器学习基础',
         'question': '请解释一下过拟合的成因，以及你常用的防止过拟合的手段。',
         'expected_points': ['数据/模型/训练多个角度', '正则化/交叉验证/数据增强']},
        {'focus': '深度学习',
         'question': '如何为你的模型选择合适的损失函数与评估指标？',
         'expected_points': ['任务类型与损失函数对应', '评估指标贴合业务']},
        {'focus': '工程落地',
         'question': '你如何把一个训练好的模型部署到生产环境并保证稳定性？',
         'expected_points': ['模型压缩/量化', '监控与回滚', '延迟与吞吐权衡']},
    ],
    '后端开发工程师': [
        {'focus': '系统设计',
         'question': '如何设计一个支持高并发的短链接服务？请说明关键设计点。',
         'expected_points': ['缓存策略', '存储选型', '限流与降级']},
        {'focus': '数据库',
         'question': 'MySQL 索引为什么使用 B+ 树而不是哈希表？什么场景下适合哈希索引？',
         'expected_points': ['范围查询', '磁盘 IO 特性', '等值查询场景']},
        {'focus': '并发编程',
         'question': '什么是死锁？如何避免死锁？请举例说明。',
         'expected_points': ['死锁四条件', '破坏条件的策略']},
    ],
    '前端开发工程师': [
        {'focus': 'JavaScript 基础',
         'question': '解释一下事件循环（Event Loop），以及宏任务和微任务的区别。',
         'expected_points': ['调用栈与任务队列', '执行顺序']},
        {'focus': '性能优化',
         'question': '首屏加载性能优化你会从哪些方面入手？',
         'expected_points': ['资源加载', '渲染路径', '缓存']},
        {'focus': '框架原理',
         'question': 'Vue/React 的响应式原理是什么？为什么需要虚拟 DOM？',
         'expected_points': ['数据劫持/发布订阅', 'diff 算法', '性能权衡']},
    ],
    '数据分析师': [
        {'focus': '分析思维',
         'question': '如果某天 App 的新用户留存率突然下降，你会如何开展分析？',
         'expected_points': ['假设拆解', '数据口径', '归因与结论']},
        {'focus': '统计基础',
         'question': 'AB 实验中如何判断实验结果是否显著？常见的陷阱有哪些？',
         'expected_points': ['假设检验', '样本量', '多重比较']},
        {'focus': '业务指标',
         'question': '如何为一个业务场景设计核心指标体系？',
         'expected_points': ['北极星指标', '拆解维度', '可落地']},
    ],
    '网络安全工程师': [
        {'focus': 'Web 安全',
         'question': '请说明 SQL 注入的原理、危害与防护手段。',
         'expected_points': ['参数化查询', '输入校验', '最小权限']},
        {'focus': '攻防思维',
         'question': '如果公司内网出现疑似横向移动，你会如何排查与处置？',
         'expected_points': ['日志分析', '隔离措施', '应急响应流程']},
    ],
    '云计算 / DevOps 工程师': [
        {'focus': '容器化',
         'question': '请说明 Docker 镜像与容器的关系，以及镜像分层的作用。',
         'expected_points': ['镜像分层复用', '容器隔离']},
        {'focus': 'CI/CD',
         'question': '如何设计一条可靠的 CI/CD 流水线？发布失败时如何快速回滚？',
         'expected_points': ['多阶段流水线', '灰度发布', '回滚策略']},
    ],
    '产品经理': [
        {'focus': '需求分析',
         'question': '如何判断一个用户需求是否值得做？请给出你的判断框架。',
         'expected_points': ['用户价值', '商业价值', '成本与优先级']},
        {'focus': '产品思维',
         'question': '如果新功能上线后核心指标没有提升，你会怎么做？',
         'expected_points': ['复盘假设', '数据归因', '快速迭代']},
    ],
    'UI/UX 设计师': [
        {'focus': '设计思维',
         'question': '请描述一次你通过用户研究改进设计的经历。',
         'expected_points': ['研究方法', '洞察到方案', '验证']},
        {'focus': '设计系统',
         'question': '设计系统如何帮助团队提升效率并保持一致性？',
         'expected_points': ['组件复用', '规范一致', '协作效率']},
    ],
}


def _build_fallback_questions(profile, target_position, num_questions):
    """Deterministic question list from the local domain bank + generic set."""
    domain, _ = detect_career_domain(profile)
    bank = []
    if domain:
        bank += _DOMAIN_QUESTIONS.get(domain['name'], [])
    bank += _GENERIC_QUESTIONS

    questions = []
    for idx, item in enumerate(bank[:num_questions], 1):
        questions.append({
            'id': idx,
            'question': item['question'],
            'focus': item['focus'],
            'expected_points': item['expected_points'],
        })
    if len(questions) < num_questions:
        for idx in range(len(questions) + 1, num_questions + 1):
            questions.append({
                'id': idx,
                'question': f'请结合你应聘的「{target_position or "目标岗位"}」岗位，谈谈你最大的优势是什么？',
                'focus': '自我认知与岗位匹配',
                'expected_points': ['优势与岗位契合', '有具体事例支撑'],
            })
    return questions


def _fallback_score(answer):
    """Rule-based 0-100 score: rewards length, structure and keywords."""
    answer = (answer or '').strip()
    if not answer:
        return 0
    length = len(answer)
    if length < 20:
        return 30
    if length < 60:
        return 50
    if length < 150:
        return 70
    if length < 300:
        return 85
    return 92


class FallbackMockInterview:
    """Local, deterministic mock interview engine (no LLM call)."""

    def generate_questions(self, profile, target_position, num_questions=5):
        return _build_fallback_questions(profile, target_position, num_questions)

    def evaluate_answer(self, question, focus, answer):
        answer = (answer or '').strip()
        score = _fallback_score(answer)
        if score < 50:
            feedback = '回答过于简短，建议补充具体事例和思考过程。'
        elif score < 70:
            feedback = '回答基本到位，但内容偏泛，建议结合项目经历给出更具体的细节。'
        elif score < 85:
            feedback = '回答结构清晰、内容充实，展示了较好的专业能力。'
        else:
            feedback = '回答非常出色，逻辑完整且有深度，展现了扎实的积累。'
        return {
            'score': score,
            'feedback': feedback,
            'suggestion': '建议用 STAR 法则组织回答：情境-任务-行动-结果，并补充数据量化成果。',
            'strengths': ['回答完整', '态度积极'],
            'weaknesses': ['可进一步量化成果'] if score < 85 else [],
        }


class MockInterviewEngine:
    """High-level engine: LLM first, local fallback, session cache."""

    def __init__(self, client=None):
        self.client = client or create_llm_client()
        self.model = get_model()
        self.agent = InterviewAgent(self.client)
        self.llm = LLMClient(self.client)
        self.fallback = FallbackMockInterview()
        self._cache = TTLCache(ttl_seconds=SESSION_CACHE_TTL, maxsize=64)

    def _cache_key(self, profile, target_position, num_questions):
        canonical = json.dumps({
            'p': profile, 't': target_position, 'n': num_questions,
        }, ensure_ascii=False, sort_keys=True)
        return hashlib.md5(canonical.encode('utf-8')).hexdigest()

    def generate_questions(self, profile, target_position, num_questions=5):
        """Return (questions, source). Never raises on LLM errors."""
        key = self._cache_key(profile, target_position, num_questions)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        try:
            raw = self.agent.generate_questions(
                profile, target_position, num_questions)
            parsed = self.llm.parse_json(raw)
            questions = (parsed or {}).get('questions')
            if not isinstance(questions, list) or not questions:
                raise ValueError('invalid question JSON from model')
            cleaned = []
            for idx, q in enumerate(questions[:num_questions], 1):
                if not isinstance(q, dict) or not q.get('question'):
                    continue
                cleaned.append({
                    'id': idx,
                    'question': str(q.get('question')),
                    'focus': str(q.get('focus') or '综合能力'),
                    'expected_points': [str(p) for p in (q.get('expected_points') or [])],
                })
            if not cleaned:
                raise ValueError('no valid questions from model')
            result = ({'source': 'llm', 'questions': cleaned}, 'llm')
            self._cache.set(key, result, ttl_seconds=SESSION_CACHE_TTL)
            return result
        except Exception as e:
            print(f'[warn] LLM interview questions failed, using fallback: {e}')
            questions = self.fallback.generate_questions(
                profile, target_position, num_questions)
            return ({'source': 'local', 'questions': questions}, 'local')

    def evaluate_answer(self, question, focus, answer):
        """Return (evaluation_dict, source). Never raises on LLM errors."""
        if not (answer or '').strip():
            return {
                'score': 0,
                'feedback': '回答不能为空',
                'suggestion': '请认真组织语言后作答',
                'strengths': [],
                'weaknesses': ['未作答'],
            }, 'local'
        try:
            raw = self.agent.evaluate_answer(question, focus, answer)
            parsed = self.llm.parse_json(raw)
            if not isinstance(parsed, dict) or not isinstance(parsed.get('score'), (int, float)):
                raise ValueError('invalid evaluation JSON from model')
            score = max(0, min(100, int(round(float(parsed['score'])))))
            return ({
                'source': 'llm',
                'score': score,
                'feedback': str(parsed.get('feedback') or ''),
                'suggestion': str(parsed.get('suggestion') or ''),
                'strengths': [str(s) for s in (parsed.get('strengths') or [])],
                'weaknesses': [str(w) for w in (parsed.get('weaknesses') or [])],
            }, 'llm')
        except Exception as e:
            print(f'[warn] LLM answer evaluation failed, using fallback: {e}')
            result = self.fallback.evaluate_answer(question, focus, answer)
            result['source'] = 'local'
            return result, 'local'

    @staticmethod
    def build_summary(evaluations):
        """Aggregate per-answer evaluations into an interview summary."""
        if not evaluations:
            return {
                'avg_score': 0,
                'verdict': '尚未完成作答',
                'strengths': [],
                'weaknesses': [],
            }
        scores = [int(e.get('score', 0)) for e in evaluations]
        avg = round(sum(scores) / len(scores))
        strengths = []
        weaknesses = []
        for e in evaluations:
            strengths.extend(e.get('strengths') or [])
            weaknesses.extend(e.get('weaknesses') or [])
        # Deduplicate while keeping order
        seen = set()
        strengths = [s for s in strengths if not (s in seen or seen.add(s))]
        seen = set()
        weaknesses = [w for w in weaknesses if not (w in seen or seen.add(w))]
        if avg >= 85:
            verdict = '表现优秀，与目标岗位高度匹配，可以进入下一轮。'
        elif avg >= 70:
            verdict = '表现良好，核心能力达标，建议针对薄弱点继续打磨。'
        elif avg >= 50:
            verdict = '表现一般，建议补充项目经验并加强面试表达训练。'
        else:
            verdict = '准备不足，建议系统复习岗位知识并进行多轮模拟练习。'
        return {
            'avg_score': avg,
            'verdict': verdict,
            'strengths': strengths[:5],
            'weaknesses': weaknesses[:5],
        }
