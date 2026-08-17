---
name: heal_selector
description: 元素定位失败时从真实 DOM 推荐新 selector
enabled: true
tools:
  - browser_get_page_info
  - suggest_selector
  - memory_search
triggers:
  - selector_not_found
  - 定位
  - 修复selector
---

## 流程

1. **必须**先调用 `browser_get_page_info` 获取真实元素列表
2. 调用 `suggest_selector`，intent 描述目标元素
3. **禁止**编造不在 DOM 列表中的 selector
4. `memory_search` 查历史成功 selector
5. 返回 2~3 个候选及推荐 by 类型
6. 更新用例后重新 validate

## 优先级

id > name > css；xpath 仅在前两者不可用时使用
