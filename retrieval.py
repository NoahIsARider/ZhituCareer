"""Hybrid retrieval engine with an inverted index.

Implements the "retrieve then re-rank" pattern: when the course / job
catalog grows large, sending the whole catalog to the LLM would blow up
prompt size, cost and latency. This module pre-filters the catalog down
to a small candidate set using a hybrid score that combines:

  * TF-IDF cosine similarity over configured text fields (title, skills,
    description, ...), with boosted weight on key fields;
  * exact keyword / filter matching (e.g. expected city).

The top-K candidates are then handed to the LLM for final ranking, so the
system stays fast and cheap no matter how many records are stored.
"""

import math
import re
import threading
from collections import Counter, defaultdict

_CJK = re.compile(r'[\u4e00-\u9fff]+')
_WORD = re.compile(r'[a-z0-9]+')

# Bilingual alias pairs: when a phrase appears in the text, the tokens of its
# counterpart are added as well. Applying this symmetrically at index time and
# query time lets Chinese queries match English catalog entries and vice versa.
_ALIAS_PAIRS = [
    ('machine learning', '机器学习'),
    ('deep learning', '深度学习'),
    ('artificial intelligence', '人工智能'),
    ('data analysis', '数据分析'),
    ('data science', '数据科学'),
    ('data engineer', '数据工程'),
    ('frontend', '前端'),
    ('front-end', '前端'),
    ('backend', '后端'),
    ('back-end', '后端'),
    ('web development', 'web开发'),
    ('software engineer', '软件工程'),
    ('cloud computing', '云计算'),
    ('cyber security', '网络安全'),
    ('network security', '网络安全'),
    ('product manager', '产品经理'),
    ('ui design', 'ui设计'),
    ('ux design', 'ux设计'),
    ('database', '数据库'),
    ('blockchain', '区块链'),
    ('embedded', '嵌入式'),
    ('project management', '项目管理'),
    ('digital marketing', '数字营销'),
    ('algorithm', '算法'),
    ('ai', '人工智能'),
    ('security', '安全'),
    ('product', '产品'),
    ('design', '设计'),
    ('developer', '开发'),
    ('engineer', '工程师'),
]


def tokenize(text):
    """Tokenize mixed Chinese / English text with bilingual alias expansion.

    English words are split on non-alphanumeric characters and lowercased;
    Chinese runs are tokenized into character bigrams (standard approach for
    space-less scripts), falling back to single characters for short runs.
    When a known alias pair appears in the text, the counterpart's tokens are
    added so that the two languages share index / query terms.
    """
    text = (text or '').lower()
    augmented = text
    for src, alias in _ALIAS_PAIRS:
        if src in text:
            augmented += ' ' + alias
        if alias in text:
            augmented += ' ' + src

    tokens = []
    for m in _WORD.finditer(augmented):
        tokens.append(m.group(0))
    for m in _CJK.finditer(augmented):
        chunk = m.group(0)
        if len(chunk) <= 1:
            tokens.append(chunk)
        else:
            for i in range(len(chunk) - 1):
                tokens.append(chunk[i:i + 2])
    return tokens


class HybridRetriever:
    """Inverted-index hybrid retriever for dict-like documents."""

    def __init__(self, text_fields=(), filter_fields=(), boost_fields=()):
        self.text_fields = list(text_fields)
        self.filter_fields = list(filter_fields)
        self.boost_fields = set(boost_fields)
        self.docs = []
        self._postings = defaultdict(list)
        self._df = Counter()
        self._idf = {}
        self._norms = []
        self._built = False
        self._lock = threading.Lock()

    def _field_text(self, doc, field):
        raw = doc.get(field, '') or ''
        if isinstance(raw, (list, tuple)):
            raw = ' '.join(str(x) for x in raw)
        return str(raw)

    def index(self, docs):
        """Build the inverted index over a list of dict documents."""
        with self._lock:
            self.docs = list(docs)
            self._postings = defaultdict(list)
            self._df = Counter()
            self._idf = {}
            self._norms = []
            n = len(self.docs)

            for i, doc in enumerate(self.docs):
                tf = Counter()
                for field in self.text_fields:
                    weight = 2.0 if field in self.boost_fields else 1.0
                    for tok in tokenize(self._field_text(doc, field)):
                        tf[tok] += weight
                for tok, count in tf.items():
                    self._postings[tok].append((i, count))
                    self._df[tok] += 1

                norm = math.sqrt(sum((count * self._idf_placeholder()) ** 2
                                     for count in tf.values()))
                self._norms.append(norm)

            self._idf = {
                t: math.log((n + 1.0) / (df + 1.0)) + 1.0
                for t, df in self._df.items()
            }
            # norms must be computed with the final idf values
            self._norms = []
            for tf_vec in self._all_tf():
                norm = math.sqrt(
                    sum((count * self._idf[t]) ** 2 for t, count in tf_vec.items()))
                self._norms.append(norm)
            self._built = True

    def _idf_placeholder(self):
        return 1.0

    def _all_tf(self):
        vectors = [Counter() for _ in self.docs]
        for tok, postings in self._postings.items():
            for doc_idx, count in postings:
                vectors[doc_idx][tok] = count
        return vectors

    def matches_filters(self, doc, filters):
        for field, value in filters or []:
            if field not in self.filter_fields:
                continue
            if not value:
                continue
            if value.lower() not in self._field_text(doc, field).lower():
                return False
        return True

    def search(self, query, top_k=20, filters=None, min_score=0.0):
        """Return a list of (doc_index, score) for the best matches."""
        with self._lock:
            if not self._built or not self.docs:
                return []
            q = Counter(tokenize(query))
            if not q:
                return []
            q_norm = math.sqrt(
                sum((v * self._idf.get(t, 1.0)) ** 2 for t, v in q.items()))
            if q_norm == 0.0:
                return []

            scores = {}
            for term, q_count in q.items():
                idf = self._idf.get(term, 1.0)
                for doc_idx, doc_count in self._postings.get(term, ()):
                    if not self.matches_filters(self.docs[doc_idx], filters):
                        continue
                    dot_inc = q_count * idf * doc_count * idf
                    scores[doc_idx] = scores.get(doc_idx, 0.0) + dot_inc

            ranked = []
            for doc_idx, dot in scores.items():
                norm = self._norms[doc_idx]
                if norm == 0.0:
                    continue
                score = dot / (q_norm * norm)
                if score >= min_score:
                    ranked.append((score, doc_idx))
            ranked.sort(reverse=True)
            return [(idx, score) for score, idx in ranked[:top_k]]

    def candidate_docs(self, query, top_k=20, filters=None, min_score=0.0):
        """Convenience wrapper returning the matching documents themselves."""
        hits = self.search(query, top_k=top_k, filters=filters, min_score=min_score)
        return [self.docs[idx] for idx, _ in hits]
