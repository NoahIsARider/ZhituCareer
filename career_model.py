import hashlib
import json
import os

from agent.llm_client import LLMClient, create_llm_client, get_model
from agent.market_analysis_agent import MarketAnalysisAgent
from agent.user_profile_agent import UserProfileAgent
from agent.job_recommendation_agent import JobRecommendationAgent
from cache import TTLCache
from fallback_matcher import FallbackCareerAnalyzer

SUCCESS_CACHE_TTL = int(os.getenv('ANALYSIS_CACHE_TTL', '3600'))
FALLBACK_CACHE_TTL = int(os.getenv('ANALYSIS_FALLBACK_TTL', '300'))


class CareerAnalyzer:
    def __init__(self, client=None):
        self.client = client or create_llm_client()
        self.model = get_model()
        self.user_profile_agent = UserProfileAgent(self.client)
        self.market_analysis_agent = MarketAnalysisAgent(self.client)
        self.job_recommendation_agent = JobRecommendationAgent(self.client)
        self.llm = LLMClient(self.client)
        self.fallback = FallbackCareerAnalyzer()
        self._cache = TTLCache(ttl_seconds=SUCCESS_CACHE_TTL, maxsize=128)

    def _cache_key(self, user_data):
        canonical = json.dumps(user_data, ensure_ascii=False, sort_keys=True)
        return hashlib.md5(canonical.encode('utf-8')).hexdigest()

    def analyze_career(self, user_data):
        """Run the multi-agent career analysis, never failing on LLM errors.

        Falls back to a deterministic local analysis when the LLM is
        unavailable, and caches results so repeated analyses are instant.
        """
        key = self._cache_key(user_data)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        try:
            result = self._analyze_with_llm(user_data)
            result['source'] = 'llm'
            self._cache.set(key, result, ttl_seconds=SUCCESS_CACHE_TTL)
            return result
        except Exception as e:
            print(f'[warn] LLM career analysis failed, using fallback: {e}')
            result = self.fallback.analyze_career(user_data)
            result['source'] = 'local'
            self._cache.set(key, result, ttl_seconds=FALLBACK_CACHE_TTL)
            return result

    def _analyze_with_llm(self, user_data):
        user_profile_evaluation = self.user_profile_agent.evaluate_user_profile(user_data)
        if not user_profile_evaluation:
            raise ValueError("Failed to evaluate user profile")

        market_analysis = self.market_analysis_agent.analyze_market()
        if not market_analysis:
            raise ValueError("Failed to analyze market")

        job_recommendation = self.job_recommendation_agent.generate_recommendation(
            user_profile_evaluation, market_analysis)
        if not job_recommendation:
            raise ValueError("Failed to generate job recommendation")

        parsed = self.llm.parse_json(job_recommendation)
        if not isinstance(parsed, dict) or not parsed.get('career_path'):
            raise ValueError("Model returned invalid career analysis JSON")
        return parsed
