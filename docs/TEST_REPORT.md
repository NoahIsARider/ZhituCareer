# 智途Career+ 测试报告（AI 模拟面试 + 长期职业生涯规划升级版）

本报告记录新增「AI 模拟面试」与「长期职业生涯规划」两大功能后的完整测试执行结果，
作为代码上传 GitHub 时"系统完全可用"的凭据。测试覆盖 LLM 路径与离线 fallback 路径，
全部在隔离的临时数据目录中运行，不依赖网络、不消耗真实 API 配额。

## 测试环境

- Python 3.12.3（Linux x64）
- Flask 3.0.3、openai 3.0.0、pytest 9.1.1
- LLM 相关测试通过 `os.environ` + monkeypatch 隔离（`LLM_MAX_RETRIES=0`、mock `_chat_once`）
- 数据隔离：每个用例使用独立 `tmp_path` 数据目录，仓库样例数据零污染

## 测试总量

| 指标 | 数值 |
|------|------|
| 测试用例总数 | **164** |
| 通过 | **164** |
| 失败 | **0** |
| 错误 | **0** |
| 跳过 | **0** |
| 执行时间 | 35.8s |

## 新增测试明细（本轮新增 36 个用例）

| 测试文件 | 数量 | 覆盖内容 |
|---------|------|---------|
| `tests/test_mock_interview.py` | 22 | 鉴权、LLM 出题、fallback 出题、题目数量校验与钳制（3-8）、会话持久化、LLM 评分、fallback 评分、空回答/无效会话/无效题号、完整面试总结（平均分/评语/亮点）、完成后拒绝重复作答、历史列表/删除/上限/用户隔离、汇总助手函数 |
| `tests/test_career_plan.py` | 14 | 鉴权、LLM 生成 5 年三阶段路线图、fallback 生成、无个人信息拒绝、带职业分析生成、latest 查询、历史列表/删除/上限/用户隔离、fallback 引擎未知/已知方向 |

## 新增功能（API）

| 功能 | 端点 |
|------|------|
| AI 模拟面试 | `POST /mock_interview/start` · `POST /mock_interview/answer` · `GET /mock_interview/session` · `GET/DELETE /api/interviews[/<id>]` |
| 长期职业生涯规划 | `POST /career_plan/generate` · `GET /career_plan/latest` · `GET/DELETE /api/plans[/<id>]` |

## 完整执行记录（pytest -v，164 passed）

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0 -- /home/ubuntu/.openclaw/workspace/noah-space/ZhituCareer/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/ubuntu/.openclaw/workspace/noah-space/ZhituCareer
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.14.2
collecting ... collected 164 items

