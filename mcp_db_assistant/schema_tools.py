"""Schema探索工具

提供表结构、索引、外键、建表语句等Schema信息的MCP工具。
使用SQLite的PRAGMA命令获取元数据。
"""

from mcp_db_assistant import mcp
from mcp_db_assistant import format_markdown_table
from mcp_db_assistant.connection import db_manager
from mcp_db_assistant.query_tools import _validate_identifier


@mcp.tool()
def list_tables() -> str:
    """列出数据库中的所有表。

    返回所有用户表的名称、类型和创建语句摘要。

    Returns:
        表列表（Markdown格式）
    """
    try:
        conn = db_manager.get_conn()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name, type FROM sqlite_master "
            "WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%' "
            "ORDER BY type, name"
        )
        rows = cursor.fetchall()

        if not rows:
            return "数据库中没有找到任何表或视图。"

        headers = ["序号", "名称", "类型"]
        data = []
        for i, row in enumerate(rows, 1):
            data.append([i, row[0], row[1]])

        return "## 数据库表列表\n\n" + format_markdown_table(headers, data)
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ 列出表失败: {str(e)}"


@mcp.tool()
def describe_table(table_name: str) -> str:
    """获取表结构详情（列名、类型、约束等）。

    返回指定表的所有列信息，包括列名、数据类型、是否可空、
    默认值、是否主键等。

    Args:
        table_name: 表名，如 'employees'

    Returns:
        表结构详情（Markdown格式）
    """
    try:
        _validate_identifier(table_name)
        conn = db_manager.get_conn()
        cursor = conn.cursor()

        # 获取列信息
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()

        if not columns_info:
            return f"❌ 表 '{table_name}' 不存在或没有列信息。"

        headers = ["序号", "列名", "类型", "非空", "默认值", "主键"]
        data = []
        for col in columns_info:
            cid, name, col_type, notnull, default, pk = col
            data.append([
                cid,
                name,
                col_type or "未指定",
                "是" if notnull else "否",
                str(default) if default is not None else "无",
                "✅" if pk else "",
            ])

        result = f"## 表结构: {table_name}\n\n"
        result += format_markdown_table(headers, data)

        # 获取表行数
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        result += f"\n\n**总行数:** {row_count}"

        return result
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except ValueError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ 获取表结构失败: {str(e)}"


@mcp.tool()
def list_indexes(table_name: str) -> str:
    """列出指定表的所有索引。

    返回索引名称、是否唯一、创建语句等信息。
    如果表没有索引，会提示建议创建索引。

    Args:
        table_name: 表名，如 'employees'

    Returns:
        索引列表（Markdown格式）
    """
    try:
        _validate_identifier(table_name)
        conn = db_manager.get_conn()
        cursor = conn.cursor()

        # 获取索引列表
        cursor.execute(f"PRAGMA index_list({table_name})")
        indexes = cursor.fetchall()

        if not indexes:
            return f"表 '{table_name}' 没有自定义索引。\n\n💡 建议在常用查询条件列上创建索引以提高查询性能。"

        headers = ["序号", "索引名", "唯一", "创建语句"]
        data = []
        for i, idx in enumerate(indexes, 1):
            idx_name = idx[1]
            is_unique = "✅ 是" if idx[2] else "否"

            # 获取索引的创建SQL
            cursor.execute(f"PRAGMA index_info({idx_name})")
            idx_info = cursor.fetchall()
            columns = [row[2] for row in idx_info]
            create_sql = f"CREATE {'UNIQUE ' if idx[2] else ''}INDEX {idx_name} ON {table_name}({', '.join(columns)})"

            data.append([i, idx_name, is_unique, create_sql])

        result = f"## 表 '{table_name}' 的索引列表\n\n"
        result += format_markdown_table(headers, data)
        return result
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except ValueError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ 列出索引失败: {str(e)}"


@mcp.tool()
def get_table_ddl(table_name: str) -> str:
    """获取指定表的建表语句（DDL）。

    返回完整的CREATE TABLE语句，包括列定义、约束、外键等。

    Args:
        table_name: 表名，如 'employees'

    Returns:
        建表DDL语句
    """
    try:
        _validate_identifier(table_name)
        conn = db_manager.get_conn()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        row = cursor.fetchone()

        if not row or not row[0]:
            return f"❌ 表 '{table_name}' 不存在或没有DDL记录。"

        ddl = row[0]

        result = f"## 建表语句: {table_name}\n\n"
        result += f"```sql\n{ddl}\n```\n"

        # 额外显示列信息摘要
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        col_names = [col[1] for col in columns]
        result += f"\n**列:** {', '.join(col_names)}\n"
        result += f"**列数:** {len(columns)}"

        return result
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except ValueError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ 获取DDL失败: {str(e)}"


@mcp.tool()
def get_foreign_keys(table_name: str) -> str:
    """获取指定表的外键关系。

    返回表的所有外键约束，包括引用的表和列。
    外键关系是理解表间关系的重要信息。

    Args:
        table_name: 表名，如 'employees'

    Returns:
        外键关系列表（Markdown格式）
    """
    try:
        _validate_identifier(table_name)
        conn = db_manager.get_conn()
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fks = cursor.fetchall()

        if not fks:
            return f"表 '{table_name}' 没有外键约束。"

        headers = ["序号", "引用表", "本表列", "引用列", "删除行为", "更新行为"]
        data = []
        for i, fk in enumerate(fks, 1):
            # fk: (id, seq, table, from, to, on_update, on_delete, match)
            ref_table = fk[2]
            from_col = fk[3]
            to_col = fk[4]
            on_update = fk[5] or "NO ACTION"
            on_delete = fk[6] or "NO ACTION"

            data.append([i, ref_table, from_col, to_col, on_delete, on_update])

        result = f"## 表 '{table_name}' 的外键关系\n\n"
        result += format_markdown_table(headers, data)
        result += (
            "\n\n**说明:**\n"
            "- 本表列: 当前表中的外键列\n"
            "- 引用列: 被引用表中的对应列\n"
            "- 删除行为: 当被引用行被删除时的操作"
        )
        return result
    except RuntimeError as e:
        return f"❌ {str(e)}"
    except ValueError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        return f"❌ 获取外键失败: {str(e)}"
