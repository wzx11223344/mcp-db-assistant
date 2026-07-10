"""数据库连接管理工具

提供数据库连接、断开、状态查询等MCP工具。
支持SQLite（内置）和PostgreSQL（可选，需安装psycopg2）。
"""

import os
import sqlite3
from typing import Optional

from mcp_db_assistant import mcp
from mcp_db_assistant import format_markdown_table


class ConnectionManager:
    """数据库连接管理器，维护全局连接状态。

    在整个服务器生命周期中持有一个活跃的数据库连接，
    所有工具模块通过 db_manager 访问当前连接。
    """

    def __init__(self):
        self.connection: Optional[sqlite3.Connection] = None
        self.db_path: Optional[str] = None
        self.db_type: Optional[str] = None  # 'sqlite' 或 'postgres'

    def get_conn(self) -> sqlite3.Connection:
        """获取当前数据库连接。

        Returns:
            当前活动的sqlite3.Connection对象

        Raises:
            RuntimeError: 如果没有活动的数据库连接
        """
        if self.connection is None:
            raise RuntimeError(
                "没有活动的数据库连接。请先使用 connect_sqlite 工具连接数据库。"
            )
        return self.connection

    def is_connected(self) -> bool:
        """检查是否已连接到数据库。"""
        return self.connection is not None

    def reset(self):
        """重置连接状态，关闭当前连接。"""
        if self.connection is not None:
            try:
                self.connection.close()
            except Exception:
                pass
        self.connection = None
        self.db_path = None
        self.db_type = None


# 全局连接管理器实例
db_manager = ConnectionManager()


@mcp.tool()
def connect_sqlite(db_path: str) -> str:
    """连接到SQLite数据库文件。

    如果当前已有连接，会先关闭旧连接再建立新连接。
    连接成功后，所有其他数据库工具都可以使用。

    Args:
        db_path: SQLite数据库文件路径，如 'sample.db' 或 '/path/to/db.sqlite'

    Returns:
        连接结果信息（Markdown格式）
    """
    try:
        # 关闭已有连接
        if db_manager.connection is not None:
            db_manager.connection.close()

        # 检查文件是否存在
        if not os.path.exists(db_path):
            return f"❌ 数据库文件不存在: {db_path}\n\n请确认路径是否正确。"

        # 创建新连接
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row

        db_manager.connection = conn
        db_manager.db_path = os.path.abspath(db_path)
        db_manager.db_type = "sqlite"

        # 获取数据库基本信息
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        file_size = os.path.getsize(db_path)

        headers = ["属性", "值"]
        rows = [
            ["状态", "✅ 已连接"],
            ["数据库类型", "SQLite"],
            ["文件路径", db_manager.db_path],
            ["文件大小", f"{file_size / 1024:.1f} KB"],
            ["表数量", str(table_count)],
        ]

        return "## SQLite连接成功\n\n" + format_markdown_table(headers, rows)
    except Exception as e:
        return f"❌ 连接SQLite数据库失败: {str(e)}"


@mcp.tool()
def connect_postgres(
    host: str, port: int, db: str, user: str, password: str
) -> str:
    """连接到PostgreSQL数据库（需要安装psycopg2驱动）。

    PostgreSQL连接为可选功能，需要额外安装 psycopg2-binary。
    如果未安装驱动，将返回安装指引。

    Args:
        host: PostgreSQL服务器地址（如 'localhost' 或 '192.168.1.100'）
        port: 端口号（通常为5432）
        db: 数据库名称
        user: 用户名
        password: 密码

    Returns:
        连接结果信息（Markdown格式）
    """
    try:
        import psycopg2
    except ImportError:
        return (
            "❌ PostgreSQL连接需要安装 psycopg2 驱动。\n\n"
            "请执行以下命令安装：\n"
            "```\n"
            "pip install psycopg2-binary\n"
            "```\n\n"
            "安装后重新调用此工具即可连接PostgreSQL数据库。"
        )

    try:
        # 关闭已有连接
        if db_manager.connection is not None:
            db_manager.connection.close()

        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=db,
            user=user,
            password=password,
        )

        db_manager.connection = conn
        db_manager.db_path = f"{host}:{port}/{db}"
        db_manager.db_type = "postgres"

        cursor = conn.cursor()
        cursor.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema = 'public'"
        )
        table_count = cursor.fetchone()[0]
        cursor.close()

        headers = ["属性", "值"]
        rows = [
            ["状态", "✅ 已连接"],
            ["数据库类型", "PostgreSQL"],
            ["主机", f"{host}:{port}"],
            ["数据库名", db],
            ["用户", user],
            ["表数量", str(table_count)],
        ]

        return "## PostgreSQL连接成功\n\n" + format_markdown_table(headers, rows)
    except Exception as e:
        return f"❌ 连接PostgreSQL数据库失败: {str(e)}"


@mcp.tool()
def list_databases() -> str:
    """列出当前连接中的所有数据库。

    对于SQLite，列出所有附加（ATTACH）的数据库；
    对于PostgreSQL，列出服务器上所有可访问的数据库。

    Returns:
        数据库列表（Markdown格式）
    """
    try:
        conn = db_manager.get_conn()

        if db_manager.db_type == "sqlite":
            cursor = conn.cursor()
            cursor.execute("PRAGMA database_list")
            rows_data = cursor.fetchall()

            if not rows_data:
                return "当前没有附加的数据库。"

            headers = ["序号", "数据库名", "文件路径"]
            rows = []
            for i, row in enumerate(rows_data, 1):
                rows.append([i, row[1], row[2] or "(内存数据库)"])

            return "## 附加数据库列表\n\n" + format_markdown_table(headers, rows)
        else:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT datname FROM pg_database "
                "WHERE datistemplate = false ORDER BY datname"
            )
            rows_data = cursor.fetchall()

            headers = ["序号", "数据库名"]
            rows = []
            for i, row in enumerate(rows_data, 1):
                rows.append([i, row[0]])

            return "## 数据库列表\n\n" + format_markdown_table(headers, rows)
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ 列出数据库失败: {str(e)}"


@mcp.tool()
def get_connection_status() -> str:
    """获取当前数据库连接状态。

    返回连接类型、路径、表数量等状态信息。

    Returns:
        连接状态信息（Markdown格式）
    """
    if not db_manager.is_connected():
        return (
            "## 数据库连接状态\n\n"
            "| 属性 | 值 |\n"
            "|------|----|\n"
            "| 状态 | ❌ 未连接 |\n"
            "| 提示 | 请使用 connect_sqlite 工具连接数据库 |\n"
        )

    status_items = [
        ("状态", "✅ 已连接"),
        ("数据库类型", db_manager.db_type or "未知"),
        ("数据库路径", db_manager.db_path or "未知"),
    ]

    if db_manager.db_type == "sqlite":
        try:
            conn = db_manager.get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            )
            table_count = cursor.fetchone()[0]
            status_items.append(("表数量", str(table_count)))

            if db_manager.db_path and os.path.exists(db_manager.db_path):
                file_size = os.path.getsize(db_manager.db_path)
                status_items.append(("文件大小", f"{file_size / 1024:.1f} KB"))

            # SQLite版本
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            status_items.append(("SQLite版本", version))
        except Exception:
            status_items.append(("详细信息", "获取失败"))

    headers = ["属性", "值"]
    return "## 数据库连接状态\n\n" + format_markdown_table(headers, status_items)
