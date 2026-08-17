---
name: generate_case
description: 自然语言生成符合 Easy-Web 标准字段的测试用例 JSON
enabled: true
tools:
  - validate_test_case
  - save_test_case_staging
  - get_config
  - memory_search
triggers:
  - generate
  - 生成用例
  - 写用例
---

## 流程

1. 理解用户测试意图（页面、操作、期望结果）
2. 调用 `get_config` 获取 `base_url`
3. 若有历史，调用 `memory_search` 检索相似用例
4. 生成标准 JSON 用例（type: search/login/nav/workflow 等）
5. 调用 `validate_test_case` 校验
6. 校验通过后询问用户，确认后 `save_test_case_staging`

## 字段规范

- 必填：id, name, type, url, expected_type, expected_value
- login 类型优先使用 username_selector / password_selector / login_btn_selector
- url 使用 `${base_url}/...` 占位符
