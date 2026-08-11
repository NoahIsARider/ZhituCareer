"""Tests for the hybrid retrieval engine."""

import time

from retrieval import HybridRetriever, tokenize


def _docs(n):
    return [
        {'id': i, 'title': f'职位 {i}', 'company': '公司A',
         'description': '负责后端开发与系统维护',
         'requirements': ['Python', 'Java'], 'location': '杭州市'}
        for i in range(n)
    ]


class TestTokenize:
    def test_english_words(self):
        assert 'python' in tokenize('Python 3.11 and Flask')

    def test_chinese_bigrams(self):
        toks = tokenize('机器学习')
        assert '机器' in toks and '器学' in toks and '学习' in toks

    def test_mixed(self):
        toks = tokenize('AI 工程师 Python')
        assert 'ai' in toks and 'python' in toks
        assert '工程' in toks and '程师' in toks

    def test_alias_expansion(self):
        # Chinese query picks up English tokens and vice versa
        assert 'machine' in tokenize('机器学习')
        assert '机器' in tokenize('machine learning')

    def test_empty(self):
        assert tokenize('') == []
        assert tokenize(None) == []


class TestRetrieverBasics:
    def test_index_and_rank(self):
        docs = [
            {'title': '后端工程师', 'desc': 'Java Spring 微服务'},
            {'title': '数据分析师', 'desc': 'SQL 可视化 报表'},
            {'title': '算法工程师', 'desc': 'Python 机器学习 推荐'},
        ]
        r = HybridRetriever(text_fields=['title', 'desc'], boost_fields=['title'])
        r.index(docs)
        hits = r.search('机器学习 python', top_k=5)
        assert hits and hits[0][0] == 2  # 算法工程师 ranks first

    def test_top_k(self):
        r = HybridRetriever(text_fields=['title', 'description', 'requirements', 'location'])
        r.index(_docs(50))
        hits = r.search('后端 开发', top_k=10)
        assert 0 < len(hits) <= 10

    def test_location_filter(self):
        docs = [
            {'title': '前端', 'location': '杭州市'},
            {'title': '后端', 'location': '北京市'},
            {'title': '全栈', 'location': '杭州市'},
        ]
        r = HybridRetriever(text_fields=['title', 'location'], filter_fields=['location'])
        r.index(docs)
        hits = r.search('工程师 杭州', filters=[('location', '杭州')])
        assert len(hits) == 2  # only 杭州 entries

    def test_empty_index(self):
        r = HybridRetriever(text_fields=['title'])
        r.index([])
        assert r.search('anything') == []

    def test_empty_query(self):
        r = HybridRetriever(text_fields=['title'])
        r.index(_docs(5))
        assert r.search('') == []

    def test_candidate_docs(self):
        r = HybridRetriever(text_fields=['title'], boost_fields=['title'])
        r.index([{'title': 'AI 工程师'}, {'title': '产品经理'}])
        docs = r.candidate_docs('人工智能', top_k=1)
        assert len(docs) == 1
        assert 'AI' in docs[0]['title']

    def test_reindex_updates(self):
        r = HybridRetriever(text_fields=['title'], boost_fields=['title'])
        r.index([{'title': '苹果'}])
        assert r.search('香蕉') == []
        r.index([{'title': '香蕉'}])
        hits = r.search('香蕉')
        assert hits and hits[0][0] == 0


class TestRetrieverScale:
    def test_large_catalog(self):
        n = 5000
        docs = [
            {'id': i, 'title': f'岗位 {i}', 'description': '负责业务研发与架构设计',
             'requirements': ['Python', '分布式'], 'location': '上海'}
            for i in range(n)
        ]
        # insert a needle
        docs[1234]['title'] = '机器学习算法工程师'
        docs[1234]['description'] = 'Python 深度学习 推荐系统 大模型'

        start = time.time()
        r = HybridRetriever(text_fields=['title', 'description', 'requirements', 'location'],
                            boost_fields=['title'])
        r.index(docs)
        index_time = time.time() - start

        start = time.time()
        hits = r.search('机器学习 python 深度学习', top_k=5)
        query_time = time.time() - start

        assert hits
        assert hits[0][0] == 1234
        assert index_time < 10.0, f'index too slow: {index_time:.2f}s'
        assert query_time < 2.0, f'query too slow: {query_time:.2f}s'
