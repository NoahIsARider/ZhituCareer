import os
import threading

from agent.job_matching_agent import JobMatchingAgent
from agent.llm_client import LLMClient, create_llm_client
from data_store import JsonStore
from fallback_matcher import FallbackJobMatcher
from retrieval import HybridRetriever

# How many pre-filtered candidates are handed to the LLM for final ranking.
RETRIEVE_TOP_K = int(os.getenv('RETRIEVE_TOP_K', '20'))
# How many results the fallback rule-based matcher returns.
FALLBACK_TOP_K = 3


def _build_query(user_input, user_data):
    parts = []
    keyword = user_input.get('keyword', '')
    location = user_input.get('location', '')
    career_analysis = user_input.get('career_analysis', '')
    if keyword:
        parts.append(str(keyword))
    if location:
        parts.append(str(location))
    for field in ('skills', 'career_goals', 'major', 'experience'):
        value = user_data.get(field, '')
        if value:
            parts.append(str(value))
    if career_analysis:
        parts.append(str(career_analysis)[:800])
    return ' '.join(parts)


def normalize_job_result(result):
    """Coerce the LLM output into a clean list of job dicts."""
    if isinstance(result, dict):
        if result.get('error') or not result.get('title'):
            return []
        return [result]
    if isinstance(result, list):
        return [x for x in result
                if isinstance(x, dict) and x.get('title')]
    return []


class JobMatcher:
    def __init__(self, client=None):
        self.client = client or create_llm_client()
        self.job_matching_agent = JobMatchingAgent(self.client)
        self.llm = LLMClient(self.client)
        self.fallback = FallbackJobMatcher()
        self._retriever = None
        self._retriever_mtime = None
        self._retriever_size = None
        self._lock = threading.Lock()
        self.jobs_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'data', 'jobs.json')

    def load_jobs(self):
        store = JsonStore(self.jobs_path)
        data = store.load({}) or {}
        return data.get('jobs', [])

    def _get_retriever(self):
        try:
            stat = os.stat(self.jobs_path)
            mtime, size = stat.st_mtime, stat.st_size
        except OSError:
            mtime, size = 0, 0
        with self._lock:
            if (self._retriever is None or mtime != self._retriever_mtime
                    or size != self._retriever_size):
                jobs = self.load_jobs()
                retriever = HybridRetriever(
                    text_fields=['title', 'company', 'description',
                                 'requirements', 'location'],
                    filter_fields=['location'],
                    boost_fields=['title', 'company'],
                )
                retriever.index(jobs)
                self._retriever = retriever
                self._retriever_mtime = mtime
                self._retriever_size = size
            return self._retriever

    def job_matching(self, user_input, user_data):
        jobs = self.load_jobs()
        if not jobs:
            raise ValueError("No jobs available for matching")

        retriever = self._get_retriever()
        query = _build_query(user_input, user_data)
        location = user_input.get('location', '') or ''
        filters = [('location', location)] if location else None

        candidates = retriever.candidate_docs(
            query, top_k=RETRIEVE_TOP_K, filters=filters)

        # LLM re-ranks a bounded candidate set; when retrieval has no hits we
        # still give it the first slice of the catalog for a best-effort pick.
        llm_candidates = candidates or jobs[:RETRIEVE_TOP_K]
        # The deterministic fallback can afford to scan the whole catalog.
        fallback_candidates = candidates or jobs

        try:
            matched_text = self.job_matching_agent.match_job(
                user_input, user_data, llm_candidates)
            parsed = self.llm.parse_json(matched_text)
            result = normalize_job_result(parsed)
            if not result:
                raise ValueError('Model returned no valid job matches')
            return result
        except Exception as e:
            print(f'[warn] LLM job matching failed, using fallback: {e}')
            return self.fallback.match_jobs(
                user_input, user_data, fallback_candidates, top_k=FALLBACK_TOP_K)
