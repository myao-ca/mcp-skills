"""
MCP Server — 记忆存储服务

暴露 3 个 tool：
  - save_memory:   存一条记忆
  - search_memory: 关键词搜索记忆
  - list_memories: 列出所有记忆

存储用 SQLite，运行在本地，通过 stdio 和 MCP Client 通信。

启动方式：
  python memory_server.py

MCP Client（如 Claude Code）通过 stdio 连接，
不需要端口，不需要 HTTP，就是标准输入输出。
"""

import sqlite3
import asyncio
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# ============================================================
# 数据库初始化
# ============================================================

DB_PATH = Path(__file__).parent / "memories.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            key     TEXT NOT NULL,
            value   TEXT NOT NULL,
            created TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.commit()
    conn.close()


# ============================================================
# MCP Server 定义
# ============================================================

server = Server("memory-server")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """
    告诉 MCP Client 这个 server 有哪些 tool。
    每个 tool 的 description 就是 LLM 判断何时调用的依据。
    和你在 mini-claw/tools.py 里写的 schema 是同一个概念。
    """
    return [
        types.Tool(
            name="save_memory",
            description="保存一条记忆到长期存储。当用户提到需要记住某件事时使用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "key":   {"type": "string", "description": "记忆的标签或标题"},
                    "value": {"type": "string", "description": "记忆的具体内容"},
                },
                "required": ["key", "value"]
            }
        ),
        types.Tool(
            name="search_memory",
            description="搜索记忆库，返回包含关键词的记忆。当需要回忆之前存储的内容时使用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="list_memories",
            description="列出所有已存储的记忆。当需要查看记忆库全貌时使用。",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """
    MCP Client 调用 tool 时进入这里。
    name 是 tool 名，arguments 是参数字典。
    返回值是 TextContent 列表，内容会被传回给 LLM。
    """
    conn = sqlite3.connect(DB_PATH)

    try:
        if name == "save_memory":
            key = arguments["key"]
            value = arguments["value"]
            conn.execute(
                "INSERT INTO memories (key, value) VALUES (?, ?)",
                (key, value)
            )
            conn.commit()
            result = f"已保存记忆：[{key}] {value}"

        elif name == "search_memory":
            query = arguments["query"]
            rows = conn.execute(
                "SELECT key, value, created FROM memories WHERE key LIKE ? OR value LIKE ?",
                (f"%{query}%", f"%{query}%")
            ).fetchall()
            if rows:
                lines = [f"[{r[0]}] {r[1]}  ({r[2]})" for r in rows]
                result = f"找到 {len(rows)} 条记忆：\n" + "\n".join(lines)
            else:
                result = f"没有找到包含「{query}」的记忆"

        elif name == "list_memories":
            rows = conn.execute(
                "SELECT key, value, created FROM memories ORDER BY id DESC"
            ).fetchall()
            if rows:
                lines = [f"[{r[0]}] {r[1]}  ({r[2]})" for r in rows]
                result = f"共 {len(rows)} 条记忆：\n" + "\n".join(lines)
            else:
                result = "记忆库为空"

        else:
            result = f"未知 tool：{name}"

    finally:
        conn.close()

    return [types.TextContent(type="text", text=result)]


# ============================================================
# 启动
# ============================================================

async def main():
    init_db()
    # stdio_server 负责和 MCP Client 的通信
    # 读 stdin，写 stdout，遵循 MCP 协议格式
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
