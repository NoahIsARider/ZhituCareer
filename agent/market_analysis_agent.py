from openai import OpenAI
from playwright.sync_api import sync_playwright

class MarketDataScraper:
    def scrape_market_analysis(self):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Search for job market status
            page.goto('https://www.baidu.com')
            search_box = page.locator('#kw')
            search_box.fill('就业市场现状')
            search_box.press('Enter')
            page.wait_for_timeout(2000)
            
            # Extract search results
            results = page.locator('.c-container').all()
            market_info = ''
            for result in results[:5]:
                if result.locator('.content-right_8Zs40').count() > 0:
                    content = result.locator('.content-right_8Zs40').text_content()
                    market_info += content.strip() + '\n'
                elif result.locator('.content-right').count() > 0:
                    content = result.locator('.content-right').text_content()
                    market_info += content.strip() + '\n'
                else:
                    content = result.text_content()
                    market_info += content.strip() + '\n'
            print("Received response from playwright:")
            print('Scraped Market Information:', market_info)
            
            market_data = {
                'industry_trends': market_info 
            }
            
            browser.close()
            return market_data

class MarketAnalysisAgent:
    def __init__(self, client):
        self.client = client
        self.market_scraper = MarketDataScraper()

    def analyze_market(self):
        # 获取实时市场数据
        market_data = self.market_scraper.scrape_market_analysis()
        prompt = f"请基于以下实时市场数据，对当前就业市场进行分析：\n\n{market_data}"
        try:
            response = self.client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3-0324",
                messages=[
                    {'role': 'system', 'content': '你是一个专业的市场分析师。'},
                    {'role': 'user', 'content': prompt}
                ],
                stream=True
            )
            print('Received response from market analysis API')
        except Exception as api_error:
            print(f'API call error: {str(api_error)}')
            raise ValueError(f"API call failed: {str(api_error)}")

        try:
            full_response = ''
            for chunk in response:
                if chunk is None:
                    continue
                if hasattr(chunk, 'choices') and chunk.choices and len(chunk.choices) > 0:
                    if hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta and hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        if content is not None:
                            full_response += content
                            print(content, end='', flush=True)

            if not full_response:
                raise ValueError("Empty response from API")

            # 处理可能的Markdown代码块
            if '```json' in full_response:
                start = full_response.find('```json') + 7
                end = full_response.find('```', start)
                if end != -1:
                    full_response = full_response[start:end].strip()
            elif '```' in full_response:
                start = full_response.find('```') + 3
                end = full_response.find('```', start)
                if end != -1:
                    full_response = full_response[start:end].strip()

            print("Market Analysis Result:", full_response)
            return full_response
        except Exception as e:
            print(f'Error processing API response: {str(e)}')
            raise ValueError(f"Failed to process API response: {str(e)}")
