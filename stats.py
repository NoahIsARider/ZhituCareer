"""Aggregate statistics over the course & job catalogs for the dashboard.

The results feed the ECharts data-insight widgets on the user dashboard, so
the project can be demoed with real numbers straight out of the box.
"""

import re
from collections import Counter

from agent.market_analysis_agent import MarketDataScraper

_market_scraper = MarketDataScraper()

SALARY_BUCKETS = ['10k 以下', '10-20k', '20-30k', '30-50k', '50k 以上']

_CITY_RE = re.compile(r'([\u4e00-\u9fa5]{2,4}?市)')
_SALARY_RANGE_RE = re.compile(
    r'(\d+(?:\.\d+)?)\s*(?:-|~|—|至|到)\s*(\d+(?:\.\d+)?)\s*k',
    flags=re.IGNORECASE)
_SALARY_SINGLE_RE = re.compile(r'(\d+(?:\.\d+)?)\s*k', flags=re.IGNORECASE)


def _parse_salary_k(salary):
    """Extract the lower bound of a salary string in thousands, or None."""
    if not salary:
        return None
    text = str(salary)
    match = _SALARY_RANGE_RE.search(text)
    if match:
        return float(match.group(1))
    match = _SALARY_SINGLE_RE.search(text)
    return float(match.group(1)) if match else None


def salary_bucket(k):
    if k is None:
        return None
    if k < 10:
        return '10k 以下'
    if k < 20:
        return '10-20k'
    if k < 30:
        return '20-30k'
    if k < 50:
        return '30-50k'
    return '50k 以上'


def _city_of(location):
    location = (location or '').strip()
    match = _CITY_RE.search(location)
    return match.group(1) if match else (location[:4] or '未知')


def _top(items, key, n=8):
    return Counter(key(item) for item in items).most_common(n)


def compute_overview(courses, jobs):
    """Return dashboard-ready aggregates for the given catalogs."""
    job_locations = _top(jobs, lambda j: _city_of(j.get('location', '')), n=8)

    salary_counts = Counter()
    for job in jobs:
        bucket = salary_bucket(_parse_salary_k(job.get('salary', '')))
        if bucket:
            salary_counts[bucket] += 1
    salary_distribution = [(b, salary_counts.get(b, 0)) for b in SALARY_BUCKETS]

    skill_counts = Counter()
    for job in jobs:
        for skill in job.get('requirements') or []:
            skill_counts[skill] += 1
    top_skills = skill_counts.most_common(10)

    level_counts = Counter(
        (course.get('level', '') or '') or '未知' for course in courses)

    return {
        'jobs': {
            'total': len(jobs),
            'by_location': job_locations,
            'salary_distribution': salary_distribution,
            'top_skills': top_skills,
        },
        'courses': {
            'total': len(courses),
            'by_level': list(level_counts.items()),
        },
        'market': _market_scraper.scrape_market_analysis(),
    }
