---
name: diagnose_failure
description: 测试失败时分析原因并给出修复建议
enabled: true
tools:
  - memory_search
  - get_config
triggers:
  - test_failed
  - 失败
  - 诊断
---

## 流程

1. 收集失败信息：断言错误、URL、用例 JSON、截图路径
2. `memory_search` 检索相似失败修复记录
3. 分析可能原因：selector 失效、超时、数据错误、页面变更
4. 给出具体修复建议（新 selector、调整 expected_value、增加 wait 步骤）
5. 建议写入 L2 episode 供后续检索

## 输出格式

- **原因**：...
- **建议**：...
- **可选修复**：...
