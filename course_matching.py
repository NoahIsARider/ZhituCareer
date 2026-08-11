import os
import threading

from agent.course_matching_agent import CourseMatchingAgent
from agent.llm_client import LLMClient, create_llm_client
from data_store import JsonStore
from fallback_matcher import FallbackCourseMatcher
from retrieval import HybridRetriever

RETRIEVE_TOP_K = int(os.getenv('RETRIEVE_TOP_K', '20'))
FALLBACK_TOP_K = 3


def _build_query(user_input, career_analysis):
    parts = []
    keyword = user_input.get('keyword', '')
    if keyword:
        parts.append(str(keyword))
    if career_analysis:
        parts.append(str(career_analysis)[:800])
    return ' '.join(parts)


def normalize_course_result(result):
    if isinstance(result, dict):
        if result.get('error') or not result.get('title'):
            return []
        return [result]
    if isinstance(result, list):
        return [x for x in result
                if isinstance(x, dict) and x.get('title')]
    return []


class CourseMatcher:
    def __init__(self, client=None):
        self.client = client or create_llm_client()
        self.course_matching_agent = CourseMatchingAgent(self.client)
        self.llm = LLMClient(self.client)
        self.fallback = FallbackCourseMatcher()
        self._retriever = None
        self._retriever_mtime = None
        self._retriever_size = None
        self._lock = threading.Lock()
        self.courses_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'data', 'course.json')

    def load_courses(self):
        store = JsonStore(self.courses_path)
        data = store.load({}) or {}
        return data.get('courses', [])

    def _get_retriever(self):
        try:
            stat = os.stat(self.courses_path)
            mtime, size = stat.st_mtime, stat.st_size
        except OSError:
            mtime, size = 0, 0
        with self._lock:
            if (self._retriever is None or mtime != self._retriever_mtime
                    or size != self._retriever_size):
                courses = self.load_courses()
                retriever = HybridRetriever(
                    text_fields=['title', 'provider', 'description',
                                 'skills', 'career_paths'],
                    filter_fields=[],
                    boost_fields=['title', 'skills'],
                )
                retriever.index(courses)
                self._retriever = retriever
                self._retriever_mtime = mtime
                self._retriever_size = size
            return self._retriever

    def course_matching(self, user_input, career_analysis):
        courses = self.load_courses()
        if not courses:
            raise ValueError("No courses available for matching")

        retriever = self._get_retriever()
        query = _build_query(user_input, career_analysis)

        candidates = retriever.candidate_docs(query, top_k=RETRIEVE_TOP_K)

        llm_candidates = candidates or courses[:RETRIEVE_TOP_K]
        fallback_candidates = candidates or courses

        try:
            matched_text = self.course_matching_agent.match_courses(
                user_input, career_analysis, llm_candidates)
            parsed = self.llm.parse_json(matched_text)
            result = normalize_course_result(parsed)
            if not result:
                raise ValueError('Model returned no valid course matches')
            return result
        except Exception as e:
            print(f'[warn] LLM course matching failed, using fallback: {e}')
            return self.fallback.match_courses(
                user_input, career_analysis, fallback_candidates, top_k=FALLBACK_TOP_K)
