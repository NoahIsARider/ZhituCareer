# 智途Career+ 测试报告

本报告记录本次大规模数据升级后完整的测试执行结果，作为代码上传 GitHub 时"测试无错误"的凭据。

## 测试环境

- Python 3.11.2（Linux x64）
- Flask 3.1.3、openai 2.53.0、pytest 9.1.1
- LLM 相关测试通过 `os.environ` + monkeypatch 隔离：不依赖网络、不消耗真实 API 配额

## 测试总量

| 指标 | 数值 |
|------|------|
| 测试用例总数 | **120** |
| 通过 | **120** |
| 失败 | **0** |
| 错误 | **0** |
| 跳过 | **0** |

## 执行记录（连续 3 轮，验证稳定性）

| 轮次 | 命令 | 结果 | 耗时 |
|------|------|------|------|
| 1 | `python3 -m pytest --tb=short -rA` | **120 passed** | 25.10s |
| 2 | `python3 -m pytest` | **120 passed** | 25.32s |
| 3 | `python3 -m pytest` | **120 passed** | 25.91s |

三轮结果完全一致，无偶发失败。

## 测试文件分布

| 测试文件 | 用例数 | 覆盖范围 |
|----------|--------|----------|
| tests/test_app.py | 46 | Flask 端到端：认证/注册/限流/管理分页搜索/单条增删改/职业分析/职位与课程匹配/错误处理/JSON 安全 |
| tests/test_data_store.py | 19 | JsonStore：原子写入、并发保存不损坏、模式校验、字段裁剪、规范化 |
| tests/test_llm_client.py | 18 | LLM JSON 解析健壮性：代码围栏剥离、嵌套括号、字符串内花括号、尾逗号、重试 |
| tests/test_retrieval.py | 13 | 混合检索：中文 bigram 分词、中英文别名扩展、过滤/加权/top_k |
| tests/test_fallback.py | 12 | 规则兜底：职业领域识别、职位/课程匹配、确定性、空输入 |
| tests/test_cache.py | 7 | TTL 缓存：条目级过期、maxsize 淘汰、假值保留 |
| tests/test_large_data.py | 5 | **大规模数据**：5000 职位/课程的索引、检索、兜底匹配、LLM 候选集有界性 |

## 大规模数据基准（tests/test_large_data.py）

针对 5000 条职位 / 5000 条课程的规模验证，全部通过并满足性能预算：

| 场景 | 实测 | 预算 | 结论 |
|------|------|------|------|
| 5000 职位倒排索引构建 | 0.78s | <10s | 通过 |
| 索引后检索查询（含位置过滤） | <0.05s | <2s | 通过 |
| 5000 职位兜底匹配全流程（含首次建索引） | 1.31s | <5s | 通过 |
| 5000 课程兜底匹配全流程 | 0.32s | <5s | 通过 |
| LLM 精排候选集大小 | ≤ RETRIEVE_TOP_K(20) | 有界 | 通过 |

关键设计验证：即使全库 5000 条，送入 LLM 的候选集始终被限制在 20 条以内（`test_llm_only_sees_bounded_candidates` 用 monkeypatch 捕获实际传入条数并断言），保证数据量增长不会放大 LLM 调用开销。

## 真实服务器端到端验证（curl）

关闭 LLM 密钥（强制走规则兜底）后，对 `app.py` 实际启动的服务器执行：

| 请求 | 结果 |
|------|------|
| `GET /health` | 200 |
| `GET /login` | 200 |
| 管理员登录 `POST /login` | 成功，跳转 `/admin` |
| `GET /api/courses?page=1&page_size=3` | 分页数据正常返回 |
| `POST /search_jobs` | 返回职位（首条「智慧物流算法专家」） |
| `POST /register`（新用户） | 成功，自动登录跳转 |
| `POST /analyze_profile` | 返回 `source: local` 兜底职业分析 |
| `POST /search_course` | 返回匹配课程 |

## 说明

- 测试期间 LLM 成功路径使用确定性 canned 响应，失败路径强制抛错，两条分支（`llm_success` / `llm_failure` fixture）均被覆盖。
- 所有测试数据写入 `tmp_path` 隔离目录，仓库 `data/course.json`、`data/jobs.json`、`data/users.json` 在测试与端到端验证后均已通过 `git checkout` 恢复，无污染。
- 真实服务器验证后已停止（`background_terminal_kill`）。
