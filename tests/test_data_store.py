"""Tests for atomic / validated JSON data persistence."""

import json
import os
import threading

import pytest

from data_store import JsonStore, MAX_ITEMS


@pytest.fixture
def store(tmp_path):
    return JsonStore(str(tmp_path / 'data.json'))


class TestLoad:
    def test_missing_returns_default(self, store):
        assert store.load(default={'x': 1}) == {'x': 1}

    def test_roundtrip(self, store):
        payload = {'users': [{'phone': '13800000000', 'role': 'admin'}]}
        store.save(payload)
        assert store.load() == payload

    def test_corrupt_returns_default(self, store):
        with open(store.path, 'w', encoding='utf-8') as f:
            f.write('{ not valid json')
        assert store.load(default=[]) == []

    def test_empty_file_returns_default(self, store):
        with open(store.path, 'w', encoding='utf-8') as f:
            f.write('')
        assert store.load(default={}) == {}


class TestAtomicity:
    def test_no_partial_writes_on_failure(self, store, monkeypatch):
        store.save({'version': 1})

        def boom(*args, **kwargs):
            raise OSError('disk full')

        monkeypatch.setattr(os, 'replace', boom)
        with pytest.raises(OSError):
            store.save({'version': 2})

        # original content preserved
        assert store.load() == {'version': 1}

    def test_concurrent_saves_never_corrupt(self, tmp_path):
        path = str(tmp_path / 'shared.json')
        store = JsonStore(path)
        store.save({'version': 0})

        def writer(idx):
            s = JsonStore(path)
            for i in range(30):
                # each save is a complete, independent document
                s.save({'version': idx, 'batch': i, 'values': list(range(i))})

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # The final document must be exactly one writer's complete payload
        # (atomic whole-file replace) and always valid JSON — never a torn mix.
        data = JsonStore(path).load()
        assert data['version'] in (0, 1, 2, 3)
        assert isinstance(data['values'], list)
        assert len(data['values']) == data['batch']
        assert json.loads(json.dumps(data)) == data


class TestValidation:
    def test_valid_course(self):
        ok, err = JsonStore.validate_records([
            {'title': '机器学习', 'description': '入门课程', 'skills': ['Python']}
        ], 'course')
        assert ok and err is None

    def test_valid_job(self):
        ok, _ = JsonStore.validate_records([
            {'title': '后端工程师', 'company': 'X', 'requirements': ['Go']}
        ], 'job')
        assert ok

    def test_missing_required(self):
        ok, err = JsonStore.validate_records(
            [{'description': 'no title'}], 'course')
        assert not ok and 'title' in err

    def test_blank_required(self):
        ok, err = JsonStore.validate_records(
            [{'title': '  ', 'description': 'x'}], 'course')
        assert not ok

    def test_wrong_type(self):
        ok, err = JsonStore.validate_records(
            [{'title': 'x', 'description': 123}], 'course')
        assert not ok and 'description' in err

    def test_non_dict_item(self):
        ok, err = JsonStore.validate_records(['oops'], 'course')
        assert not ok

    def test_not_a_list(self):
        ok, err = JsonStore.validate_records({'a': 1}, 'course')
        assert not ok

    def test_too_many_items(self):
        ok, err = JsonStore.validate_records([{'title': f'x{i}'} for i in range(MAX_ITEMS + 1)], 'course')
        assert not ok

    def test_wrong_list_element_type(self):
        ok, err = JsonStore.validate_records(
            [{'title': 'x', 'description': 'd', 'skills': ['ok', 3]}], 'course')
        assert not ok


class TestNormalize:
    def test_strips_unknown_fields(self):
        out = JsonStore.normalize_records([
            {'title': 'T', 'description': 'D', 'hack': 'drop', 'skills': ['a']}
        ], 'course')
        assert out == [{'title': 'T', 'description': 'D', 'skills': ['a']}]

    def test_coerces_strings_and_int_list_items(self):
        out = JsonStore.normalize_records([
            {'title': 123, 'description': 'd', 'requirements': [1, 'go']}
        ], 'job')
        assert out[0]['title'] == '123'
        assert out[0]['requirements'] == ['1', 'go']

    def test_drops_broken_records(self):
        out = JsonStore.normalize_records(['nope', None, {'title': 'ok', 'description': 'd'}], 'course')
        assert len(out) == 1

    def test_truncates_long_fields(self):
        out = JsonStore.normalize_records([
            {'title': 'x' * 5000, 'description': 'd'}
        ], 'course')
        assert len(out[0]['title']) <= 2000
