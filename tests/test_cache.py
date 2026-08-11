"""Tests for the TTL cache."""

import time

from cache import TTLCache


def test_set_get():
    c = TTLCache()
    c.set('k', 'v')
    assert c.get('k') == 'v'


def test_missing_key():
    assert TTLCache().get('nope') is None


def test_expiry():
    c = TTLCache(ttl_seconds=1)
    c.set('k', 'v')
    assert c.get('k') == 'v'
    time.sleep(1.1)
    assert c.get('k') is None


def test_per_item_ttl():
    c = TTLCache(ttl_seconds=100)
    c.set('short', 'v', ttl_seconds=1)
    c.set('long', 'v', ttl_seconds=100)
    time.sleep(1.1)
    assert c.get('short') is None
    assert c.get('long') == 'v'


def test_maxsize_eviction():
    c = TTLCache(maxsize=2)
    c.set('a', 1)
    c.set('b', 2)
    c.set('c', 3)
    assert len(c._data) <= 2
    assert c.get('a') is None


def test_clear():
    c = TTLCache()
    c.set('a', 1)
    c.clear()
    assert c.get('a') is None


def test_falsy_value_kept():
    c = TTLCache()
    c.set('zero', 0)
    c.set('none', None)
    assert c.get('zero') == 0
    # None is treated as a missing entry
    assert c.get('none') is None
