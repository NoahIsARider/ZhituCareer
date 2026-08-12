"""Long-term career planning engine with a deterministic local fallback.

LLM path generates a structured 5-year, three-phase roadmap; when the API is
unavailable a rule-based local planner builds a roadmap from the matched
career domain so the feature never fails.
"""

import hashlib
import json
import os

from agent.llm_client import LLMClient, create_llm_client, get_model
from agent.career_planning_agent import CareerPlanningAgent
from cache import TTLCache
from fallback_matcher import detect_career_domain

PLAN_CACHE_TTL = int(os.getenv('PLAN_CACHE_TTL', '600'))

DEFAULT_HORIZON = 5


def _phases_from_domain(domain):
    """Build a deterministic three-phase roadmap for a career domain."""
    name = domain['name'] if domain else '职业发展'
    advice = domain['advice'] if domain else '结合专业与兴趣，选择 1-2 个主赛道深耕。'
    skills = domain['skills'] if domain else '目标岗位核心技能、项目实践、求职表达。'
    positions = domain['positions'] if domain else ['目标岗位']

    return [
        {
            'period': '0-1年',
            'theme': '筑基：补齐核心能力，完成从学生到职业人的转变',
            'goals': [
                f'系统掌握「{name}」方向的核心知识体系',
                '完成 1-2 个可展示的完整项目，建立作品集',
            ],
            'actions': [
                f'围绕「{skills}」制定学习计划并严格执行',
                '参与开源项目或实习，积累真实业务经验',
                '定期复盘并输出技术/学习笔记',
            ],
            'milestones': ['完成核心课程与认证', '独立交付一个完整项目'],
            'kpis': ['每周有效学习 ≥ 10 小时', '年内完成 ≥ 2 个完整项目'],
        },
        {
            'period': '1-3年',
            'theme': '深耕：进入目标行业，成为团队中的可靠骨干',
            'goals': [
                f'入职目标岗位（{positions[0]}），独立承担业务模块',
                '在某一细分方向形成个人优势',
            ],
            'actions': [
                '深度参与核心项目，主动承担有挑战的模块',
                '建立行业内的人脉与影响力（分享、开源贡献）',
                '持续跟踪前沿技术并落地到工作中',
            ],
            'milestones': ['晋升/承担更高复杂度任务', '主导至少一个关键项目'],
            'kpis': ['绩效达到团队前 30%', '每年主导 ≥ 1 个重点项目'],
        },
        {
            'period': '3-5年',
            'theme': '跃迁：从执行者走向专家或管理者',
            'goals': [
                '成为团队的技术专家或带团队的管理者',
                '形成可复用的方法论与影响力',
            ],
            'actions': [
                '承担技术选型/架构决策或团队管理职责',
                '输出方法论（文章、演讲、培训）',
                '评估长期方向：专家路线 or 管理路线，做出选择',
            ],
            'milestones': ['达到高级/专家职级', '建立可验证的个人品牌'],
            'kpis': ['负责模块/团队业务指标持续增长', '年度输出 ≥ 4 篇高质量内容'],
        },
    ]


def _default_risks():
    return [
        {'risk': '行业与技术快速变化，既有技能可能贬值',
         'mitigation': '保持学习节奏，每年更新一次核心技能栈'},
        {'risk': '长期高压导致倦怠与动力不足',
         'mitigation': '设定阶段性小目标与奖励机制，保持工作生活平衡'},
        {'risk': '职业方向与个人兴趣错配',
         'mitigation': '每年做一次职业复盘，及时调整路线'},
    ]


class FallbackCareerPlanner:
    """Deterministic local career planner (no LLM call)."""

    def generate_plan(self, profile, career_analysis=''):
        domain, score = detect_career_domain(profile)
        phases = _phases_from_domain(domain)
        if domain is None or score == 0:
            summary = ('暂未识别到明确的职业方向，建议在 0-1 年先通过课程与项目实践探索 '
                       '技术开发、数据分析、产品、设计等主赛道，再逐步收敛。')
        else:
            summary = (f'你的技能与职业目标与「{domain["name"]}」方向高度契合，'
                       f'按「筑基 → 深耕 → 跃迁」三阶段推进，5 年内可实现从入门到'
                       f'独当一面的跨越。')
        return {
            'horizon_years': DEFAULT_HORIZON,
            'summary': summary,
            'phases': phases,
            'risks': _default_risks(),
        }


class CareerPlanner:
    """High-level planner: LLM first, local fallback, caching."""

    def __init__(self, client=None):
        self.client = client or create_llm_client()
        self.model = get_model()
        self.agent = CareerPlanningAgent(self.client)
        self.llm = LLMClient(self.client)
        self.fallback = FallbackCareerPlanner()
        self._cache = TTLCache(ttl_seconds=PLAN_CACHE_TTL, maxsize=64)

    def _cache_key(self, profile, career_analysis):
        canonical = json.dumps({'p': profile, 'c': career_analysis or ''},
                               ensure_ascii=False, sort_keys=True)
        return hashlib.md5(canonical.encode('utf-8')).hexdigest()

    @staticmethod
    def _clean_phase(phase):
        def _list(v):
            return [str(x) for x in (v or []) if str(x).strip()]

        return {
            'period': str(phase.get('period') or ''),
            'theme': str(phase.get('theme') or ''),
            'goals': _list(phase.get('goals')),
            'actions': _list(phase.get('actions')),
            'milestones': _list(phase.get('milestones')),
            'kpis': _list(phase.get('kpis')),
        }

    def generate_plan(self, profile, career_analysis=''):
        """Return (plan_dict, source). Never raises on LLM errors."""
        key = self._cache_key(profile, career_analysis)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        try:
            raw = self.agent.generate_plan(profile, career_analysis)
            parsed = self.llm.parse_json(raw)
            if not isinstance(parsed, dict) or not parsed.get('phases'):
                raise ValueError('invalid plan JSON from model')
            phases = [self._clean_phase(p) for p in parsed['phases']]
            phases = [p for p in phases if p['period'] and p['theme']]
            if len(phases) < 3:
                raise ValueError('model returned fewer than 3 phases')
            plan = {
                'horizon_years': int(parsed.get('horizon_years') or DEFAULT_HORIZON),
                'summary': str(parsed.get('summary') or ''),
                'phases': phases[:3],
                'risks': [{
                    'risk': str(r.get('risk') or ''),
                    'mitigation': str(r.get('mitigation') or ''),
                } for r in (parsed.get('risks') or []) if isinstance(r, dict)],
            }
            result = ({'source': 'llm', **plan}, 'llm')
            self._cache.set(key, result, ttl_seconds=PLAN_CACHE_TTL)
            return result
        except Exception as e:
            print(f'[warn] LLM career plan failed, using fallback: {e}')
            plan = self.fallback.generate_plan(profile, career_analysis)
            plan['source'] = 'local'
            return plan, 'local'
