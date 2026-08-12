"""Long-term career planning agent (LLM path).

Produces a 5-year, three-phase career roadmap as strict JSON. The high-level
engine (:class:`career_plan.CareerPlanner`) wraps this agent and falls back
to a deterministic local planner when the API is unavailable.
"""

from agent.llm_client import LLMClient

MODEL = 'LLM-Research/Meta-Llama-3.1-8B-Instruct'


class CareerPlanningAgent:
    """Generates a long-term career roadmap from a user profile."""

    def __init__(self, client):
        self.llm = LLMClient(client)

    def generate_plan(self, profile, career_analysis=''):
        prompt = f"""请基于以下求职者信息，制定一份 5 年长期职业发展规划，分为三个阶段（0-1 年、1-3 年、3-5 年）。

求职者信息：
学历：{profile.get('education', '')}
专业：{profile.get('major', '')}
技能特长：{profile.get('skills', '')}
工作经验：{profile.get('experience', '')}
职业目标：{profile.get('career_goals', '')}

职业分析参考：
{career_analysis or '（暂无）'}

要求：
1. 三阶段主题递进：筑基 → 深耕 → 跃迁
2. 每阶段给出可执行的目标、行动、里程碑与量化 KPI
3. 识别关键风险与应对策略
4. 只返回 JSON 结果，不要任何解释，格式如下：
{{
    "horizon_years": 5,
    "summary": "总体路线概述（2-3 句话）",
    "phases": [
        {{
            "period": "0-1年",
            "theme": "阶段主题",
            "goals": ["目标1", "目标2"],
            "actions": ["行动1", "行动2", "行动3"],
            "milestones": ["里程碑1", "里程碑2"],
            "kpis": ["量化指标1", "量化指标2"]
        }},
        {{
            "period": "1-3年",
            "theme": "阶段主题",
            "goals": ["目标1", "目标2"],
            "actions": ["行动1", "行动2", "行动3"],
            "milestones": ["里程碑1", "里程碑2"],
            "kpis": ["量化指标1", "量化指标2"]
        }},
        {{
            "period": "3-5年",
            "theme": "阶段主题",
            "goals": ["目标1", "目标2"],
            "actions": ["行动1", "行动2", "行动3"],
            "milestones": ["里程碑1", "里程碑2"],
            "kpis": ["量化指标1", "量化指标2"]
        }}
    ],
    "risks": [
        {{"risk": "风险描述", "mitigation": "应对策略"}}
    ]
}}"""
        return self.llm.chat(
            MODEL,
            '你是一位资深的长期职业规划顾问，擅长制定系统化、可执行的职业发展路线图。',
            prompt
        )
