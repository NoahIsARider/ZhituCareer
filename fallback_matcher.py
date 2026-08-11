"""Deterministic rule-based matchers used when the LLM is unavailable.

The AI features should never leave the user empty-handed: whenever the LLM
call fails (no API key, quota exceeded, network error, invalid output) the
system falls back to these pure-Python matchers, which always return the
same JSON contract as the LLM path. This guarantees the application keeps
working even in offline / degraded mode.
"""

from retrieval import tokenize

# ---------------------------------------------------------------------------
# Local career-analysis knowledge base: skill keyword -> career direction
# ---------------------------------------------------------------------------

CAREER_DOMAINS = [
    {
        'name': '人工智能 / 机器学习工程师',
        'keywords': ['python', 'machine learning', 'deep learning', 'tensorflow',
                     'pytorch', '人工智能', '机器学习', '深度学习', 'nlp', 'llm',
                     '大模型', 'cv', '推荐算法', '算法'],
        'advice': '深耕算法基础与工程落地能力，积累端到端建模与推理优化的实践经验。',
        'skills': '分布式训练、模型部署（ONNX/TensorRT）、提示词工程与 RAG 应用、MLOps。',
        'positions': ['AI 算法工程师', '机器学习工程师', '大模型应用工程师'],
    },
    {
        'name': '后端开发工程师',
        'keywords': ['java', 'spring', 'go', 'golang', '后端', '后端开发',
                     '微服务', 'api', '数据库', 'redis', 'mysql', 'linux'],
        'advice': '夯实语言基础与系统设计能力，理解高并发、分布式与可观测性。',
        'skills': '微服务架构、消息队列、容器化部署、数据库调优、性能优化。',
        'positions': ['后端开发工程师', 'Java/Go 工程师', '系统架构师'],
    },
    {
        'name': '前端开发工程师',
        'keywords': ['javascript', 'typescript', 'react', 'vue', '前端', '前端开发',
                     'html', 'css', 'webpack', 'node'],
        'advice': '强化组件化思维与性能优化能力，跟进主流框架演进与工程化实践。',
        'skills': 'TypeScript、前端工程化、性能优化、跨端开发（小程序/RN）、可视化。',
        'positions': ['前端开发工程师', 'Web 全栈工程师', '大前端工程师'],
    },
    {
        'name': '数据分析师',
        'keywords': ['数据分析', '数据挖掘', 'sql', 'tableau', 'power bi',
                     'pandas', 'excel', '统计', '可视化', '数分'],
        'advice': '提升从业务问题到数据建模的闭环能力，注重数据驱动决策的表达力。',
        'skills': 'SQL 进阶、Python 数据分析、指标体系搭建、A/B 实验设计、BI 可视化。',
        'positions': ['数据分析师', '商业分析师', '数据产品经理'],
    },
    {
        'name': '网络安全工程师',
        'keywords': ['网络安全', '信息安全', 'security', '渗透', 'ctf', '安全',
                     '攻防', '漏洞', 'soc'],
        'advice': '以攻促防，建立体系化的安全运营与应急响应能力。',
        'skills': '漏洞挖掘、渗透测试、安全运营（SIEM/SOC）、合规与等保、应急响应。',
        'positions': ['安全工程师', '渗透测试工程师', '安全运营分析师'],
    },
    {
        'name': '云计算 / DevOps 工程师',
        'keywords': ['云', '云计算', 'docker', 'kubernetes', 'k8s', 'devops',
                     'aws', '阿里云', '运维', 'ci/cd', '容器'],
        'advice': '构建从基础设施到应用交付的自动化能力，理解云原生全链路。',
        'skills': 'Kubernetes、IaC（Terraform）、CI/CD 流水线、可观测性、成本治理。',
        'positions': ['DevOps 工程师', '云原生工程师', 'SRE 工程师'],
    },
    {
        'name': '产品经理',
        'keywords': ['产品', '产品经理', '用户需求', 'prd', '市场', '运营', '商业'],
        'advice': '强化需求洞察与数据验证能力，培养跨团队协作和商业思维。',
        'skills': '需求分析、用户研究、数据分析、项目管理、商业模型设计。',
        'positions': ['产品经理', 'B 端产品经理', '数据分析型产品经理'],
    },
    {
        'name': 'UI/UX 设计师',
        'keywords': ['ui', 'ux', 'figma', '设计', '交互', '视觉', 'adobe', 'sketch'],
        'advice': '建立以用户为中心的体验设计流程，打通交互与视觉落地能力。',
        'skills': '设计系统、用户研究、交互原型、设计走查与可用性测试。',
        'positions': ['UI 设计师', 'UX 设计师', '交互设计师'],
    },
]


def detect_career_domain(profile):
    """Map a user profile to the most relevant career domain (fallback path)."""
    text = ' '.join([
        str(profile.get('major', '')),
        str(profile.get('skills', '')),
        str(profile.get('career_goals', '')),
        str(profile.get('experience', '')),
    ]).lower()
    best_domain = None
    best_score = 0
    for domain in CAREER_DOMAINS:
        score = sum(1 for kw in domain['keywords'] if kw.lower() in text)
        if score > best_score:
            best_score = score
            best_domain = domain
    return best_domain, best_score


