---
description: 从记忆库中搜索并回顾历史记忆，需要 my-memory-server 连接
---

你有访问记忆库的能力，通过 my-memory-server 提供的工具来操作。

根据用户的请求，选择合适的操作：

- 如果用户想**搜索**特定内容 → 调用 `search_memory`，用用户提供的关键词
- 如果用户想**查看全部**记忆 → 调用 `list_memories`
- 如果用户想**保存**一条记忆 → 调用 `save_memory`，提取合适的 key 和 value

操作完成后，用自然语言总结结果，不要直接输出原始数据。

如果 my-memory-server 未连接，告知用户需要先在 /mcp 中启用 my-memory-server。

$ARGUMENTS
