"""数据库助手MCP服务器包

基于MCP (Model Context Protocol) 协议的数据库操作服务器，
为AI客户端提供数据库连接、查询、Schema探索、数据分析和SQL生成工具。

支持SQLite（内置）和可扩展其他数据库。
"""

from mcp.server.fastmcp import FastMCP

# 创建FastMCP服务器实例
mcp = FastMCP("db-assistant")


def format_markdown_table(headers: list, rows: list) -> str:
    """将数据格式化为Markdown表格。

    Args:
        headers: 表头列表
        rows: 数据行列表，每行是一个列表

    Returns:
        Markdown格式的表格字符串
    """
    lines = []
    lines.append("| " + " | ".join(str(h) for h in headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


# 导入工具模块以注册所有MCP工具
# 注意：导入顺序很重要，connection必须先导入，因为其他模块依赖它
from . import connection  # noqa: E402, F401
from . import query_tools  # noqa: E402, F401
from . import schema_tools  # noqa: E402, F401
from . import analysis  # noqa: E402, F401
from . import sql_builder  # noqa: E402, F401

__all__ = ["mcp", "format_markdown_table"]
__version__ = "1.0.0"