class FallbackCareerAnalyzer:
    """Produces a structured career analysis without any LLM call."""

    def analyze_career(self, profile):
        domain, score = detect_career_domain(profile)
        if domain is None or score == 0:
            return {
                'career_path': '暂未识别到明确的专业方向，建议结合你的专业与技能，从技术开发、'
                               '数据分析、产品、设计等主赛道中选择 1-2 个方向深入。',
                'job_advice': '先通过在线课程和项目实践补齐核心技能，再通过实习或小型项目'
                              '验证方向，逐步建立作品集。',
                'skills_to_improve': '目标岗位核心技能、项目实践能力、求职与面试表达。',
                'recommended_positions': ['软件开发工程师', '数据分析师', '产品经理'],
            }
        return {
            'career_path': f'你的技能与职业目标与「{domain["name"]}」方向高度契合，'
                           f'建议聚焦该赛道建立核心竞争力。',
            'job_advice': domain['advice'],
            'skills_to_improve': domain['skills'],
            'recommended_positions': domain['positions'],
        }


def _token_overlap(tokens_a, tokens_b):
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b)


def _matched_skill_names(user_skills, requirement_text, limit=3):
    user_tokens = set(tokenize(user_skills))
    req_tokens = set(tokenize(requirement_text))
    matched = user_tokens & req_tokens
    keep = []
    seen = set()
    for tok in matched:
        norm = tok.replace(' ', '')
        if norm and norm not in seen:
            seen.add(norm)
            keep.append(norm)
        if len(keep) >= limit:
            break
    return keep


def _keyword_score(keyword, title, text):
    """Score keyword relevance with substring and token overlap.

    Token overlap (which runs through bilingual alias expansion) lets Chinese
    keywords match English catalog entries and vice versa.
    """
    keyword = (keyword or '').strip().lower()
    title = (title or '').lower()
    text = (text or '').lower()
    if not keyword:
        return 0.0
    if keyword in title:
        return 2.0
    if keyword in text:
        return 1.2
    overlap = set(tokenize(keyword)) & set(tokenize(text))
    if overlap:
        return 1.0 + 0.2 * min(3, len(overlap))
    return 0.0


class FallbackJobMatcher:
    """Rule-based job matching with deterministic scoring."""

    def match_jobs(self, user_input, user_data, jobs, top_k=3):
        keyword = str(user_input.get('keyword', '') or '').strip()
        location = str(user_input.get('location', '') or '').strip()
        career_analysis = str(user_input.get('career_analysis', '') or '')
        skills = str(user_data.get('skills', '') or '')
        career_tokens = set(tokenize(career_analysis))

        scored = []
        for job in jobs:
            title = str(job.get('title', '') or '')
            desc = str(job.get('description', '') or '')
            job_loc = str(job.get('location', '') or '')
            reqs = job.get('requirements') or []
            req_text = ' '.join(str(r) for r in reqs)
            job_text = ' '.join([title, desc, req_text]).lower()

            score = 0.0
            reasons = []

            kw_score = _keyword_score(keyword, title, job_text)
            if kw_score >= 2.0:
                reasons.append('职位名称与关键词匹配')
                score += 2.0
            elif kw_score >= 1.2:
                reasons.append('职位内容与关键词匹配')
                score += 1.2
            elif kw_score > 0:
                reasons.append('关键词语义匹配')
                score += kw_score

            if location and location.lower() in job_loc.lower():
                score += 1.5
                reasons.append(f'工作地点符合期望（{job_loc}）')

            skill_overlap = _token_overlap(set(tokenize(skills)), set(tokenize(req_text)))
            if skill_overlap:
                score += min(1.0, skill_overlap * 0.25)
                matched = _matched_skill_names(skills, req_text)
                if matched:
                    reasons.append('技能匹配：' + '、'.join(matched))

            if career_tokens:
                ca_overlap = _token_overlap(career_tokens, set(tokenize(title + desc)))
                if ca_overlap:
                    score += min(0.6, ca_overlap * 0.1)

            if score > 0:
                job_copy = dict(job)
                job_copy['score'] = round(score, 3)
                job_copy['match_reason'] = '；'.join(reasons) or '根据你的搜索偏好推荐'
                scored.append(job_copy)

        scored.sort(key=lambda x: x['score'], reverse=True)
        results = scored[:top_k]
        for item in results:
            item.pop('score', None)
        return results


class FallbackCourseMatcher:
    """Rule-based course matching with deterministic scoring."""

    def match_courses(self, user_input, career_analysis, courses, top_k=3):
        keyword = str(user_input.get('keyword', '') or '').strip()
        career_tokens = set(tokenize(career_analysis))

        scored = []
        for course in courses:
            title = str(course.get('title', '') or '')
            desc = str(course.get('description', '') or '')
            skills = course.get('skills') or []
            paths = course.get('career_paths') or []
            text = ' '.join([title, desc, ' '.join(str(s) for s in skills),
                             ' '.join(str(p) for p in paths)]).lower()

            score = 0.0
            reasons = []

            kw_score = _keyword_score(keyword, title, text)
            if kw_score >= 2.0:
                reasons.append('课程名称与关键词匹配')
                score += 2.0
            elif kw_score >= 1.2:
                reasons.append('课程内容与关键词匹配')
                score += 1.2
            elif kw_score > 0:
                reasons.append('关键词语义匹配')
                score += kw_score

            if career_tokens:
                overlap = _token_overlap(
                    career_tokens,
                    set(tokenize(' '.join([title, desc, ' '.join(str(s) for s in skills),
                                           ' '.join(str(p) for p in paths)]))))
                if overlap:
                    score += min(1.0, overlap * 0.2)
                    reasons.append('与职业分析方向契合')

            if score > 0:
                course_copy = dict(course)
                course_copy['score'] = round(score, 3)
                course_copy['match_reason'] = '；'.join(reasons) or '根据你的学习目标推荐'
                scored.append(course_copy)

        scored.sort(key=lambda x: x['score'], reverse=True)
        results = scored[:top_k]
        for item in results:
            item.pop('score', None)
        return results
