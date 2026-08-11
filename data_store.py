"""Robust JSON data persistence.

Replaces plain ``open()`` / ``json.dump()`` writes which can corrupt files
when a process is killed mid-write or two requests write concurrently.

Provides:

  * atomic writes (write to a temp file, ``os.replace`` into place);
  * cross-process file locking (``fcntl``) plus a process-local lock;
  * schema validation for course / job records with size limits;
  * tolerant reads that never crash on a missing or malformed file.
"""

import fcntl
import json
import os
import tempfile
import threading

MAX_ITEMS = 10000
MAX_FIELD_LEN = 2000

_SCHEMAS = {
    'course': {
        'required': ['title', 'description'],
        'string_fields': ['title', 'provider', 'level', 'duration', 'price',
                          'description'],
        'list_fields': ['skills', 'career_paths'],
        'list_item_type': str,
    },
    'job': {
        'required': ['title'],
        'string_fields': ['title', 'company', 'location', 'salary',
                          'description'],
        'list_fields': ['requirements'],
        'list_item_type': str,
    },
}

_LOCK_STORE = {}


def _global_lock(path):
    if path not in _LOCK_STORE:
        _LOCK_STORE[path] = threading.Lock()
    return _LOCK_STORE[path]


class JsonStore:
    """Thread-safe, crash-safe JSON file store with optional validation."""

    def __init__(self, path):
        self.path = path
        self._lock = _global_lock(path)

    def load(self, default=None):
        """Read and parse the JSON file. Never raises on corrupt input."""
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            return default
        except (json.JSONDecodeError, OSError) as e:
            print(f'[error] loading {self.path}: {e}')
            return default

    def save(self, data):
        """Atomically write ``data`` to disk under a cross-process lock."""
        path = self.path
        directory = os.path.dirname(path) or '.'
        os.makedirs(directory, exist_ok=True)

        with self._lock:
            lock_path = path + '.lock'
            with open(lock_path, 'a', encoding='utf-8') as lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    fd, tmp_path = tempfile.mkstemp(
                        dir=directory, prefix=os.path.basename(path) + '.', suffix='.tmp')
                    try:
                        with os.fdopen(fd, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                            f.flush()
                            os.fsync(f.fileno())
                        os.replace(tmp_path, path)
                    except Exception:
                        try:
                            os.unlink(tmp_path)
                        except OSError:
                            pass
                        raise
                finally:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def validate_records(records, schema_name):
        """Validate a list of records against a named schema.

        Returns ``(ok, error_message)``. ``ok`` is True when the list is a
        valid, non-empty... empty list is allowed; only malformed items and
        size overflows are rejected.
        """
        if not isinstance(records, list):
            return False, '数据必须是数组'
        if len(records) > MAX_ITEMS:
            return False, f'数据量超过上限（{MAX_ITEMS} 条）'
        schema = _SCHEMAS.get(schema_name)
        if schema is None:
            return True, None

        for idx, item in enumerate(records):
            if not isinstance(item, dict):
                return False, f'第 {idx + 1} 条记录必须是对象'
            for field in schema['required']:
                value = item.get(field)
                if value is None or (isinstance(value, str) and not value.strip()):
                    return False, f'第 {idx + 1} 条记录缺少必填字段「{field}」'
            for field in schema['string_fields']:
                if field in item and item[field] is not None:
                    if not isinstance(item[field], str):
                        return False, f'第 {idx + 1} 条记录字段「{field}」必须是字符串'
                    if len(item[field]) > MAX_FIELD_LEN:
                        return False, f'第 {idx + 1} 条记录字段「{field}」过长'
            for field in schema['list_fields']:
                if field in item and item[field] is not None:
                    value = item[field]
                    if not isinstance(value, list):
                        return False, f'第 {idx + 1} 条记录字段「{field}」必须是数组'
                    for item_val in value:
                        if not isinstance(item_val, schema['list_item_type']):
                            return False, f'第 {idx + 1} 条记录字段「{field}」元素类型错误'
        return True, None

    @staticmethod
    def normalize_records(records, schema_name):
        """Drop unknown fields and coerce common types; safe for any input."""
        schema = _SCHEMAS.get(schema_name)
        if schema is None:
            return records
        allowed = set(schema['string_fields']) | set(schema['list_fields'])
        allowed.add('id')
        normalized = []
        for item in records:
            if not isinstance(item, dict):
                continue
            clean = {}
            for key, value in item.items():
                if key not in allowed:
                    continue
                if key in schema['string_fields'] and value is not None:
                    clean[key] = str(value)[:MAX_FIELD_LEN]
                elif key in schema['list_fields'] and value is not None:
                    clean[key] = [str(v)[:MAX_FIELD_LEN] for v in value
                                  if isinstance(v, (str, int, float))]
                elif key == 'id':
                    clean[key] = value
            if clean.get('title') is None and schema_name == 'course':
                # keep the record only when it carries a title/description
                if 'title' not in clean and 'description' not in clean:
                    continue
            normalized.append(clean)
        return normalized