tests/test_app.py::TestHealthAndAuth::test_health PASSED                 [  0%]
tests/test_app.py::TestHealthAndAuth::test_root_redirects_to_login PASSED [  1%]
tests/test_app.py::TestHealthAndAuth::test_api_requires_auth PASSED      [  1%]
tests/test_app.py::TestHealthAndAuth::test_admin_api_requires_admin PASSED [  2%]
tests/test_app.py::TestHealthAndAuth::test_login_success_admin PASSED    [  3%]
tests/test_app.py::TestHealthAndAuth::test_login_success_user PASSED     [  3%]
tests/test_app.py::TestHealthAndAuth::test_login_wrong_password PASSED   [  4%]
tests/test_app.py::TestHealthAndAuth::test_login_unknown_user PASSED     [  4%]
tests/test_app.py::TestHealthAndAuth::test_login_rate_limit PASSED       [  5%]
tests/test_app.py::TestHealthAndAuth::test_logout PASSED                 [  6%]
tests/test_app.py::TestHealthAndAuth::test_admin_page_redirects_non_admin PASSED [  6%]
tests/test_app.py::TestRegister::test_register_success PASSED            [  7%]
tests/test_app.py::TestRegister::test_register_invalid_phone PASSED      [  7%]
tests/test_app.py::TestRegister::test_register_short_password PASSED     [  8%]
tests/test_app.py::TestRegister::test_register_missing_name PASSED       [  9%]
tests/test_app.py::TestRegister::test_register_duplicate_phone PASSED    [  9%]
tests/test_app.py::TestRegister::test_register_rate_limit PASSED         [ 10%]
tests/test_app.py::TestAdminCourses::test_list_paginated PASSED          [ 10%]
tests/test_app.py::TestAdminCourses::test_search PASSED                  [ 11%]
tests/test_app.py::TestAdminCourses::test_search_no_match PASSED         [ 12%]
tests/test_app.py::TestAdminCourses::test_invalid_page_defaults PASSED   [ 12%]
tests/test_app.py::TestAdminCourses::test_add_item PASSED                [ 13%]
tests/test_app.py::TestAdminCourses::test_update_item PASSED             [ 14%]
tests/test_app.py::TestAdminCourses::test_delete_item PASSED             [ 14%]
tests/test_app.py::TestAdminCourses::test_delete_missing_returns_404 PASSED [ 15%]
tests/test_app.py::TestAdminCourses::test_delete_missing_id PASSED       [ 15%]
tests/test_app.py::TestAdminCourses::test_post_invalid_payload PASSED    [ 16%]
tests/test_app.py::TestAdminCourses::test_post_invalid_record PASSED     [ 17%]
tests/test_app.py::TestAdminCourses::test_post_valid_normalizes PASSED   [ 17%]
tests/test_app.py::TestAdminCourses::test_whole_replace PASSED           [ 18%]
tests/test_app.py::TestAdminJobs::test_list PASSED                       [ 18%]
tests/test_app.py::TestAdminJobs::test_add_update_delete PASSED          [ 19%]
tests/test_app.py::TestAdminJobs::test_non_admin_forbidden PASSED        [ 20%]
tests/test_app.py::TestAnalysisAndMatching::test_analyze_with_llm PASSED [ 20%]
tests/test_app.py::TestAnalysisAndMatching::test_analyze_falls_back PASSED [ 21%]
tests/test_app.py::TestAnalysisAndMatching::test_analyze_missing_fields PASSED [ 21%]
tests/test_app.py::TestAnalysisAndMatching::test_search_jobs_with_llm PASSED [ 22%]
tests/test_app.py::TestAnalysisAndMatching::test_search_jobs_fallback PASSED [ 23%]
tests/test_app.py::TestAnalysisAndMatching::test_search_course_with_llm PASSED [ 23%]
tests/test_app.py::TestAnalysisAndMatching::test_search_course_fallback PASSED [ 24%]
tests/test_app.py::TestErrors::test_api_404 PASSED                       [ 25%]
tests/test_app.py::TestErrors::test_page_404_redirects PASSED            [ 25%]
tests/test_app.py::TestErrors::test_me_returns_profile PASSED            [ 26%]
tests/test_app.py::TestErrors::test_session_persists PASSED              [ 26%]
tests/test_app.py::TestJsonBodySafety::test_invalid_json_body PASSED     [ 27%]
tests/test_app.py::TestJsonBodySafety::test_form_body_on_json_endpoint PASSED [ 28%]
tests/test_app.py::TestStatsOverview::test_stats_require_auth PASSED     [ 28%]
tests/test_app.py::TestStatsOverview::test_stats_overview_shape PASSED   [ 29%]
tests/test_app.py::TestStatsOverview::test_stats_salary_bucketing PASSED [ 29%]
tests/test_app.py::TestAnalysisHistory::test_analyze_saves_history PASSED [ 30%]
tests/test_app.py::TestAnalysisHistory::test_history_reversed_order PASSED [ 31%]
tests/test_app.py::TestAnalysisHistory::test_history_delete PASSED       [ 31%]
tests/test_app.py::TestAnalysisHistory::test_history_capped PASSED       [ 32%]
tests/test_app.py::TestAnalysisHistory::test_history_requires_auth PASSED [ 32%]
tests/test_cache.py::test_set_get PASSED                                 [ 33%]
tests/test_cache.py::test_missing_key PASSED                             [ 34%]
tests/test_cache.py::test_expiry PASSED                                  [ 34%]
tests/test_cache.py::test_per_item_ttl PASSED                            [ 35%]
tests/test_cache.py::test_maxsize_eviction PASSED                        [ 35%]
tests/test_cache.py::test_clear PASSED                                   [ 36%]
tests/test_cache.py::test_falsy_value_kept PASSED                        [ 37%]
tests/test_career_plan.py::TestPlanAuth::test_generate_requires_auth PASSED [ 37%]
tests/test_career_plan.py::TestPlanAuth::test_latest_requires_auth PASSED [ 38%]
tests/test_career_plan.py::TestPlanAuth::test_history_requires_auth PASSED [ 39%]
tests/test_career_plan.py::TestPlanGenerate::test_generate_llm PASSED    [ 39%]
tests/test_career_plan.py::TestPlanGenerate::test_generate_fallback PASSED [ 40%]
tests/test_career_plan.py::TestPlanGenerate::test_generate_without_profile_rejected PASSED [ 40%]
tests/test_career_plan.py::TestPlanGenerate::test_generate_with_analysis_text PASSED [ 41%]
tests/test_career_plan.py::TestPlanGenerate::test_generate_saves_and_latest PASSED [ 42%]
tests/test_career_plan.py::TestPlanGenerate::test_latest_empty PASSED    [ 42%]
tests/test_career_plan.py::TestPlanHistory::test_list_and_delete PASSED  [ 43%]
tests/test_career_plan.py::TestPlanHistory::test_history_capped PASSED   [ 43%]
tests/test_career_plan.py::TestPlanHistory::test_history_user_isolation PASSED [ 44%]
tests/test_career_plan.py::TestPlanFallbackEngine::test_unknown_profile_gets_generic_plan PASSED [ 45%]
tests/test_career_plan.py::TestPlanFallbackEngine::test_domain_profile_gets_matched_plan PASSED [ 45%]
tests/test_data_store.py::TestLoad::test_missing_returns_default PASSED  [ 46%]
tests/test_data_store.py::TestLoad::test_roundtrip PASSED                [ 46%]
tests/test_data_store.py::TestLoad::test_corrupt_returns_default PASSED  [ 47%]
tests/test_data_store.py::TestLoad::test_empty_file_returns_default PASSED [ 48%]
tests/test_data_store.py::TestAtomicity::test_no_partial_writes_on_failure PASSED [ 48%]
tests/test_data_store.py::TestAtomicity::test_concurrent_saves_never_corrupt PASSED [ 49%]
tests/test_data_store.py::TestValidation::test_valid_course PASSED       [ 50%]
tests/test_data_store.py::TestValidation::test_valid_job PASSED          [ 50%]
tests/test_data_store.py::TestValidation::test_missing_required PASSED   [ 51%]
tests/test_data_store.py::TestValidation::test_blank_required PASSED     [ 51%]
tests/test_data_store.py::TestValidation::test_wrong_type PASSED         [ 52%]
tests/test_data_store.py::TestValidation::test_non_dict_item PASSED      [ 53%]
tests/test_data_store.py::TestValidation::test_not_a_list PASSED         [ 53%]
tests/test_data_store.py::TestValidation::test_too_many_items PASSED     [ 54%]
tests/test_data_store.py::TestValidation::test_wrong_list_element_type PASSED [ 54%]
tests/test_data_store.py::TestNormalize::test_strips_unknown_fields PASSED [ 55%]
tests/test_data_store.py::TestNormalize::test_coerces_strings_and_int_list_items PASSED [ 56%]
tests/test_data_store.py::TestNormalize::test_drops_broken_records PASSED [ 56%]
tests/test_data_store.py::TestNormalize::test_truncates_long_fields PASSED [ 57%]
tests/test_fallback.py::TestCareerFallback::test_detects_ai_domain PASSED [ 57%]
tests/test_fallback.py::TestCareerFallback::test_unknown_profile_returns_default PASSED [ 58%]
tests/test_fallback.py::TestCareerFallback::test_result_shape PASSED     [ 59%]
tests/test_fallback.py::TestCareerFallback::test_all_missing_fields_no_crash PASSED [ 59%]
tests/test_fallback.py::TestJobFallback::test_keyword_and_location PASSED [ 60%]
tests/test_fallback.py::TestJobFallback::test_skill_overlap_ranks_higher PASSED [ 60%]
tests/test_fallback.py::TestJobFallback::test_empty_input_returns_empty PASSED [ 61%]
tests/test_fallback.py::TestJobFallback::test_deterministic PASSED       [ 62%]
tests/test_fallback.py::TestCourseFallback::test_chinese_keyword_matches_english_catalog PASSED [ 62%]
tests/test_fallback.py::TestCourseFallback::test_career_analysis_boost PASSED [ 63%]
tests/test_fallback.py::TestCourseFallback::test_empty_results PASSED    [ 64%]
tests/test_fallback.py::TestCourseFallback::test_deterministic PASSED    [ 64%]
tests/test_large_data.py::TestLargeJobMatching::test_fallback_fast_and_accurate PASSED [ 65%]
tests/test_large_data.py::TestLargeJobMatching::test_llm_only_sees_bounded_candidates PASSED [ 65%]
tests/test_large_data.py::TestLargeCourseMatching::test_fallback_fast_and_accurate PASSED [ 66%]
tests/test_large_data.py::TestLargeCourseMatching::test_llm_only_sees_bounded_candidates PASSED [ 67%]
tests/test_large_data.py::TestRetrievalIndexScale::test_index_time_for_5000_jobs PASSED [ 67%]
tests/test_llm_client.py::TestStripCodeFence::test_plain PASSED          [ 68%]
tests/test_llm_client.py::TestStripCodeFence::test_json_fence PASSED     [ 68%]
tests/test_llm_client.py::TestStripCodeFence::test_generic_fence PASSED  [ 69%]
tests/test_llm_client.py::TestStripCodeFence::test_fence_with_prose PASSED [ 70%]
tests/test_llm_client.py::TestExtractJson::test_prose_wrapped PASSED     [ 70%]
tests/test_llm_client.py::TestExtractJson::test_array_wrapped PASSED     [ 71%]
tests/test_llm_client.py::TestExtractJson::test_nested_braces PASSED     [ 71%]
tests/test_llm_client.py::TestExtractJson::test_string_containing_braces PASSED [ 72%]
tests/test_llm_client.py::TestExtractJson::test_no_json PASSED           [ 73%]
tests/test_llm_client.py::TestExtractJson::test_empty PASSED             [ 73%]
tests/test_llm_client.py::TestParseJson::test_valid PASSED               [ 74%]
tests/test_llm_client.py::TestParseJson::test_trailing_commas PASSED     [ 75%]
tests/test_llm_client.py::TestParseJson::test_invalid_returns_none PASSED [ 75%]
tests/test_llm_client.py::TestParseJson::test_with_prose PASSED          [ 76%]
tests/test_llm_client.py::TestChatRetry::test_success_first_try PASSED   [ 76%]
tests/test_llm_client.py::TestChatRetry::test_retry_then_success PASSED  [ 77%]
tests/test_llm_client.py::TestChatRetry::test_exhausts_retries PASSED    [ 78%]
tests/test_llm_client.py::TestChatRetry::test_empty_response_raises PASSED [ 78%]
tests/test_mock_interview.py::TestInterviewAuth::test_start_requires_auth PASSED [ 79%]
tests/test_mock_interview.py::TestInterviewAuth::test_answer_requires_auth PASSED [ 79%]
tests/test_mock_interview.py::TestInterviewAuth::test_session_requires_auth PASSED [ 80%]
tests/test_mock_interview.py::TestInterviewAuth::test_history_requires_auth PASSED [ 81%]
tests/test_mock_interview.py::TestInterviewStart::test_start_llm PASSED  [ 81%]
tests/test_mock_interview.py::TestInterviewStart::test_start_fallback PASSED [ 82%]
tests/test_mock_interview.py::TestInterviewStart::test_start_missing_target PASSED [ 82%]
tests/test_mock_interview.py::TestInterviewStart::test_start_custom_count PASSED [ 83%]
tests/test_mock_interview.py::TestInterviewStart::test_start_clamps_count_high PASSED [ 84%]
tests/test_mock_interview.py::TestInterviewStart::test_start_clamps_count_low PASSED [ 84%]
tests/test_mock_interview.py::TestInterviewStart::test_start_saves_session PASSED [ 85%]
tests/test_mock_interview.py::TestInterviewAnswer::test_answer_llm PASSED [ 85%]
tests/test_mock_interview.py::TestInterviewAnswer::test_answer_fallback PASSED [ 86%]
tests/test_mock_interview.py::TestInterviewAnswer::test_answer_empty_rejected PASSED [ 87%]
tests/test_mock_interview.py::TestInterviewAnswer::test_answer_unknown_session PASSED [ 87%]
tests/test_mock_interview.py::TestInterviewAnswer::test_answer_bad_index PASSED [ 88%]
tests/test_mock_interview.py::TestInterviewAnswer::test_complete_interview_summary PASSED [ 89%]
tests/test_mock_interview.py::TestInterviewAnswer::test_answer_after_completed_rejected PASSED [ 89%]
tests/test_mock_interview.py::TestInterviewAnswer::test_build_summary_helpers PASSED [ 90%]
tests/test_mock_interview.py::TestInterviewHistory::test_history_list_and_delete PASSED [ 90%]
tests/test_mock_interview.py::TestInterviewHistory::test_history_capped PASSED [ 91%]
tests/test_mock_interview.py::TestInterviewHistory::test_history_user_isolation PASSED [ 92%]
tests/test_retrieval.py::TestTokenize::test_english_words PASSED         [ 92%]
tests/test_retrieval.py::TestTokenize::test_chinese_bigrams PASSED       [ 93%]
tests/test_retrieval.py::TestTokenize::test_mixed PASSED                 [ 93%]
tests/test_retrieval.py::TestTokenize::test_alias_expansion PASSED       [ 94%]
tests/test_retrieval.py::TestTokenize::test_empty PASSED                 [ 95%]
tests/test_retrieval.py::TestRetrieverBasics::test_index_and_rank PASSED [ 95%]
tests/test_retrieval.py::TestRetrieverBasics::test_top_k PASSED          [ 96%]
tests/test_retrieval.py::TestRetrieverBasics::test_location_filter PASSED [ 96%]
tests/test_retrieval.py::TestRetrieverBasics::test_empty_index PASSED    [ 97%]
tests/test_retrieval.py::TestRetrieverBasics::test_empty_query PASSED    [ 98%]
tests/test_retrieval.py::TestRetrieverBasics::test_candidate_docs PASSED [ 98%]
tests/test_retrieval.py::TestRetrieverBasics::test_reindex_updates PASSED [ 99%]
tests/test_retrieval.py::TestRetrieverScale::test_large_catalog PASSED   [100%]

============================= 164 passed in 35.78s =============================
```
