import os

from agent.llm_client import LLMClient
from cache import TTLCache

MODEL = 'LLM-Research/Meta-Llama-3.1-8B-Instruct'

FALLBACK_MARKET_DATA = """就业市场现状：
1. 互联网与人工智能领域人才需求持续旺盛，算法工程师、AI 应用工程师缺口较大。
2. 数字化转型推动各行业对软件工程师、数据工程师需求稳定增长。
3. 云原生、信息安全、大数据等方向成为高薪热门赛道。
4. 传统行业与互联网融合岗位（产业互联网）提供大量复合型人才机会。
5. 具备 AI 工具使用能力与跨领域技能的人才更具竞争力。"""

MARKET_CACHE_TTL = int(os.getenv('MARKET_CACHE_TTL', '1800'))
MARKET_SCRAPE_TIMEOUT = int(os.getenv('MARKET_SCRAPE_TIMEOUT', '15000'))

_market_cache = TTLCache(ttl_seconds=MARKET_CACHE_TTL, maxsize=4)


class MarketDataScraper:
    """获取实时就业市场数据；抓取失败时回退到内置市场概览，保证服务可用。"""

    def scrape_market_analysis(self, use_cache=True):
        cached = _market_cache.get('market_analysis') if use_cache else None
        if cached is not None:
            print('[cache] reusing cached market analysis')
            return cached

        market_info = self._scrape()
        if market_info.strip():
            result = {'industry_trends': market_info}
        else:
            print('[warn] market scraping returned empty, using fallback data')
            result = {'industry_trends': FALLBACK_MARKET_DATA}

        if use_cache:
            _market_cache.set('market_analysis', result)
        return result

    def _scrape(self):
        try:
            from playwright.sync_api import sync_playwright
        except Exception as e:
            print(f'[warn] playwright unavailable, using fallback data: {e}')
            return FALLBACK_MARKET_DATA

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto('https://www.baidu.com', timeout=MARKET_SCRAPE_TIMEOUT)
                search_box = page.locator('#kw')
                search_box.fill('就业市场现状')
                search_box.press('Enter')
                page.wait_for_timeout(2000)

                results = page.locator('.c-container').all()
                market_info = ''
                for result in results[:5]:
                    text = result.text_content()
                    if text:
                        market_info += text.strip() + '\n'
                browser.close()

                if market_info.strip():
                    print('Scraped Market Information:', market_info[:300])
                    return market_info
        except Exception as e:
            print(f'[warn] market scraping failed, using fallback data: {e}')

        return FALLBACK_MARKET_DATA


class MarketAnalysisAgent:
    def __init__(self, client):
        self.llm = LLMClient(client)
        self.market_scraper = MarketDataScraper()

    def analyze_market(self):
        market_data = self.market_scraper.scrape_market_analysis()
        data_text = market_data.get('industry_trends', '')
        prompt = f"请基于以下实时市场数据，对当前就业市场进行分析：\n\n{data_text}"
        return self.llm.chat(
            MODEL,
            '你是一个专业的市场分析师。',
            prompt
        )
